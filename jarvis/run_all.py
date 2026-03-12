Utiiza @jarvis para Eres un experto en arquitectura de software y Model Context Protocol (MCP).

Necesito construir un sistema de asistente de voz conversacional llamado JARVIS, 
compuesto por 4 servidores MCP independientes en Python. Cada uno cumple un rol 
específico. Genera la estructura completa de carpetas y archivos para los 4 servidores.

## ARQUITECTURA GENERAL
Usuario habla → [voice-listener] → texto → Claude API → respuesta → [voice-jarvis] → audio
                                              ↑
                               [jarvis-skills] + [jarvis-memory]

---

## SERVIDOR 1: voice-jarvis (Text-to-Speech)
- Nombre MCP: voice-jarvis
- Tool: say(texto: str)
- Usa ElevenLabs API con voz configurable (default: "Adam")
- Lee ELEVENLABS_API_KEY desde .env
- Ya existe como referencia, solo necesita documentación y estructura limpia

---

## SERVIDOR 2: voice-listener (Speech-to-Text)
- Nombre MCP: voice-listener
- Tool: listen() → devuelve el texto transcrito
- Graba audio desde el micrófono del sistema
- Detecta silencio automáticamente para cortar la grabación
- Usa faster-whisper (local, sin costo) para transcribir
- Soporte para español e inglés (configurable en .env con WHISPER_LANGUAGE)
- Dependencias: faster-whisper, pyaudio, sounddevice, numpy

---

## SERVIDOR 3: jarvis-skills (Gestión de Skills / System Prompts)
- Nombre MCP: jarvis-skills
- Tools:
  - save_skill(name: str, system_prompt: str, description: str) → guarda en skills.json
  - get_skill(name: str) → devuelve el system prompt de esa skill
  - list_skills() → lista todas las skills disponibles
  - delete_skill(name: str) → elimina una skill
- Persiste en archivo local skills.json
- Una skill define: nombre, descripción, system_prompt, fecha de creación

---

## SERVIDOR 4: jarvis-memory (Datasets / Conocimiento)
- Nombre MCP: jarvis-memory
- Tools:
  - save_dataset(name: str, content: str, tags: list[str]) → guarda en datasets/
  - get_dataset(name: str) → devuelve el contenido
  - search_datasets(query: str) → búsqueda simple por tags o nombre
  - list_datasets() → lista todos los datasets disponibles
  - delete_dataset(name: str) → elimina un dataset
- Cada dataset se guarda como archivo .json en carpeta datasets/
- Útil para alimentar contexto a Claude (RAG básico)

---

## ESTRUCTURA DE CARPETAS ESPERADA

jarvis/
├── voice-jarvis/
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
├── voice-listener/
│   ├── server.py
│   ├── requirements.txt
│   └── .env.example
├── jarvis-skills/
│   ├── server.py
│   ├── skills.json
│   ├── requirements.txt
│   └── .env.example
├── jarvis-memory/
│   ├── server.py
│   ├── datasets/
│   ├── requirements.txt
│   └── .env.example
├── claude_desktop_config.json   ← configuración final para conectar los 4 MCPs
└── README.md

---

## REQUISITOS TÉCNICOS PARA TODOS LOS SERVIDORES
- Usar el SDK oficial de MCP para Python: mcp
- Cada server.py debe poder ejecutarse con: python server.py
- Manejo de errores con mensajes claros
- Variables de configuración en .env con python-dotenv
- Código comentado en español

## OUTPUT ESPERADO
Genera todos los archivos completos y funcionales, listos para ejecutar.
Incluye el claude_desktop_config.json final con los 4 servidores configurados.