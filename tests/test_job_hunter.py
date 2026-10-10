from pathlib import Path

import yaml

from job_hunter.filtro import Filtro, anios_pedidos
from job_hunter.fuentes import infojobs, linkedin, tecnoempleo
from job_hunter.modelo import Oferta
from job_hunter.correo import construir_html

RAIZ = Path(__file__).resolve().parents[1]
FIX = Path(__file__).parent / "fixtures"
CFG = yaml.safe_load((RAIZ / "config.yaml").read_text(encoding="utf-8"))


def oferta(titulo, desc=""):
    return Oferta("Test", "1", titulo, "Empresa", "Valencia", "https://example.com", descripcion=desc)


# ---------- parsers ----------
def test_linkedin_listado():
    ofertas = linkedin.parsear_listado((FIX / "linkedin_listado.html").read_text(encoding="utf-8"))
    assert len(ofertas) == 2
    o = ofertas[0]
    assert o.id == "4400000001"
    assert o.titulo == "Desarrollador Python Junior"
    assert o.empresa == "Empresa Ejemplo"
    assert o.ubicacion == "Valencia, Comunidad Valenciana, España"
    assert o.url == "https://www.linkedin.com/jobs/view/4400000001/"
    assert o.fecha == "2026-10-10"


def test_linkedin_descripcion():
    html = '<div class="show-more-less-html__markup"><p>Buscamos <b>junior</b></p><ul><li>Python</li></ul></div>'
    assert linkedin.parsear_descripcion(html) == "Buscamos\njunior\nPython"


def test_tecnoempleo_listado():
    ofertas = tecnoempleo.parsear_listado((FIX / "tecnoempleo_listado.html").read_text(encoding="utf-8"))
    assert len(ofertas) == 1
    o = ofertas[0]
    assert o.id == "67b2115572c203d37146"
    assert o.titulo == "Becario/a DevOps"
    assert o.empresa == "UST"
    assert o.ubicacion == "100% remoto"
    assert o.fecha == "09/10/2026"
    assert "talento" in o.descripcion


def test_infojobs_parsear():
    datos = {"items": [{"id": "abc", "title": "Programador Java Junior", "author": {"name": "ACME"},
                        "city": "Valencia", "link": "https://www.infojobs.net/x/of-iabc",
                        "published": "2026-10-10T08:00:00.000Z",
                        "experienceMin": {"value": "Al menos 1 año"}}]}
    o = infojobs.parsear(datos)[0]
    assert (o.id, o.empresa, o.fecha) == ("abc", "ACME", "2026-10-10")
    assert "1 año" in o.descripcion


# ---------- filtro ----------
def test_anios():
    assert anios_pedidos("Se requieren 3 años de experiencia en Java") == 3
    assert anios_pedidos("At least 5 years of experience") == 5
    assert anios_pedidos("Experiencia: +2 años") == 2
    assert anios_pedidos("Formación de 6 meses") == 0


def test_filtro_acepta_junior():
    f = Filtro(CFG)
    o = oferta("Desarrollador Python Junior", "Sin experiencia. Python, SQL y Docker. Teletrabajo.")
    ok, _ = f.evaluar(o)
    assert ok and o.puntuacion >= 3 and "python" in o.motivos


def test_filtro_descarta_senior():
    ok, motivo = Filtro(CFG).evaluar(oferta("Senior Java Developer"))
    assert not ok and motivo == "título fuera de perfil"


def test_filtro_descarta_experiencia():
    ok, motivo = Filtro(CFG).evaluar(oferta("Desarrollador Java", "Requisitos: 4 años de experiencia con Spring"))
    assert not ok and "4 años" in motivo


def test_filtro_descarta_convenio():
    o = oferta("Prácticas Desarrollo Software", "Imprescindible estar matriculado en grado o máster")
    ok, motivo = Filtro(CFG).evaluar(o)
    assert not ok and "matrícula" in motivo


def test_filtro_titulo_no_tech():
    ok, _ = Filtro(CFG).evaluar(oferta("Dependiente de tienda"))
    assert not ok


def test_duplicados():
    a = Oferta("LinkedIn", "1", "Dev Junior", "ACME S.L.", "", "")
    b = Oferta("Tecnoempleo", "x", "dev junior", "ACME SL", "", "")
    assert a.clave_duplicado == b.clave_duplicado


def test_correo_html():
    o = oferta("Desarrollador <Junior>", "Python")
    o.motivos = ["python"]
    html = construir_html([o], {"LinkedIn": 1}, ["Tecnoempleo: error"])
    assert "&lt;Junior&gt;" in html and "Avisos" in html
