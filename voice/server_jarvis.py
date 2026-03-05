from mcp.server.fastmcp import FastMCP
import requests
import tempfile
import os
import pygame
import time

mcp = FastMCP("Speak")

ELEVENLABS_API_KEY = "sk_5889e23e7bff0170171ae29397e4d1b49da6f07338e9fbd4"
VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam

@mcp.tool(name="say", description="Haz que el ordenador hable en voz alta")
def say(texto: str) -> str:
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
    headers = {
        "xi-api-key": ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": texto,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    }
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
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

if __name__ == "__main__":
    mcp.run()