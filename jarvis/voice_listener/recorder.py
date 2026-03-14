import sys, wave, numpy as np, subprocess, os

if len(sys.argv) < 2:
    print('Uso: python recorder.py <output.wav>', file=sys.stderr)
    sys.exit(1)

out = sys.argv[1].replace('\\', '/')

# Grabar via oneliner en subprocess separado para evitar bug de PortAudio
code = f"""
import wave, numpy as np, pyaudiowpatch as p
pa=p.PyAudio()
s=pa.open(format=p.paInt16,channels=1,rate=48000,input=True,input_device_index=15,frames_per_buffer=1024)
frames=[s.read(1024) for _ in range(int(48000/1024*8))]
s.stop_stream();s.close();pa.terminate()
raw=b''.join(frames)
audio=np.frombuffer(raw,dtype=np.int16).astype(float)/32767
nl=int(len(audio)*16000/48000)
audio=np.interp(np.linspace(0,len(audio)-1,nl),np.arange(len(audio)),audio)
wf=wave.open(r'{out}','wb');wf.setnchannels(1);wf.setsampwidth(2);wf.setframerate(16000)
wf.writeframes((audio*32767).astype(np.int16).tobytes());wf.close()
print('[recorder] OK')
"""

result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
if result.returncode != 0:
    print(result.stderr, file=sys.stderr)
    sys.exit(3)
print(result.stdout.strip())
sys.exit(0)
