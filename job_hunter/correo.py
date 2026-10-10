"""Construcción y envío del correo con las ofertas encontradas (Gmail por SMTP)."""
import os
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from .modelo import Oferta


def _resumen(texto: str, n: int = 350) -> str:
    texto = " ".join(texto.split())
    return texto if len(texto) <= n else texto[:n].rsplit(" ", 1)[0] + "…"


def construir_html(ofertas: list[Oferta], estadisticas: dict, errores: list[str]) -> str:
    filas = []
    for o in ofertas:
        etiquetas = "".join(
            f'<span style="background:#eef2ff;color:#3730a3;border-radius:10px;padding:1px 8px;'
            f'margin-right:4px;font-size:12px">{escape(m)}</span>' for m in o.motivos[:8])
        filas.append(f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:12px 14px;margin:0 0 12px">
          <div style="font-size:16px;font-weight:600">
            <a href="{escape(o.url)}" style="color:#1d4ed8;text-decoration:none">{escape(o.titulo)}</a>
          </div>
          <div style="color:#374151;margin:2px 0 6px">{escape(o.empresa)} · {escape(o.ubicacion)}
            <span style="color:#6b7280"> · {escape(o.fuente)} {escape(o.fecha)} · puntuación {o.puntuacion}</span></div>
          <div style="margin-bottom:6px">{etiquetas}</div>
          <div style="color:#4b5563;font-size:14px">{escape(_resumen(o.descripcion)) or '<i>Sin descripción</i>'}</div>
        </div>""")
    cuerpo = "".join(filas) or "<p>No hay ofertas nuevas que encajen en esta ejecución.</p>"
    stats = " · ".join(f"{k}: {v}" for k, v in estadisticas.items())
    errs = "".join(f"<li>{escape(e)}</li>" for e in errores)
    return f"""<html><body style="font-family:Arial,Helvetica,sans-serif;max-width:720px;margin:auto">
      <h2 style="margin-bottom:4px">{len(ofertas)} {"oferta nueva" if len(ofertas) == 1 else "ofertas nuevas"} para ti</h2>
      <p style="color:#6b7280;margin-top:0">{datetime.now():%d/%m/%Y %H:%M} · {escape(stats)}</p>
      {cuerpo}
      {f'<p style="color:#b45309"><b>Avisos:</b></p><ul style="color:#b45309">{errs}</ul>' if errores else ''}
      <p style="color:#9ca3af;font-size:12px">Job Hunter · GitHub Actions</p>
    </body></html>"""


def enviar(asunto: str, html: str) -> None:
    usuario = os.environ["GMAIL_USER"]
    clave = os.environ["GMAIL_APP_PASSWORD"]
    destino = os.environ.get("MAIL_TO", usuario)
    msg = MIMEMultipart("alternative")
    msg["Subject"], msg["From"], msg["To"] = asunto, usuario, destino
    msg.attach(MIMEText(html, "html", "utf-8"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
        s.login(usuario, clave)
        s.sendmail(usuario, [destino], msg.as_string())
