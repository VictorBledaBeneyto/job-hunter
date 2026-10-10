"""InfoJobs: API oficial (gratuita, requiere registrar una app en developer.infojobs.net).

Solo se activa si existen las variables INFOJOBS_CLIENT_ID e INFOJOBS_CLIENT_SECRET.
"""
import os

import requests

from ..modelo import Oferta

API = "https://api.infojobs.net/api/9/offer"


def activo() -> bool:
    return bool(os.getenv("INFOJOBS_CLIENT_ID") and os.getenv("INFOJOBS_CLIENT_SECRET"))


def parsear(datos: dict) -> list[Oferta]:
    ofertas = []
    for it in datos.get("items", []):
        ofertas.append(Oferta(
            fuente="InfoJobs",
            id=str(it.get("id", "")),
            titulo=it.get("title", ""),
            empresa=(it.get("author") or {}).get("name", ""),
            ubicacion=it.get("city", "") or (it.get("province") or {}).get("value", ""),
            url=it.get("link", ""),
            fecha=(it.get("published") or "")[:10],
            descripcion=" ".join(filter(None, [
                (it.get("experienceMin") or {}).get("value", ""),
                (it.get("contractType") or {}).get("value", ""),
                (it.get("teleworking") or {}).get("value", ""),
                it.get("requirementMin", ""),
            ])),
        ))
    return ofertas


def buscar(cfg) -> list[Oferta]:
    auth = (os.environ["INFOJOBS_CLIENT_ID"], os.environ["INFOJOBS_CLIENT_SECRET"])
    c = cfg["infojobs"]
    vistas = {}
    for termino in c["terminos"]:
        for prov in c["provincias"]:
            params = {"q": termino, "province": prov, "sinceDate": "_24_HOURS",
                      "maxResults": 50, "order": "updated-desc"}
            r = requests.get(API, params=params, auth=auth, timeout=20)
            r.raise_for_status()
            for o in parsear(r.json()):
                vistas.setdefault(o.id, o)
    return list(vistas.values())
