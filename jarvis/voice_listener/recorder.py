"""recorder.py - Script de grabacion independiente.
Corre como subprocess para acceder al audio de Windows desde Claude Desktop.
Uso: python recorder.py <output.wav>
"""
import sys
import os
import wave
import numpy as np

def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if not os.path.exists(env_path):
        return
    with open(env_path, encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env()

DEVICE_INDEX      = os.environ.get('DEVICE_INDEX', None)
RECORD_RATE       = int(os.environ.get('RECORD_RATE', '48000'))
SAMPLE_RATE       = int(os.environ.get('SAMPLE_RATE', '16000'))
SILENCE_THRESHOLD = float(os.environ.get('SILENCE_THRESHOLD', '0.01'))
SILENCE_DURATION  = float(os.environ.get('SILENCE_DURATION', '2.0'))
MAX_DURATION      = int(os.environ.get('MAX_DURATION', '30'))

if len(sys.argv) < 2:
    print('Uso: python recorder.py <output.wav>', file=sys.stderr)
    sys.exit(1)

output_path = sys.argv[1]

try:
    import sounddevice as sd
except ImportError:
    print('sounddevice no instalado', file=sys.stderr)
    sys.exit(2)

device_index = int(DEVICE_INDEX) if DEVICE_INDEX is not None else None

try:
    info = sd.query_devices(device_index, 'input')
    print(f'[recorder] Dispositivo: [{device_index}] {info["name"]} @ {RECORD_RATE} Hz')
except Exception as e:
    print(f'[recorder] Warning: {e} - usando default', file=sys.stderr)
    device_index = None

chunk_dur     = 0.1
chunk_samp    = int(RECORD_RATE * chunk_dur)
max_chunks    = int(MAX_DURATION / chunk_dur)
silence_needed = int(SILENCE_DURATION / chunk_dur)

frames = []
silence_count = 0
has_voice = False

print('[recorder] Escuchando...')

# Intentar WASAPI modo compartido, luego fallback a default
wasapi_kwargs = {}
try:
    import sounddevice as _sd_check
    hostapis = _sd_check.query_hostapis()
    wasapi_idx = next((i for i, h in enumerate(hostapis) if 'WASAPI' in h['name']), None)
    if wasapi_idx is not None and device_index is not None:
        dev_info = _sd_check.query_devices(device_index)
        if dev_info['hostapi'] == wasapi_idx:
            wasapi_kwargs['extra_settings'] = sd.WasapiSettings(exclusive=False)
except Exception:
    pass

try:
    with sd.InputStream(samplerate=RECORD_RATE, channels=1, dtype='float32',
                        device=device_index, blocksize=chunk_samp, **wasapi_kwargs) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_samp)
            frames.append(chunk.copy())
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms > SILENCE_THRESHOLD:
                has_voice = True
                silence_count = 0
            else:
                if has_voice:
                    silence_count += 1
            if has_voice and silence_count >= silence_needed:
                break
except Exception as e:
    print(f'Error grabando: {e}', file=sys.stderr)
    sys.exit(3)

if not frames:
    print('No se capturo audio', file=sys.stderr)
    sys.exit(4)

audio_np = np.concatenate(frames).flatten()

if RECORD_RATE != SAMPLE_RATE:
    new_len = int(len(audio_np) * SAMPLE_RATE / RECORD_RATE)
    audio_np = np.interp(
        np.linspace(0, len(audio_np) - 1, new_len),
        np.arange(len(audio_np)),
        audio_np
    )

audio_int16 = (audio_np * 32767).astype(np.int16)

with wave.open(output_path, 'wb') as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_int16.tobytes())

print(f'[recorder] WAV guardado: {output_path}')
sys.exit(0)
"""
Recorder.py - Script de grabación independiente.
Corre como subprocess separado para acceder al audio de Windows.
Uso: python recorder.py <output.wav>
"""
import sys
import os
import wave
import tempfile
import numpy as np

# Cargar .env
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            os.environ[key.strip()] = val.strip()

load_env()

DEVICE_INDEX = os.getenv("DEVICE_INDEX", None)
RECORD_RATE = int(os.getenv("RECORD_RATE", "48000"))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
SILENCE_THRESHOLD = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
SILENCE_DURATION = float(os.getenv("SILENCE_DURATION", "2.0"))
MAX_DURATION = int(os.getenv("MAX_DURATION", "30"))

if len(sys.argv) < 2:
    print("Uso: python recorder.py <output.wav>", file=sys.stderr)
    sys.exit(1)

try:
    import soundevice as sd
except ImportError:
    print("sounddevice no instalado", file=sys.stderr)
    sys.exit(2)

device_index = int(DEVICE_INDEX) if DEVICE_INDEX is not None else None

# Intentar abrir con el device configurado, si falla usar default
try:
    info = sd.query_devices(device_index, "input")
    print(f'[recorder] Usando dispositivo: {info["name"]} (index {device_index})')
except Exception as e:
    print(f'[recorder] Error al consultar el dispositivo: {e}', file=sys.stderr)
    device_index = None

chunk_dur = 0.1
chunk_samp = int(RECORD_RATE * chunk_dur)
max_chunks = int(MAX_DURATION / chunk_dur)
silence_needed = int(SILENCE_DURATION / chunk_dur)

frames = []
silence_count = 0
has_voice = False

print('[recorder] Grabando... (habla ahora)')

try:
    with sd.InputStream(samplerate=RECORD_RATE, channels=1, dtype='float32', device=device_index, blocksize=chunk_samp) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_samp)
            frames.append(chunk.copy())
            rms = float(np.sqrt(np.mean(chunk ** 2)))

            if rms > SILENCE_THRESHOLD:
                has_voice = True
                silence_count = 0
            else:
                if has_voice:
                    silence_count += 1
            if has_voice and silence_count >= silence_needed:
                break
except Exception as e:
    print(f'[recorder] Error durante la grabación: {e}', file=sys.stderr)
    sys.exit(3)

if not frames:
    print("[recorder] No se grabó audio", file=sys.stderr)
    sys.exit(4)

audio_np = np.concatenate(frames, axis=0).flatten()

# Resamplea si es necesario (RECORD_RATE → SAMPLE_RATE)
if RECORD_RATE != SAMPLE_RATE:
    new_length = int(len(audio_np) * SAMPLE_RATE / RECORD_RATE)
    audio_np = np.interp(
        np.linspace(0, len(audio_np) - 1, new_length),
        np.arange(len(audio_np)),
        audio_np
    )

audio_int16 = np.int16(audio_np * 32767).astype(np.int16)

with wave.open(output_path, "wb") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(SAMPLE_RATE)
    wf.writeframes(audio_int16.tobytes())

print(f'[recorder] Grabación guardada en: {output_path}')