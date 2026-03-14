import sounddevice as sd
import numpy as np

devices = sd.query_devices()
print('Probando dispositivos de entrada...')
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        try:
            with sd.InputStream(samplerate=int(d['default_samplerate']), channels=1, dtype='float32', device=i, blocksize=1024) as s:
                s.read(1024)
            print(f'  OK [{i}] {d[\"name\"]}')
        except Exception as e:
            print(f'  FAIL [{i}] {d[\"name\"]}: {e}')