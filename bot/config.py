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

# Número del dueño/equipo para escalar conversaciones (formato internacional sin +)
OWNER_PHONE = os.environ.get("OWNER_PHONE", "")

# Claude
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-opus-5-5")
CLAUDE_EFFORT = os.environ.get("CLAUDE_EFFORT", "low")

# Persistencia
DB_PATH = os.environ.get("DB_PATH", str(BASE_DIR / "boccos.db"))
KNOWLEDGE_PATH = os.environ.get("KNOWLEDGE_PATH", str(BASE_DIR / "knowledge" / "boccos.md"))

# Tras estas horas sin mensajes se empieza una conversación nueva
CONVERSATION_TTL_HOURS = float(os.environ.get("CONVERSATION_TTL_HOURS", "24"))
