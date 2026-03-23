from fastapi import APIRouter
from app.api.endpoints.search import router as search_router
from app.api.endpoints.filesystem import router as filesystem_router
from app.api.endpoints.tools import router as tools_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.claude import router as claude_router
from app.api.endpoints.prompts import router as prompts_router
from app.api.endpoints.logs import router as logs_router
from app.api.endpoints.resources import router as resources_router
from app.api.endpoints.mcp import router as mcp_router

router = APIRouter()

router.include_router(search_router)
router.include_router(filesystem_router)
router.include_router(tools_router)
router.include_router(health_router)
router.include_router(claude_router)
router.include_router(prompts_router)
router.include_router(logs_router)
router.include_router(resources_router)
router.include_router(mcp_router)

__all__ = [
    "router",
    "search_router",
    "filesystem_router",
    "tools_router",
    "health_router",
    "claude_router",
    "prompts_router",
    "logs_router",
    "resources_router",
    "mcp_router"
] 