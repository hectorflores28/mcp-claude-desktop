"""
JARVIS - voice-listener (Speech-to-Text)
Servidor MCP para capturar voz del micrófono y transcribirla con faster-whisper.
Usa PyAudio para compatibilidad con Windows MME.
"""

from mcp.server.fastmcp import FastMCP
import os
import tempfile
import wave
import struct
import math
import pyaudio
import numpy as np
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("voice-listener")

# ─── Configuración ────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE  = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_LANGUAGE    = os.getenv("WHISPER_LANGUAGE", "es")
SAMPLE_RATE         = int(os.getenv("SAMPLE_RATE", "16000"))   # tasa objetivo para Whisper
RECORD_RATE         = int(os.getenv("RECORD_RATE", "44100"))    # tasa real del dispositivo
CHUNK               = int(os.getenv("CHUNK", "1024"))
SILENCE_THRESHOLD   = float(os.getenv("SILENCE_THRESHOLD", "500"))   # RMS amplitude
SILENCE_DURATION    = float(os.getenv("SILENCE_DURATION", "2.0"))    # segundos de silencio para cortar
MAX_DURATION        = int(os.getenv("MAX_DURATION", "30"))            # segundos máximos
DEVICE_INDEX        = os.getenv("DEVICE_INDEX", None)                 # None = default del sistema

# ─── Cargar modelo Whisper una sola vez ───────────────────────────────────────
print(f"[voice-listener] Cargando modelo Whisper '{WHISPER_MODEL_SIZE}'...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[voice-listener] Modelo listo. Esperando llamadas...")


def calcular_rms(data: bytes) -> float:
    """Calcula el nivel RMS (volumen) de un chunk de audio PCM 16-bit."""
    count = len(data) // 2
    if count == 0:
        return 0.0
    shorts = struct.unpack(f"{count}h", data)
    sum_sq = sum(s * s for s in shorts)
    return math.sqrt(sum_sq / count)


def grabar_hasta_silencio() -> str:
    """
    Graba audio con PyAudio hasta detectar silencio prolongado.
    Devuelve la ruta del archivo WAV temporal.
    """
    pa = pyaudio.PyAudio()

    # Seleccionar dispositivo
    device_index = int(DEVICE_INDEX) if DEVICE_INDEX is not None else None

    # Diagnóstico: imprimir info del dispositivo seleccionado
    try:
        info = pa.get_device_info_by_index(device_index) if device_index is not None else pa.get_default_input_device_info()
        print(f"[voice-listener] Dispositivo: [{device_index}] {info['name']}")
        print(f"[voice-listener] Rate nativa: {int(info['defaultSampleRate'])} Hz, canales: {info['maxInputChannels']}")
        print(f"[voice-listener] RECORD_RATE configurado: {RECORD_RATE} Hz")
    except Exception as diag_e:
        print(f"[voice-listener] Error al obtener info del dispositivo: {diag_e}")

    # Abrir stream de entrada a la tasa nativa del dispositivo
    stream = pa.open(
        format=pyaudio.paInt16,
        channels=1,
        rate=RECORD_RATE,
        input=True,
        input_device_index=device_index,
        frames_per_buffer=CHUNK
    )

    print("[voice-listener] 🎤 Escuchando... (habla ahora)")

    frames = []
    silence_chunks = 0
    silence_limit   = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK)
    max_chunks       = int(MAX_DURATION    * SAMPLE_RATE / CHUNK)
    has_voice        = False

    for _ in range(max_chunks):
        data = stream.read(CHUNK, exception_on_overflow=False)
        frames.append(data)
        rms = calcular_rms(data)

        if rms > SILENCE_THRESHOLD:
            has_voice = True
            silence_chunks = 0
        else:
            if has_voice:               # Solo contar silencio después de detectar voz
                silence_chunks += 1

        if has_voice and silence_chunks >= silence_limit:
            break

    stream.stop_stream()
    stream.close()
    pa.terminate()

    print("[voice-listener] ✅ Silencio detectado, procesando audio...")

    # Resamplear de RECORD_RATE → SAMPLE_RATE para Whisper
    raw_audio = b"".join(frames)
    if RECORD_RATE != SAMPLE_RATE:
        audio_np = np.frombuffer(raw_audio, dtype=np.int16).astype(np.float32)
        ratio = SAMPLE_RATE / RECORD_RATE
        new_length = int(len(audio_np) * ratio)
        resampled_np = np.interp(
            np.linspace(0, len(audio_np) - 1, new_length),
            np.arange(len(audio_np)),
            audio_np
        ).astype(np.int16)
        resampled = resampled_np.tobytes()
    else:
        resampled = raw_audio

    # Guardar como WAV temporal
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)   # 16-bit = 2 bytes
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(resampled)

    return tmp.name


@mcp.tool(name="listen", description="Escucha el micrófono y transcribe lo que dice el usuario usando Whisper")
def listen() -> str:
    """
    Activa el micrófono, graba hasta detectar silencio,
    y transcribe el audio con faster-whisper.
    Devuelve el texto transcrito.
    """
    try:
        tmp_path = grabar_hasta_silencio()

        # Transcribir con Whisper
        segments, info = whisper_model.transcribe(
            tmp_path,
            language=WHISPER_LANGUAGE,
            beam_size=5
        )

        os.unlink(tmp_path)

        texto = " ".join(seg.text.strip() for seg in segments).strip()

        if texto:
            print(f"[voice-listener] 📝 Transcripción: {texto}")
            return texto
        else:
            return "No se detectó texto en el audio."

    except Exception as e:
        return f"Error al escuchar/transcribir: {str(e)}"


@mcp.tool(name="list_audio_devices", description="Lista los dispositivos de audio disponibles en el sistema")
def list_audio_devices() -> str:
    """
    Útil para diagnosticar qué dispositivos de micrófono están disponibles
    y obtener el DEVICE_INDEX correcto para el .env
    """
    try:
        pa = pyaudio.PyAudio()
        lines = ["Dispositivos de audio disponibles:\n"]
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                lines.append(
                    f"  [{i}] {info['name']} "
                    f"(inputs: {info['maxInputChannels']}, "
                    f"rate: {int(info['defaultSampleRate'])} Hz)"
                )
        pa.terminate()
        return "\n".join(lines)
    except Exception as e:
        return f"Error al listar dispositivos: {str(e)}"


if __name__ == "__main__":
    mcp.run()
