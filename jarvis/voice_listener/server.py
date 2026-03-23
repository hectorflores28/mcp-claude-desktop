"""
JARVIS - voice-listener (Speech-to-Text)
Servidor MCP para capturar voz del micrófono y transcribirla con faster-whisper.
Usa sounddevice para compatibilidad con Windows (más estable que PyAudio).
"""

from mcp.server.fastmcp import FastMCP
import os
import tempfile
import wave
import numpy as np
import pyaudiowpatch as pyaudio
from faster_whisper import WhisperModel
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("voice-listener")

# ─── Configuración ────────────────────────────────────────────────────────────
WHISPER_MODEL_SIZE  = os.getenv("WHISPER_MODEL_SIZE", "base")
WHISPER_LANGUAGE    = os.getenv("WHISPER_LANGUAGE", "es")
SAMPLE_RATE         = int(os.getenv("SAMPLE_RATE", "16000"))         # tasa para Whisper
RECORD_RATE         = int(os.getenv("RECORD_RATE", "48000"))          # tasa real del dispositivo
SILENCE_THRESHOLD   = float(os.getenv("SILENCE_THRESHOLD", "0.01"))  # RMS normalizado 0.0-1.0
SILENCE_DURATION    = float(os.getenv("SILENCE_DURATION", "2.0"))    # segundos de silencio para cortar
MAX_DURATION        = int(os.getenv("MAX_DURATION", "30"))            # segundos máximos
DEVICE_INDEX        = os.getenv("DEVICE_INDEX", None)                 # None = default del sistema

# ─── Cargar modelo Whisper una sola vez ───────────────────────────────────────
print(f"[voice-listener] Cargando modelo Whisper '{WHISPER_MODEL_SIZE}'...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("[voice-listener] Modelo listo. Esperando llamadas...")


def grabar_hasta_silencio() -> str:
    """
    Delega la grabacion al bridge.py que corre en sesion interactiva.
    Escribe bridge_state.json con estado=record y espera done.
    """
    import json, time

    base       = os.path.dirname(os.path.abspath(__file__))
    state_file = os.path.join(base, 'bridge_state.json')
    audio_file = os.path.join(base, 'bridge_audio.wav')

    # Verificar que el bridge esta corriendo
    if not os.path.exists(state_file):
        raise RuntimeError('bridge.py no esta corriendo. Ejecuta: python bridge.py')

    # Enviar comando de grabacion
    with open(state_file, 'w') as f:
        json.dump({'estado': 'record', 'ts': time.time()}, f)

    print('[voice-listener] Esperando audio del bridge...')

    # Esperar hasta done o error
    timeout = MAX_DURATION + 10
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(0.3)
        try:
            with open(state_file) as f:
                state = json.load(f)
        except:
            continue
        if state.get('estado') == 'done':
            break
        if state.get('estado') == 'error':
            raise RuntimeError(f"Bridge error: {state.get('msg', 'desconocido')}")
    else:
        raise RuntimeError('Timeout esperando al bridge')

    if not os.path.exists(audio_file):
        raise RuntimeError('bridge_audio.wav no encontrado')

    # Copiar a temp para no bloquear el archivo
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    tmp_path = tmp.name
    tmp.close()
    import shutil
    shutil.copy2(audio_file, tmp_path)

    # Reset estado
    with open(state_file, 'w') as f:
        json.dump({'estado': 'idle', 'ts': time.time()}, f)

    return tmp_path


def grabar_hasta_silencio_inline() -> str:
    """
    Graba audio con sounddevice hasta detectar silencio prolongado.
    Devuelve la ruta del archivo WAV temporal.
    """
    device_index = int(DEVICE_INDEX) if DEVICE_INDEX is not None else None
    record_rate = RECORD_RATE
    try:
        info = sd.query_devices(device_index, 'input')
        print(f"[voice-listener] Dispositivo: [{device_index}] {info['name']} @ {record_rate} Hz")
    except Exception as diag_e:
        print(f"[voice-listener] Advertencia diagnostico: {diag_e}")

    print("[voice-listener] Escuchando... (habla ahora)")

    chunk_duration = 0.1  # segundos por chunk
    chunk_samples  = int(SAMPLE_RATE * chunk_duration)
    silence_chunks_needed = int(SILENCE_DURATION / chunk_duration)
    max_chunks = int(MAX_DURATION / chunk_duration)

    frames = []
    silence_count = 0
    has_voice = False

    with sd.InputStream(
        samplerate=record_rate,
        channels=1,
        dtype='float32',
        device=device_index,
        blocksize=chunk_samples
    ) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_samples)
            frames.append(chunk.copy())
            rms = float(np.sqrt(np.mean(chunk ** 2)))

            if rms > SILENCE_THRESHOLD:
                has_voice = True
                silence_count = 0
            else:
                if has_voice:
                    silence_count += 1

            if has_voice and silence_count >= silence_chunks_needed:
                break

    print("[voice-listener] Silencio detectado, procesando audio...")

    # Concatenar audio
    audio_np = np.concatenate(frames, axis=0).flatten()

    # Resamplear de RECORD_RATE → SAMPLE_RATE para Whisper
    if record_rate != SAMPLE_RATE:
        new_length = int(len(audio_np) * SAMPLE_RATE / record_rate)
        audio_np = np.interp(
            np.linspace(0, len(audio_np) - 1, new_length),
            np.arange(len(audio_np)),
            audio_np
        )

    audio_int16 = (audio_np * 32767).astype(np.int16)

    # Guardar como WAV temporal
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    with wave.open(tmp.name, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_int16.tobytes())

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

        segments, info = whisper_model.transcribe(
            tmp_path,
            language=WHISPER_LANGUAGE,
            beam_size=5
        )

        os.unlink(tmp_path)

        texto = " ".join(seg.text.strip() for seg in segments).strip()

        if texto:
            print(f"[voice-listener] Transcripcion: {texto}")
            return texto
        else:
            return "No se detectó texto en el audio."

    except Exception as e:
        return f"Error al escuchar/transcribir: {str(e)}"


@mcp.tool(name="list_audio_devices", description="Lista los dispositivos de audio disponibles en el sistema")
def list_audio_devices() -> str:
    """
    Lista dispositivos de entrada disponibles con sounddevice.
    """
    try:
        devices = sd.query_devices()
        lines = ["Dispositivos de audio disponibles (sounddevice):\n"]
        for i, d in enumerate(devices):
            if d['max_input_channels'] > 0:
                lines.append(
                    f"  [{i}] {d['name']} "
                    f"(inputs: {d['max_input_channels']}, "
                    f"rate: {int(d['default_samplerate'])} Hz)"
                )
        return "\n".join(lines)
    except Exception as e:
        return f"Error al listar dispositivos: {str(e)}"


if __name__ == "__main__":
    mcp.run()
