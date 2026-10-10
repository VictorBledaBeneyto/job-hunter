# Job Hunter

Busca ofertas de empleo junior de desarrollo de software, datos e IA dos veces al día, las filtra según un perfil configurable y envía un resumen por correo con la descripción y el enlace de cada oferta.

Funciona solo con **GitHub Actions**: no hace falta servidor ni tener el ordenador encendido.

![Python](https://img.shields.io/badge/python-3.12-blue) ![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF)

## Cómo funciona

```
GitHub Actions (cron 2 veces al día)
  └─ job_hunter.main
       ├─ fuentes/linkedin.py     → API pública de invitados de LinkedIn
       ├─ fuentes/tecnoempleo.py  → resultados públicos de Tecnoempleo
       ├─ fuentes/infojobs.py     → API oficial de InfoJobs (opcional)
       ├─ filtro.py               → descarta senior, +N años, prácticas con matrícula… y puntúa
       ├─ estado.py               → recuerda lo ya enviado (caché de Actions, no se publica)
       └─ correo.py               → correo HTML por Gmail (SMTP)
```

- **Filtro por título:** tiene que parecer un puesto de desarrollo, datos o IA y no ser senior, lead, manager, etc.
- **Filtro por descripción:** descarta las ofertas que piden más años de experiencia de los configurados, las que exigen estar matriculado o un convenio de prácticas, y las que piden idiomas que no se tienen.
- **Puntuación:** suma puntos por palabras clave (junior, Python, Java, Spring, SQL, machine learning…). Solo se envían las que superan el mínimo, ordenadas de más a menos.
- **Sin repeticiones:** una oferta ya enviada no vuelve a llegar (durante 45 días), y la misma oferta publicada en dos portales solo llega una vez.
- **Robusto:** si un portal falla o bloquea la petición, el resto sigue funcionando y el correo incluye un aviso.

Todo se ajusta en [`config.yaml`](config.yaml): palabras clave, ubicaciones, puntuaciones, exclusiones…

## Puesta en marcha

### 1. Contraseña de aplicación de Gmail

Gmail no deja usar tu contraseña normal desde un script. Necesitas una **contraseña de aplicación**:

1. Activa la verificación en dos pasos en tu cuenta de Google, si no la tienes.
2. Entra en <https://myaccount.google.com/apppasswords>, crea una con el nombre "Job Hunter" y copia los 16 caracteres.

### 2. Secrets del repositorio

En GitHub: **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Valor | Obligatorio |
|---|---|---|
| `GMAIL_USER` | La cuenta de Gmail que envía el correo | Sí |
| `GMAIL_APP_PASSWORD` | La contraseña de aplicación del paso 1 | Sí |
| `MAIL_TO` | Dónde quieres recibirlo (si falta, se usa `GMAIL_USER`) | No |
| `INFOJOBS_CLIENT_ID` / `INFOJOBS_CLIENT_SECRET` | Credenciales de una app en <https://developer.infojobs.net> | No |

Los secrets están cifrados y **no son visibles** aunque el repositorio sea público, ni siquiera en los logs.

### 3. Probarlo

**Actions → Buscar ofertas → Run workflow**. En un par de minutos debería llegarte el correo. Después se ejecuta solo a las 08:05 y 17:05 (hora de España en verano; una hora antes en invierno).

## Ejecutarlo en local

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt -r requirements-dev.txt

pytest                              # tests
python -m job_hunter.main --dry-run # no envía nada: genera salida.html con el correo
```

Para enviar de verdad en local, define las variables `GMAIL_USER`, `GMAIL_APP_PASSWORD` y `MAIL_TO` antes de ejecutar `python -m job_hunter.main`.

## Privacidad

Este repositorio es público, así que:

- No contiene datos personales: ni correo, ni teléfono, ni CV.
- Las credenciales van en los Secrets de GitHub.
- La lista de ofertas ya vistas se guarda en la caché privada de Actions y está en `.gitignore`.

## Limitaciones

- LinkedIn limita las peticiones desde servidores en la nube. Si responde con error 429 o 999, ese día no habrá ofertas de LinkedIn y el correo lo avisará.
- Los portales pueden cambiar su HTML. Si una fuente deja de devolver resultados, hay que revisar su parser (los tests usan HTML de ejemplo en `tests/fixtures`).
- Uso personal y con pocas peticiones. Respeta las condiciones de uso de cada portal.

## Tecnologías

Python 3.12 · Requests · BeautifulSoup · PyYAML · pytest · GitHub Actions (cron, cache, secrets) · SMTP
