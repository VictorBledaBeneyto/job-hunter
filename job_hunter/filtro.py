"""Filtrado y puntuación de ofertas según el perfil definido en config.yaml."""
import re

from .modelo import Oferta


def _regex(texto: str) -> re.Pattern:
    """Admite expresiones partidas en varias líneas en el YAML."""
    limpio = re.sub(r"\s*\|\s*", "|", texto.strip())
    return re.compile(limpio, re.IGNORECASE)


ANIOS = re.compile(
    r"(?:(?:m[ií]nimo|al menos|at least|\+)\s*)?(\d{1,2})\s*\+?\s*(?:años|year|yrs)"
    r"(?:\s+(?:de\s+)?(?:experiencia|experience))?",
    re.IGNORECASE,
)


def anios_pedidos(texto: str) -> int:
    """Mayor número de años de experiencia que aparece junto a 'experiencia'."""
    maximo = 0
    for m in ANIOS.finditer(texto):
        contexto = texto[max(0, m.start() - 60): m.end() + 60].lower()
        if "experien" in contexto:
            n = int(m.group(1))
            if n < 15:
                maximo = max(maximo, n)
    return maximo


class Filtro:
    def __init__(self, cfg: dict):
        f = cfg["filtro"]
        self.debe = _regex(f["titulo_debe_contener"])
        self.excluye = _regex(f["titulo_excluye"])
        self.desc_excluye = _regex(f["descripcion_excluye"])
        self.suma = {k.lower(): int(v) for k, v in f["suma"].items()}
        self.minimo = int(f["puntuacion_minima"])
        self.max_anios = int(f["max_anios_experiencia"])

    def titulo_valido(self, o: Oferta) -> bool:
        return bool(self.debe.search(o.titulo)) and not self.excluye.search(o.titulo)

    def evaluar(self, o: Oferta) -> tuple[bool, str]:
        """Devuelve (aceptada, motivo_si_se_descarta) y rellena puntuación y motivos."""
        if not self.titulo_valido(o):
            return False, "título fuera de perfil"
        if o.descripcion:
            if self.desc_excluye.search(o.descripcion):
                return False, "pide matrícula/convenio o idioma no disponible"
            anios = anios_pedidos(o.descripcion)
            if anios > self.max_anios:
                return False, f"pide {anios} años de experiencia"
        texto = f"{o.titulo} {o.descripcion}".lower()
        puntos, motivos = 0, []
        for palabra, valor in self.suma.items():
            if re.search(rf"(?<!\w){re.escape(palabra)}(?!\w)", texto):
                puntos += valor
                motivos.append(palabra)
        o.puntuacion, o.motivos = puntos, motivos
        if puntos < self.minimo:
            return False, "puntuación baja"
        return True, ""
