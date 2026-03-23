"""
JARVIS - run_all.py
Levanta los 4 servidores MCP en procesos paralelos con un solo comando:
    python run_all.py

Servidores:
  - voice-jarvis   : Text-to-Speech (ElevenLabs)
  - voice-listener : Speech-to-Text (Whisper)
  - jarvis-skills  : Gestión de Skills / System Prompts
  - jarvis-memory  : Gestión de Datasets / Conocimiento
"""

import subprocess
import sys
import os
import signal
import time
import threading
from pathlib import Path

# ─── Directorio base (donde está este script) ────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()

# ─── Definición de servidores ────────────────────────────────────────────────
SERVIDORES = [
    {
        "nombre": "voice-jarvis",
        "script": BASE_DIR / "voice_jarvis" / "server.py",
        "color": "\033[94m",   # Azul
    },
    {
        "nombre": "voice-listener",
        "script": BASE_DIR / "voice_listener" / "server.py",
        "color": "\033[92m",   # Verde
    },
    {
        "nombre": "jarvis-skills",
        "script": BASE_DIR / "jarvis_skill" / "server.py",
        "color": "\033[93m",   # Amarillo
    },
    {
        "nombre": "jarvis-memory",
        "script": BASE_DIR / "jarvis_memory" / "server.py",
        "color": "\033[95m",   # Magenta
    },
]

RESET = "\033[0m"
ROJO  = "\033[91m"
BOLD  = "\033[1m"
CYAN  = "\033[96m"

procesos = []


def log(nombre, color, mensaje):
    timestamp = time.strftime("%H:%M:%S")
    print(f"{CYAN}[{timestamp}]{RESET} {color}{BOLD}[{nombre}]{RESET} {mensaje}", flush=True)


def leer_salida(nombre, color, stream, etiqueta="OUT"):
    """Lee un stream de un proceso línea por línea e imprime con color."""
    try:
        for linea in iter(stream.readline, ""):
            linea = linea.rstrip()
            if linea:
                log(nombre, color, linea)
    except Exception:
        pass


def iniciar_servidores():
    """Lanza cada servidor en un subproceso independiente."""
    python = sys.executable  # Usa el mismo Python que corre este script

    for srv in SERVIDORES:
        script = srv["script"]

        if not script.exists():
            log(srv["nombre"], ROJO, f"⚠️  Script no encontrado: {script}")
            continue

        log(srv["nombre"], srv["color"], f"Iniciando → {script}")

        try:
            proceso = subprocess.Popen(
                [python, str(script)],
                cwd=str(script.parent),      # Ejecutar desde carpeta del servidor (carga .env correctamente)
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                encoding="utf-8",
                errors="replace"
            )

            # Hilo para stdout
            hilo_out = threading.Thread(
                target=leer_salida,
                args=(srv["nombre"], srv["color"], proceso.stdout, "OUT"),
                daemon=True
            )
            hilo_out.start()

            # Hilo para stderr (errores también visibles)
            hilo_err = threading.Thread(
                target=leer_salida,
                args=(srv["nombre"], ROJO, proceso.stderr, "ERR"),
                daemon=True
            )
            hilo_err.start()

            procesos.append({
                "nombre": srv["nombre"],
                "color": srv["color"],
                "proceso": proceso
            })

            log(srv["nombre"], srv["color"], f"✅ PID {proceso.pid} — listo")

        except Exception as e:
            log(srv["nombre"], ROJO, f"❌ Error al iniciar: {e}")

    print(f"\n{BOLD}{'─'*50}", flush=True)
    print(f"✅  {len(procesos)}/4 servidor(es) activos.")
    print(f"🛑  Presiona Ctrl+C para detener todos.")
    print(f"{'─'*50}{RESET}\n", flush=True)


def monitorear():
    """Mantiene el script vivo y vigila que los procesos no mueran."""
    try:
        while True:
            time.sleep(2)
            for srv in procesos:
                codigo = srv["proceso"].poll()
                if codigo is not None:
                    log(srv["nombre"], ROJO,
                        f"⚠️  Proceso terminó inesperadamente (código: {codigo}). "
                        f"Revisa el log de errores arriba.")
    except KeyboardInterrupt:
        detener_todos()


def detener_todos():
    """Termina todos los subprocesos limpiamente."""
    print(f"\n{BOLD}🛑  Deteniendo todos los servidores JARVIS...{RESET}", flush=True)
    for srv in procesos:
        try:
            srv["proceso"].terminate()
            srv["proceso"].wait(timeout=5)
            log(srv["nombre"], srv["color"], "Detenido ✓")
        except subprocess.TimeoutExpired:
            srv["proceso"].kill()
            log(srv["nombre"], ROJO, "Forzado a cerrar (kill)")
        except Exception as e:
            log(srv["nombre"], ROJO, f"Error al detener: {e}")
    print(f"\n{BOLD}👋  JARVIS offline.{RESET}\n", flush=True)
    sys.exit(0)


# ─── Manejo de señales (Ctrl+C en Windows/Linux) ─────────────────────────────
signal.signal(signal.SIGINT, lambda s, f: detener_todos())
if hasattr(signal, "SIGTERM"):
    signal.signal(signal.SIGTERM, lambda s, f: detener_todos())


# ─── Main ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════╗
║          🤖  JARVIS  MCP             ║
║     Sistema de Asistente de Voz      ║
╚══════════════════════════════════════╝{RESET}

  Directorio base : {BASE_DIR}
  Python          : {sys.executable}
  Servidores      : {len(SERVIDORES)}
""", flush=True)

    iniciar_servidores()
    monitorear()
