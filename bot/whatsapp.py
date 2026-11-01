"""Cliente mínimo de la WhatsApp Cloud API."""
import hashlib
import hmac
import logging

import httpx

from . import config

log = logging.getLogger(__name__)


def verify_signature(raw_body: bytes, signature_header: str | None) -> bool:
    """Valida X-Hub-Signature-256 con el App Secret de Meta."""
    if not config.WHATSAPP_APP_SECRET:
        log.warning("WHATSAPP_APP_SECRET no configurado: no se valida la firma")
        return True
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(
        config.WHATSAPP_APP_SECRET.encode(), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header.removeprefix("sha256="))


def send_text(to: str, body: str) -> None:
    url = (
        f"https://graph.facebook.com/{config.GRAPH_API_VERSION}/"
        f"{config.WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    # WhatsApp limita el texto a 4096 caracteres
    for i in range(0, len(body), 4000):
        resp = httpx.post(
            url,
            headers={"Authorization": f"Bearer {config.WHATSAPP_TOKEN}"},
            json={
                "messaging_product": "whatsapp",
                "to": to,
                "type": "text",
                "text": {"body": body[i : i + 4000]},
            },
            timeout=20,
        )
        if resp.status_code >= 400:
            log.error("Error enviando WhatsApp a %s: %s %s", to, resp.status_code, resp.text)


def extract_messages(payload: dict) -> list[dict]:
    """Extrae los mensajes entrantes del webhook como dicts simples."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            names = {
                c.get("wa_id"): c.get("profile", {}).get("name", "")
                for c in value.get("contacts", [])
            }
            for msg in value.get("messages", []):
                mtype = msg.get("type")
                if mtype == "text":
                    text = msg["text"].get("body", "")
                elif mtype == "button":
                    text = msg["button"].get("text", "")
                elif mtype == "interactive":
                    inter = msg["interactive"]
                    text = (inter.get("button_reply") or inter.get("list_reply") or {}).get(
                        "title", ""
                    )
                else:
                    # Audio, imagen, sticker, ubicación, etc.
                    text = f"[El cliente envió un mensaje de tipo '{mtype}' que no puedo ver]"
                out.append(
                    {
                        "id": msg.get("id"),
                        "from": msg.get("from"),
                        "name": names.get(msg.get("from"), ""),
                        "text": text,
                    }
                )
    return out


def extract_echoes(payload: dict) -> list[dict]:
    """Mensajes que el equipo envió desde la app de WhatsApp Business (coexistencia,
    webhook `smb_message_echoes`). Devuelve [{id, to, text}]."""
    out = []
    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "smb_message_echoes":
                continue
            for msg in change.get("value", {}).get("message_echoes", []):
                if msg.get("type") == "text":
                    text = msg.get("text", {}).get("body", "")
                else:
                    text = f"[envió un mensaje de tipo '{msg.get('type')}']"
                out.append({"id": msg.get("id"), "to": msg.get("to"), "text": text})
    return out
