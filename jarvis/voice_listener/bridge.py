import json, time, os, sys, subprocess

BASE    = os.path.dirname(os.path.abspath(__file__))
STATE   = os.path.join(BASE, 'bridge_state.json')
AUDIO   = os.path.join(BASE, 'bridge_audio.wav')
MAX_DUR = 15

GRAB_CODE = f'''
import pyaudiowpatch as p, numpy as np, wave
CHUNK,RATE,DEVICE,WHISPER=1024,48000,15,16000
THRESH,SIL_DUR,MAX_DUR=0.0001,1.5,{MAX_DUR}
pa=p.PyAudio()
s=pa.open(format=p.paInt16,channels=1,rate=RATE,input=True,input_device_index=DEVICE,frames_per_buffer=CHUNK)
frames=[]; sc=0; hv=False; sn=int(SIL_DUR*RATE/CHUNK); mc=int(MAX_DUR*RATE/CHUNK)
for _ in range(mc):
    data=s.read(CHUNK,exception_on_overflow=False); frames.append(data)
    rms=float(np.sqrt(np.mean(np.frombuffer(data,dtype=np.int16).astype(float)**2)))/32767
    if rms>THRESH: hv=True; sc=0
    elif hv: sc+=1
    if hv and sc>=sn: break
s.stop_stream(); s.close(); pa.terminate()
audio=np.frombuffer(b"".join(frames),dtype=np.int16).astype(float)/32767
nl=int(len(audio)*WHISPER/RATE)
audio=np.interp(np.linspace(0,len(audio)-1,nl),np.arange(len(audio)),audio)
wf=wave.open(r"{AUDIO}","wb"); wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(WHISPER)
wf.writeframes((audio*32767).astype(np.int16).tobytes()); wf.close()
print("OK")
'''

def ss(e, m=''):
    json.dump({'estado': e, 'msg': m, 'ts': time.time()}, open(STATE, 'w'))

def gs():
    try: return json.load(open(STATE))
    except: return {'estado': 'idle'}

ss('idle')
print('[bridge] Listo. Esperando comandos...')
sys.stdout.flush()

while True:
    if gs().get('estado') == 'record':
        ss('recording')
        print('[bridge] Grabando...'); sys.stdout.flush()
        try:
            result = subprocess.run(
                [sys.executable, '-c', GRAB_CODE],
                timeout=MAX_DUR + 10,
                capture_output=True, text=True
            )
            if result.returncode == 0:
                ss('done')
                print('[bridge] OK')
            else:
                ss('error', result.stderr.strip())
                print(f'[bridge] Error: {result.stderr.strip()}')
        except Exception as e:
            ss('error', str(e))
            print(f'[bridge] Exception: {e}')
        sys.stdout.flush()
    time.sleep(0.2)
