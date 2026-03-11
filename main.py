"""
ilPostino — Director de Agentes
Transforma información dispersa en una web personal viva.

Uso:
    python main.py                    # prueba con datos de ejemplo
    python main.py --serve            # inicia servidor HTTP en :8080
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Añadir el directorio del proyecto al path
sys.path.insert(0, str(Path(__file__).parent))

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.director import director
import tools.cloud_storage as storage

APP_NAME = "ilpostino"

# Datos de prueba para el primer onboarding
DATOS_PRUEBA = {
    "user_id": "saira_001",
    "name": "Saira García",
    "bio": "Soy diseñadora y emprendedora digital. Me dedico a crear productos digitales que conectan a las personas con lo que más les importa. Tengo experiencia en diseño UX, branding y desarrollo de comunidades online.",
    "projects": [
        "ilPostino: plataforma de marca personal vía Telegram",
        "Amapola Studio: estudio de diseño digital independiente",
        "Comunidad Creativa: newsletter semanal sobre creatividad y tecnología"
    ],
    "links": [
        "https://linkedin.com/in/sairagarcia",
        "https://instagram.com/sairagarcia",
        "https://twitter.com/sairagarcia"
    ],
    "email": "asuasaira@gmail.com",
    "style_preferences": "Quiero algo moderno, limpio y femenino. Me gustan los colores tierra, el beige, y los acentos en terracota. Tipografía elegante pero legible. Estilo editorial.",
    "photo_urls": []
}


def _guardar_pendiente(datos: dict):
    """Guarda los datos antes de procesar para poder recuperarlos si falla."""
    storage.escribir_json(f"pendientes/{datos['user_id']}.json", datos)


def _eliminar_pendiente(user_id: str):
    storage.eliminar(f"pendientes/{user_id}.json")


async def ejecutar_onboarding(datos: dict) -> str:
    """Ejecuta el pipeline de onboarding completo con retry automático en caso de 429."""
    _guardar_pendiente(datos)

    max_intentos = 3
    for intento in range(1, max_intentos + 1):
        try:
            resultado = await _ejecutar_pipeline(datos)
            _eliminar_pendiente(datos["user_id"])
            return resultado
        except Exception as e:
            if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                espera = 60 * intento
                print(f"⚠️  429 en intento {intento}/{max_intentos}, esperando {espera}s...")
                await asyncio.sleep(espera)
            else:
                raise
    raise Exception(f"Pipeline falló después de {max_intentos} intentos")


async def _ejecutar_pipeline(datos: dict) -> str:
    """Ejecuta el pipeline una vez."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=director,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=datos["user_id"],
        state={"raw_form_data": datos, "user_id": datos["user_id"]},
    )


    mensaje = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Nuevo usuario con onboarding: {json.dumps(datos, ensure_ascii=False)}"
        )],
    )

    print(f"\n🚀 ilPostino iniciando para: {datos['name']}")
    print("=" * 50)

    respuesta = ""
    async for evento in runner.run_async(
        user_id=datos["user_id"],
        session_id=session.id,
        new_message=mensaje,
    ):
        # Mostrar qué agente está activo
        if hasattr(evento, "author") and evento.author:
            agente = evento.author
            # Tool calls
            if evento.content:
                for parte in evento.content.parts:
                    if hasattr(parte, "function_call") and parte.function_call:
                        fn = parte.function_call
                        args_preview = str(fn.args)[:120]
                        print(f"  🔧 [{agente}] → {fn.name}({args_preview}...)")
                    elif hasattr(parte, "function_response") and parte.function_response:
                        fn = parte.function_response
                        resp_preview = str(fn.response)[:120]
                        print(f"  ✅ [{agente}] ← {fn.name}: {resp_preview}...")
                    elif hasattr(parte, "text") and parte.text:
                        texto = parte.text.strip()
                        if texto:
                            preview = texto[:200].replace("\n", " ")
                            print(f"  💬 [{agente}]: {preview}{'...' if len(texto) > 200 else ''}")

        if evento.is_final_response() and evento.content:
            for parte in evento.content.parts:
                if hasattr(parte, "text") and parte.text:
                    respuesta += parte.text

    print(f"\n✅ Pipeline completado para {datos['name']}")
    return respuesta


async def ejecutar_actualizacion_telegram(user_id: str, mensaje_telegram: str) -> str:
    """Procesa una actualización que llega por Telegram."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=director,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=user_id,
        state={"telegram_raw": mensaje_telegram, "user_id": user_id},
    )

    mensaje = types.Content(
        role="user",
        parts=[types.Part.from_text(
            text=f"Actualización Telegram de usuario {user_id}: {mensaje_telegram}"
        )],
    )

    print(f"\n📱 Actualización Telegram de: {user_id}")
    print(f"Mensaje: {mensaje_telegram}")
    print("=" * 50)

    respuesta = ""
    async for evento in runner.run_async(
        user_id=user_id,
        session_id=session.id,
        new_message=mensaje,
    ):
        if evento.is_final_response() and evento.content:
            for parte in evento.content.parts:
                if hasattr(parte, "text") and parte.text:
                    respuesta += parte.text
                    print(parte.text)

    return respuesta


if __name__ == "__main__":
    # Verificar API key
    if not os.environ.get("GOOGLE_API_KEY"):
        print("❌ Error: GOOGLE_API_KEY no configurada")
        print("   Ejecutá: export GOOGLE_API_KEY='tu-api-key'")
        sys.exit(1)

    print("🧠 ilPostino — Director de Agentes")
    print("Construyendo tu web personal con IA...\n")

    asyncio.run(ejecutar_onboarding(DATOS_PRUEBA))
