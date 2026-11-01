"""Configuración leída desde variables de entorno."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# WhatsApp Cloud API (Meta)
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")
GRAPH_API_VERSION = os.environ.get("GRAPH_API_VERSION", "v21.0")

# Opcional: otro número (no el del bot) que recibe avisos de escalamiento y acepta
# comandos /r /humano /bot. Formato internacional sin +. Con coexistencia no hace falta.
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")

# Claude
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = os.environ.get("CLAUDE_EFFORT", "low")

# Persistencia
DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "boccos.db"))
KNOWLEDGE_PATH = os.environ.get("KNOWLEDGE_PATH", str(BASE_DIR / "knowledge" / "boccos.md"))

# Horas que el bot se queda callado con un cliente después de que una persona
# le responde desde la app de WhatsApp Business (o tras escalar).
HUMAN_PAUSE_HOURS = float(os.environ.get("HUMAN_PAUSE_HOURS", "12"))

# Tras estas horas sin mensajes se empieza una conversación nueva
CONVERSATION_TTL_HOURS = float(os.environ.get("CONVERSATION_TTL_HOURS", "24"))
