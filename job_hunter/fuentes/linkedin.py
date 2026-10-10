"""LinkedIn: API pública de invitados (la misma que usa la web sin iniciar sesión).

No requiere credenciales. LinkedIn limita mucho las peticiones desde servidores,
así que se hacen pocas y con pausas; si responde 429/999 se abandona sin romper el resto.
"""
import time
from urllib.parse import quote

import requests
from bs4 import BeautifulSoup

from ..modelo import Oferta

BASE = "https://www.linkedin.com/jobs-guest/jobs/api"
CABECERAS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "es-ES,es;q=0.9",
}


class Bloqueado(Exception):
    pass


def _get(url):
    r = requests.get(url, headers=CABECERAS, timeout=20)
    if r.status_code in (429, 999, 403):
        raise Bloqueado(f"LinkedIn respondió {r.status_code}")
    r.raise_for_status()
    return r.text


def parsear_listado(html: str) -> list[Oferta]:
    soup = BeautifulSoup(html, "html.parser")
    ofertas = []
    for card in soup.select("[data-entity-urn*='jobPosting']"):
        job_id = card["data-entity-urn"].rsplit(":", 1)[-1]
        txt = lambda sel: (card.select_one(sel).get_text(" ", strip=True) if card.select_one(sel) else "")
        fecha = card.select_one("time")
        ofertas.append(Oferta(
            fuente="LinkedIn",
            id=job_id,
            titulo=txt(".base-search-card__title"),
            empresa=txt(".base-search-card__subtitle"),
            ubicacion=txt(".job-search-card__location"),
            url=f"https://www.linkedin.com/jobs/view/{job_id}/",
            fecha=fecha.get("datetime", "") if fecha else "",
        ))
    return ofertas


def parsear_descripcion(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    nodo = soup.select_one(".show-more-less-html__markup") or soup.select_one(".description__text")
    return nodo.get_text("\n", strip=True) if nodo else ""


def buscar(cfg) -> list[Oferta]:
    b = cfg["busquedas"]
    segundos = int(b.get("horas_antiguedad", 24)) * 3600
    vistas = {}
    for kw in b["palabras_clave"]:
        for loc in b["ubicaciones"]:
            url = (f"{BASE}/seeMoreJobPostings/search?keywords={quote(kw)}&location={quote(loc)}"
                   f"&f_TPR=r{segundos}&f_E=1,2")
            for o in parsear_listado(_get(url)):
                vistas.setdefault(o.id, o)
            time.sleep(1.5)
    return list(vistas.values())


def completar_descripciones(ofertas: list[Oferta], maximo: int) -> None:
    for o in ofertas[:maximo]:
        try:
            o.descripcion = parsear_descripcion(_get(f"{BASE}/jobPosting/{o.id}"))
        except Bloqueado:
            break
        except requests.RequestException:
            continue
        time.sleep(1.5)
