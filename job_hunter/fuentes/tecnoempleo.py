"""Tecnoempleo: portal de empleo IT español. Se lee la página pública de resultados."""
import re
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from ..modelo import Oferta

CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}


def parsear_listado(html: str) -> list[Oferta]:
    soup = BeautifulSoup(html, "html.parser")
    ofertas = []
    for a in soup.select("h3 a[href*='/rf-']"):
        url = a["href"].split("?")[0]
        if url.startswith("/"):
            url = "https://www.tecnoempleo.com" + url
        m = re.search(r"/rf-([0-9a-f]+)", url)
        bloque = a.find_parent("div")
        empresa = bloque.select_one("a.text-primary") if bloque else None
        info = bloque.select_one("span.d-block") if bloque else None
        resumen = bloque.select_one("span.hidden-md-down") if bloque else None
        ubic, fecha = "", ""
        if info:
            partes = [p.strip() for p in info.get_text(" ", strip=True).split(" - ")]
            ubic = partes[0] if partes else ""
            fecha = partes[-1] if len(partes) > 1 else ""
        ofertas.append(Oferta(
            fuente="Tecnoempleo",
            id=m.group(1) if m else url,
            titulo=a.get_text(" ", strip=True),
            empresa=empresa.get_text(" ", strip=True) if empresa else "",
            ubicacion=ubic,
            url=url,
            fecha=fecha,
            descripcion=resumen.get_text(" ", strip=True) if resumen else "",
        ))
    return ofertas


def buscar(cfg) -> list[Oferta]:
    t = cfg["tecnoempleo"]
    ex = "," + ",".join(t["experiencia"]) + ","
    vistas = {}
    for termino in t["terminos"]:
        for pr in t["provincias"]:
            url = f"https://www.tecnoempleo.com/ofertas-trabajo/?te={quote(termino)}&ex={ex}"
            if pr:
                url += f"&pr=,{pr},"
            r = requests.get(url, headers=CABECERAS, timeout=20)
            r.raise_for_status()
            for o in parsear_listado(r.text):
                vistas.setdefault(o.id, o)
            time.sleep(1)
    return list(vistas.values())
