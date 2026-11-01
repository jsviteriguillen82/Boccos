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


def test_coexistence_echo_pauses_bot(env, monkeypatch):
    from bot.whatsapp import extract_echoes
    payload = {"entry": [{"changes": [{"field": "smb_message_echoes", "value": {
        "message_echoes": [{"id": "e1", "from": "593987843771", "to": "333",
                            "type": "text", "text": {"body": "Hola, te atiendo yo"}}]}}]}]}
    echoes = extract_echoes(payload)
    assert echoes == [{"id": "e1", "to": "333", "text": "Hola, te atiendo yo"}]
    env.assistant.record_human_reply("333", echoes[0]["text"])
    monkeypatch.setattr(env.assistant.client.beta.messages, "create",
                        lambda **kw: pytest.fail("el bot no debe responder"))
    assert env.assistant.reply("333", "Luis", "Gracias") is None


def test_pause_expires(env, monkeypatch):
    import time
    env.store.save_conversation("444", [], human_takeover=True)
    assert env.store.load_conversation("444")[1] is True
    # Mensajes del cliente durante la pausa no la alargan
    env.store.save_conversation("444", [{"role": "user", "content": "x"}], human_takeover=None)
    real = time.time
    monkeypatch.setattr(time, "time", lambda: real() + env.config.HUMAN_PAUSE_HOURS * 3600 + 5)
    monkeypatch.setattr(env.config, "CONVERSATION_TTL_HOURS", 1000)
    assert env.store.load_conversation("444")[1] is False
