"""Recuerda las ofertas ya enviadas para no repetirlas (se guarda en la caché de GitHub Actions)."""
import json
import os
from datetime import datetime, timedelta

RUTA = os.environ.get("SEEN_FILE", "data/seen.json")
DIAS_RECUERDO = 45


def cargar() -> dict:
    try:
        with open(RUTA, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def guardar(vistas: dict) -> None:
    limite = (datetime.now() - timedelta(days=DIAS_RECUERDO)).isoformat()
    vistas = {k: v for k, v in vistas.items() if v >= limite}
    os.makedirs(os.path.dirname(RUTA) or ".", exist_ok=True)
    with open(RUTA, "w", encoding="utf-8") as f:
        json.dump(vistas, f, ensure_ascii=False, indent=0)
