"""
JARVIS - voice-listener (Speech-to-Text)
Servidor MCP para capturar voz del micrófono y transcribirla con faster-whisper.
"""

from mcp.server.fastmcp import FastMCP
import os
import tempfile
import numpy as np
import sounddevice as sd
import soundfile as sf
from faster_whisper import WhisperModel
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

mcp = FastMCP("voice-listener")

# Configuración desde .env
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "es")
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "2.0"))  # segundos de silencio para cortar
MAX_DURATION = int(os.getenv("MAX_DURATION", "30"))  # segundos máximos de grabación

# Cargar modelo Whisper una sola vez al iniciar
print(f"[voice-listener] Cargando modelo Whisper '{WHISPER_MODEL_SIZE}'...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[voice-listener] Modelo listo.")


def grabar_hasta_silencio() -> np.ndarray:
    """
    Graba audio desde el micrófono y corta automáticamente
    cuando detecta silencio prolongado.
    """
    frames = []
    silence_frames = 0
    silence_limit = int(SILENCE_DURATION * SAMPLE_RATE / 1024)

    print("[voice-listener] Escuchando... (habla ahora)")

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32', blocksize=1024) as stream:
        for _ in range(int(MAX_DURATION * SAMPLE_RATE / 1024)):
            data, _ = stream.read(1024)
            frames.append(data.copy())

            # Detectar silencio por nivel de volumen RMS
            rms = np.sqrt(np.mean(data ** 2))
            if rms < SILENCE_THRESHOLD:
                silence_frames += 1
            else:
                silence_frames = 0  # Reiniciar contador si hay sonido

            # Cortar si hay suficiente silencio (y ya grabamos algo)
            if silence_frames >= silence_limit and len(frames) > silence_limit:
                break

    print("[voice-listener] Silencio detectado, procesando...")
    return np.concatenate(frames, axis=0)


@mcp.tool(name="listen", description="Escucha el micrófono y transcribe lo que dice el usuario usando Whisper")
def listen() -> str:
    """
    Activa el micrófono, graba hasta detectar silencio,
    y transcribe el audio con faster-whisper.
    Devuelve el texto transcrito.
    """
    try:
        # Grabar audio
        audio_data = grabar_hasta_silencio()

        # Guardar audio temporal como WAV
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as f:
            sf.write(f.name, audio_data, SAMPLE_RATE)
            tmp_path = f.name

        # Transcribir con Whisper
        segments, info = whisper_model.transcribe(
            tmp_path,
            language=WHISPER_LANGUAGE,
            beam_size=5
        )

        # Limpiar archivo temporal
        os.unlink(tmp_path)

        # Unir segmentos transcritos
        texto = " ".join([seg.text.strip() for seg in segments])

        if texto:
            print(f"[voice-listener] Transcripción: {texto}")
            return texto
        else:
            return "No se detectó texto en el audio."

    except Exception as e:
        return f"Error al escuchar/transcribir: {str(e)}"


if __name__ == "__main__":
    mcp.run()
