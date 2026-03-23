"""
JARVIS - jarvis-skills (Gestión de Skills / System Prompts)
Servidor MCP para guardar, recuperar y administrar skills (system prompts).
"""

from mcp.server.fastmcp import FastMCP
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Cambiar al directorio del script para rutas relativas
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Cargar variables de entorno
load_dotenv()

mcp = FastMCP("jarvis-skills")

# Ruta del archivo de skills
SKILLS_FILE = os.getenv("SKILLS_FILE", os.path.join(os.path.dirname(os.path.abspath(__file__)), "skills.json"))


def cargar_skills() -> dict:
    """Carga el archivo skills.json, lo crea si no existe."""
    if not os.path.exists(SKILLS_FILE):
        with open(SKILLS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(SKILLS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_skills(skills: dict) -> None:
    """Persiste el diccionario de skills en disco."""
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        json.dump(skills, f, ensure_ascii=False, indent=2)


@mcp.tool(name="save_skill", description="Guarda una skill (system prompt) con nombre y descripción")
def save_skill(name: str, system_prompt: str, description: str) -> str:
    """
    Guarda una nueva skill o actualiza una existente.
    - name: identificador único de la skill
    - system_prompt: instrucciones de comportamiento para Claude
    - description: descripción corta de para qué sirve esta skill
    """
    try:
        skills = cargar_skills()
        skills[name] = {
            "name": name,
            "description": description,
            "system_prompt": system_prompt,
            "created_at": skills.get(name, {}).get("created_at", datetime.now().isoformat()),
            "updated_at": datetime.now().isoformat()
        }
        guardar_skills(skills)
        return f"Skill '{name}' guardada correctamente."
    except Exception as e:
        return f"Error al guardar skill: {str(e)}"


@mcp.tool(name="get_skill", description="Recupera el system prompt de una skill por su nombre")
def get_skill(name: str) -> str:
    """
    Devuelve el system_prompt completo de la skill solicitada.
    """
    try:
        skills = cargar_skills()
        if name not in skills:
            return f"Error: Skill '{name}' no encontrada."
        skill = skills[name]
        return f"[Skill: {name}]\nDescripción: {skill['description']}\n\nSystem Prompt:\n{skill['system_prompt']}"
    except Exception as e:
        return f"Error al obtener skill: {str(e)}"


@mcp.tool(name="list_skills", description="Lista todas las skills disponibles con su descripción")
def list_skills() -> str:
    """
    Devuelve un resumen de todas las skills guardadas.
    """
    try:
        skills = cargar_skills()
        if not skills:
            return "No hay skills guardadas todavía."
        lines = ["Skills disponibles:\n"]
        for name, skill in skills.items():
            lines.append(f"• {name}: {skill['description']} (actualizada: {skill['updated_at'][:10]})")
        return "\n".join(lines)
    except Exception as e:
        return f"Error al listar skills: {str(e)}"


@mcp.tool(name="delete_skill", description="Elimina una skill por su nombre")
def delete_skill(name: str) -> str:
    """
    Elimina permanentemente una skill del archivo.
    """
    try:
        skills = cargar_skills()
        if name not in skills:
            return f"Error: Skill '{name}' no encontrada."
        del skills[name]
        guardar_skills(skills)
        return f"Skill '{name}' eliminada correctamente."
    except Exception as e:
        return f"Error al eliminar skill: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
