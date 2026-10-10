"""Punto de entrada: busca, filtra, envía el correo y guarda las ofertas vistas.

Uso:
    python -m job_hunter.main            # ejecución normal (envía correo)
    python -m job_hunter.main --dry-run  # no envía, guarda el correo en salida.html
"""
import argparse
import os
from datetime import datetime

import yaml

from . import correo, estado
from .filtro import Filtro
from .fuentes import infojobs, linkedin, tecnoempleo


def ejecutar(cfg: dict, dry_run: bool = False) -> int:
    filtro = Filtro(cfg)
    vistas = estado.cargar()
    errores, todas = [], []

    fuentes = [("LinkedIn", linkedin.buscar), ("Tecnoempleo", tecnoempleo.buscar)]
    if infojobs.activo():
        fuentes.append(("InfoJobs", infojobs.buscar))

    stats = {}
    for nombre, buscar in fuentes:
        try:
            encontradas = buscar(cfg)
            stats[nombre] = len(encontradas)
            todas += encontradas
        except Exception as e:  # una fuente caída no debe parar las demás
            errores.append(f"{nombre}: {type(e).__name__}: {e}")
            stats[nombre] = "error"

    # Nuevas y con título válido
    nuevas = [o for o in todas if o.clave not in vistas and filtro.titulo_valido(o)]

    # Las de LinkedIn llegan sin descripción: se descargan solo las candidatas
    try:
        linkedin.completar_descripciones([o for o in nuevas if o.fuente == "LinkedIn"],
                                         cfg["busquedas"]["max_descripciones_linkedin"])
    except Exception as e:
        errores.append(f"LinkedIn (descripciones): {e}")

    aceptadas, descartes, duplicados = [], {}, set()
    for o in nuevas:
        ok, motivo = filtro.evaluar(o)
        if ok and o.clave_duplicado not in duplicados:
            duplicados.add(o.clave_duplicado)
            aceptadas.append(o)
        elif not ok:
            descartes[motivo] = descartes.get(motivo, 0) + 1

    aceptadas.sort(key=lambda o: o.puntuacion, reverse=True)
    stats["nuevas"] = len(nuevas)
    stats["enviadas"] = len(aceptadas)
    stats.update({f"descartadas ({k})": v for k, v in descartes.items()})

    html = correo.construir_html(aceptadas, stats, errores)
    if dry_run:
        with open("salida.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Correo guardado en salida.html")
    elif aceptadas or errores:
        n = len(aceptadas)
        correo.enviar(f"Job Hunter: {n} {'oferta nueva' if n == 1 else 'ofertas nuevas'} ({datetime.now():%d/%m %H:%M})", html)

    ahora = datetime.now().isoformat()
    for o in nuevas:
        vistas[o.clave] = ahora
    if not dry_run:
        estado.guardar(vistas)

    print(stats)
    for e in errores:
        print("AVISO:", e)
    return len(aceptadas)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--config", default=os.environ.get("JOB_HUNTER_CONFIG", "config.yaml"))
    args = p.parse_args()
    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    ejecutar(cfg, args.dry_run)


if __name__ == "__main__":
    main()
