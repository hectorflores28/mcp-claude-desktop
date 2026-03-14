###
| Jarvis Voice Listener pendiente AUN (VOICE_JARVIS YA)(JARVIS_SKILL UNA BASE)(JARVIS_MEMORY_ERROR)"
###

# 🤖 JARVIS - Sistema de Asistente de Voz MCP

Sistema conversacional de voz a voz compuesto por 4 servidores MCP independientes.

## Arquitectura

```
🎤 Tú hablas → [voice-listener] → texto
                                    ↓
                    [jarvis-skills] + [jarvis-memory]
                                    ↓
                              Claude API
                                    ↓
              [voice-jarvis] → 🔊 ElevenLabs
```

## Servidores MCP

| Servidor | Carpeta | Descripción |
|---|---|---|
| `voice-jarvis` | `voice_jarvis/` | Text-to-Speech con ElevenLabs |
| `voice-listener` | `voice_listener/` | Speech-to-Text con Whisper |
| `jarvis-skills` | `jarvis_skill/` | Gestión de system prompts |
| `jarvis-memory` | `jarvis_memory/` | Gestión de datasets/conocimiento |

---

## Instalación

### 1. voice-jarvis
```bash
cd voice_jarvis
pip install -r requirements.txt
cp .env.example .env
# Edita .env con tu ELEVENLABS_API_KEY
```

### 2. voice-listener
```bash
cd voice_listener
pip install -r requirements.txt
cp .env.example .env
# Ajusta WHISPER_LANGUAGE=es o en
```

### 3. jarvis-skills
```bash
cd jarvis_skill
pip install -r requirements.txt
cp .env.example .env
```

### 4. jarvis-memory
```bash
cd jarvis_memory
pip install -r requirements.txt
cp .env.example .env
```

---

## Configuración Claude Desktop

Copia el contenido de `claude_desktop_config.json` a:
```
C:\Users\hflores\AppData\Local\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Roaming\Claude\claude_desktop_config.json
```

Luego **reinicia Claude Desktop**.

---

## Uso de las tools

### voice-jarvis
```
/say "Hola Héctor, soy JARVIS"
```

### voice-listener
```
/listen  → graba tu voz y devuelve el texto transcrito
```

### jarvis-skills
```
/save_skill name="asistente-mar-del-cabo" description="Asistente del resort" system_prompt="Eres el asistente de Mar del Cabo..."
/get_skill name="asistente-mar-del-cabo"
/list_skills
/delete_skill name="asistente-mar-del-cabo"
```

### jarvis-memory
```
/save_dataset name="tarifas-2025" content="Temporada alta: $200/noche..." tags=["tarifas","resort"]
/get_dataset name="tarifas-2025"
/search_datasets query="tarifas"
/list_datasets
/delete_dataset name="tarifas-2025"
```

---

## Variables de entorno importantes

| Variable | Servidor | Descripción |
|---|---|---|
| `ELEVENLABS_API_KEY` | voice-jarvis | API key de ElevenLabs |
| `ELEVENLABS_VOICE_ID` | voice-jarvis | ID de voz (default: Adam) |
| `WHISPER_LANGUAGE` | voice-listener | Idioma (es/en) |
| `WHISPER_MODEL_SIZE` | voice-listener | tiny/base/small/medium |
| `SILENCE_THRESHOLD` | voice-listener | Sensibilidad del micrófono |
