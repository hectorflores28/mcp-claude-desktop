"""
JARVIS - voice-jarvis (Text-to-Speech)
Servidor MCP para convertir texto a voz usando ElevenLabs API.
"""

from mcp.server.fastmcp import FastMCP
import requests
import tempfile
import os
import pygame
import time
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

mcp = FastMCP("voice-jarvis")

# Configuración desde .env
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pNInz6obpgDQGcFmaJgB")  # Adam por defecto
MODEL_ID = os.getenv("ELEVENLABS_MODEL_ID", "eleven_turbo_v2_5")


@mcp.tool(name="say", description="Convierte texto a voz y lo reproduce en voz alta usando ElevenLabs")
def say(texto: str) -> str:
    """
    Recibe un texto y lo convierte a audio usando ElevenLabs,
    luego lo reproduce en los altavoces del sistema.
    """
    if not ELEVENLABS_API_KEY:
        return "Error: ELEVENLABS_API_KEY no configurada en .env"

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": texto,
        "model_id": MODEL_ID,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            # Guardar audio temporal y reproducir
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as f:
                f.write(response.content)
                tmp_path = f.name

            pygame.mixer.init()
            pygame.mixer.music.load(tmp_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            os.unlink(tmp_path)
            return "Hablando"
        else:
            return f"Error ElevenLabs: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error al reproducir voz: {str(e)}"


if __name__ == "__main__":
    mcp.run()
