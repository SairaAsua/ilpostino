"""
Sistema de eventos de Il Postino.
El bot llama a registrar_evento() en cada paso del pipeline.
Los eventos quedan en data/eventos.json y el dashboard los lee en tiempo real.
"""

from datetime import datetime
from . import cloud_storage as storage

_KEY = "eventos.json"


def registrar_evento(
    tipo: str,
    user_id: str,
    nombre: str = "",
    detalle: str = "",
    estado: str = "ok",
    url: str = "",
):
    """Agrega un evento al log.

    Tipos: mensaje_recibido | pipeline_iniciado | pipeline_completado |
           pipeline_error | email_enviado | blog_publicado | site_url
    """
    eventos = storage.leer_json(_KEY, [])

    eventos.append({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "tipo": tipo,
        "user_id": user_id,
        "nombre": nombre,
        "detalle": detalle[:300],
        "estado": estado,
        "url": url,
    })

    # Máximo 1000 eventos
    eventos = eventos[-1000:]
    storage.escribir_json(_KEY, eventos)
