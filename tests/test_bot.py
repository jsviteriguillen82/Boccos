import hashlib, hmac, json
from types import SimpleNamespace

import pytest


@pytest.fixture
def env(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test")
    from bot import config
    monkeypatch.setattr(config, "DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setattr(config, "OWNER_PHONE", "111")
    from bot import store, assistant, whatsapp
    store.init_db()
    sent = []
    monkeypatch.setattr(whatsapp, "send_text", lambda to, body: sent.append((to, body)))
    return SimpleNamespace(store=store, assistant=assistant, whatsapp=whatsapp, sent=sent, config=config)


def _block(**kw):
    return SimpleNamespace(**kw, model_dump=lambda **_: dict(kw))


def _resp(stop, *blocks):
    return SimpleNamespace(stop_reason=stop, content=list(blocks))


def test_signature(env, monkeypatch):
    monkeypatch.setattr(env.config, "WHATSAPP_APP_SECRET", "s")
    body = b'{"a":1}'
    sig = "sha256=" + hmac.new(b"s", body, hashlib.sha256).hexdigest()
    assert env.whatsapp.verify_signature(body, sig)
    assert not env.whatsapp.verify_signature(body, "sha256=bad")


def test_extract_messages():
    from bot.whatsapp import extract_messages
    payload = {"entry": [{"changes": [{"value": {
        "contacts": [{"wa_id": "222", "profile": {"name": "Ana"}}],
        "messages": [{"id": "m1", "from": "222", "type": "text", "text": {"body": "Hola"}}]}}]}]}
    assert extract_messages(payload) == [{"id": "m1", "from": "222", "name": "Ana", "text": "Hola"}]


def test_reply_with_escalation(env, monkeypatch):
    calls = iter([
        _resp("tool_use", _block(type="tool_use", id="t1", name="escalar_a_humano",
                                 input={"motivo": "reclamo", "resumen": "Pedido llegó roto"})),
        _resp("end_turn", _block(type="text", text="Te escribirá alguien del equipo.")),
    ])
    monkeypatch.setattr(env.assistant.client.beta.messages, "create", lambda **kw: next(calls))
    out = env.assistant.reply("222", "Ana", "Mi pedido llegó roto")
    assert out == "Te escribirá alguien del equipo."
    assert env.sent and env.sent[0][0] == "111"
    # Con la conversación escalada, el bot ya no responde
    assert env.assistant.reply("222", "Ana", "¿Hola?") is None
    env.assistant.handle_owner_command("/bot 222")
    _, takeover = env.store.load_conversation("222")
    assert takeover is False


def test_duplicate_detection(env):
    assert env.store.already_processed("x") is False
    assert env.store.already_processed("x") is True
