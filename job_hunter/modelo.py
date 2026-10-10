from dataclasses import dataclass, field


@dataclass
class Oferta:
    fuente: str
    id: str
    titulo: str
    empresa: str
    ubicacion: str
    url: str
    fecha: str = ""
    descripcion: str = ""
    puntuacion: int = 0
    motivos: list = field(default_factory=list)

    @property
    def clave(self) -> str:
        """Identificador único entre ejecuciones."""
        return f"{self.fuente}:{self.id}"

    @property
    def clave_duplicado(self) -> str:
        """Detecta la misma oferta publicada en varios portales."""
        norm = lambda s: "".join(c for c in s.lower() if c.isalnum())
        return f"{norm(self.titulo)}|{norm(self.empresa)}"
