"""Servidor webhook para WhatsApp Cloud API."""
import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

from . import assistant, config, store, whatsapp

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("boccos")

app = FastAPI(title="BOCCOS WhatsApp Assistant")
store.init_db()


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/webhook")
def verify(request: Request):
    """Verificación del webhook que hace Meta al configurarlo."""
    p = request.query_params
    if p.get("hub.mode") == "subscribe" and p.get("hub.verify_token") == config.WHATSAPP_VERIFY_TOKEN:
        return PlainTextResponse(p.get("hub.challenge", ""))
    raise HTTPException(status_code=403)


def process(msg: dict) -> None:
    try:
        phone, text = msg["from"], msg["text"]
        if config.OWNER_PHONE and phone == config.OWNER_PHONE and text.startswith("/"):
            whatsapp.send_text(phone, assistant.handle_owner_command(text))
            return
        answer = assistant.reply(phone, msg.get("name", ""), text)
        if answer:
            whatsapp.send_text(phone, answer)
    except Exception:
        log.exception("Error procesando mensaje %s", msg.get("id"))


@app.post("/webhook")
async def receive(request: Request, background: BackgroundTasks):
    raw = await request.body()
    if not whatsapp.verify_signature(raw, request.headers.get("X-Hub-Signature-256")):
        raise HTTPException(status_code=401)
    payload = await request.json()
    for msg in whatsapp.extract_messages(payload):
        if msg["id"] and store.already_processed(msg["id"]):
            continue
        background.add_task(process, msg)
    for echo in whatsapp.extract_echoes(payload):
        if echo["to"] and not (echo["id"] and store.already_processed(echo["id"])):
            assistant.record_human_reply(echo["to"], echo["text"])
    # Responder 200 rápido para que Meta no reintente.
    return {"status": "ok"}
