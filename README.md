# MCP Claude Desktop

> ⚠️ **Proyecto histórico / archivado**
> Este proyecto fue construido en una época donde los MCPs (Model Context Protocol) no tenían integración nativa con Claude Desktop. Hoy el SDK oficial de Anthropic cubre todo esto de forma mucho más limpia. Se mantiene como referencia de lo que se hacía antes.

---

## ¿Qué era esto?

Un servidor **FastAPI** que actuaba como puente entre Claude Desktop y herramientas personalizadas, cuando el ecosistema MCP estaba apenas empezando y no había integraciones nativas.

Fue construido con Claude para resolver un problema real en el momento: poder darle a Claude acceso a filesystem local, búsqueda web (Brave), caché y herramientas custom, sin esperar a que el tooling oficial madurara.

### Lo que hacía

- Exponía una **API REST** que Claude Desktop consumía como si fuera un servidor MCP
- **Filesystem**: leer, escribir y listar archivos locales
- **Brave Search**: búsquedas web con análisis opcional via Claude
- **Caché con Redis**: evitar llamadas redundantes a la API de Anthropic
- **Auth con JWT**: proteger los endpoints locales
- **Plugins**: sistema de hooks para extender funcionalidad
- **Métricas con Prometheus**: monitoreo de uso y rendimiento
- **Logging estructurado**: logs en JSON y Markdown

### Stack

- Python 3.11+
- FastAPI + Uvicorn
- Redis (caché)
- Anthropic SDK (`anthropic==0.19.1`)
- Pydantic v2
- Pytest

---

## ¿Por qué está archivado?

Desde 2024-2025 el protocolo MCP es nativo en Claude Desktop y existe el [SDK oficial de MCP](https://github.com/modelcontextprotocol/python-sdk) de Anthropic. Lo que este proyecto hacía con ~2000 líneas de FastAPI + Redis + JWT, hoy se hace en ~100 líneas con el SDK oficial, sin servidor HTTP, sin Docker, sin Redis.

Si buscas construir un MCP server hoy, ve directamente a:
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Documentación MCP oficial](https://modelcontextprotocol.io)

---

## Estructura (para referencia histórica)

```
app/
├── api/endpoints/     # Endpoints: claude, filesystem, search, tools, mcp...
├── core/              # Config, security, claude_client, mcp_config
├── services/          # claude_service, filesystem_service, brave_search, mcp_service
├── schemas/           # Modelos Pydantic
├── middleware/        # Auth JWT, rate limiting
└── main.py
tests/                 # Unit, integration, concurrency, performance
run.py
```

---

## Instalación (solo si quieres explorarlo)

```bash
python -m venv .venv
.venv\Scripts\activate       # Windows
pip install -r requirements.txt
cp .env.example .env         # Configurar variables
python run.py
```

Requería Redis corriendo localmente y una API key de Anthropic + Brave Search.

---

## Contexto

Construido en Querétaro, México, durante los primeros meses del ecosistema MCP (early 2024), cuando los únicos servidores MCP disponibles eran experimentales y Claude Desktop apenas comenzaba a soportar el protocolo. Este proyecto fue una solución pragmática mientras el tooling maduraba.

---

## Licencia

MIT — úsalo como referencia si te es útil.
