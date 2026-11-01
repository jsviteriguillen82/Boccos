"""Asistente de ventas y soporte de BOCCOS impulsado por Claude."""
import json
import logging
from pathlib import Path

import anthropic

from . import config, store, whatsapp

log = logging.getLogger(__name__)

client = anthropic.Anthropic()

SYSTEM_TEMPLATE = """Eres el asistente oficial de BOCCOS en WhatsApp. Atiendes a clientes en ventas, soporte y preguntas generales, en nombre del equipo de BOCCOS.

Cómo escribir:
- Responde en el idioma del cliente (por defecto, español), con tono cálido, cercano y profesional.
- Mensajes cortos, pensados para WhatsApp: 1 a 4 frases, sin tablas ni encabezados. Usa *negritas* de WhatsApp con moderación y emojis solo si encajan.
- Una pregunta a la vez cuando necesites datos del cliente.

Qué puedes hacer:
- Ventas: entender qué necesita el cliente, recomendar productos del catálogo, dar precios y promociones vigentes y guiarlo hacia la compra. Cuando un cliente muestre intención clara de compra o deje sus datos, usa la herramienta registrar_lead.
- Soporte: resolver dudas sobre pedidos, envíos, cambios, devoluciones y garantías siguiendo las políticas de abajo.

Límites (importantes):
- Usa solo la información de la base de conocimiento de abajo. Si algo no está ahí (un precio, stock, el estado de un pedido concreto, una fecha de entrega), no lo inventes: dilo con naturalidad y escala a una persona.
- Escala con escalar_a_humano cuando el cliente lo pida, esté molesto, haya un reclamo, un pago o reembolso que revisar, un pedido que consultar en el sistema, o cualquier caso que no puedas resolver con la información disponible. Después de escalar, avísale al cliente que una persona del equipo le escribirá pronto (según el horario de atención).
- No prometas descuentos, plazos ni excepciones que no estén en las políticas.
- Nunca pidas datos de tarjeta, contraseñas ni códigos de verificación.

<base_de_conocimiento>
{knowledge}
</base_de_conocimiento>"""

TOOLS = [
    {
        "name": "registrar_lead",
        "description": (
            "Guarda un cliente potencial interesado en comprar para que el equipo de ventas le dé "
            "seguimiento. Úsala cuando el cliente muestre intención de compra o pida una cotización."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre": {"type": "string", "description": "Nombre del cliente, o '' si no lo dio"},
                "interes": {"type": "string", "description": "Producto(s) o servicio de interés"},
                "detalles": {
                    "type": "string",
                    "description": "Cantidades, ciudad, presupuesto, fecha deseada u otros datos útiles",
                },
            },
            "required": ["nombre", "interes", "detalles"],
            "additionalProperties": False,
        },
    },
    {
        "name": "escalar_a_humano",
        "description": (
            "Pasa la conversación a una persona del equipo de BOCCOS y le envía un resumen. "
            "Mientras esté escalada, el bot deja de responder a este cliente."
        ),
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "motivo": {
                    "type": "string",
                    "enum": ["pedido_cliente", "reclamo", "pago_reembolso", "consulta_pedido", "venta_compleja", "sin_informacion", "otro"],
                },
                "resumen": {
                    "type": "string",
                    "description": "Resumen breve de lo que necesita el cliente y lo que ya se le dijo",
                },
            },
            "required": ["motivo", "resumen"],
            "additionalProperties": False,
        },
    },
]


def _system_prompt() -> str:
    path = Path(config.KNOWLEDGE_PATH)
    knowledge = path.read_text(encoding="utf-8") if path.exists() else "(sin información cargada)"
    return SYSTEM_TEMPLATE.format(knowledge=knowledge)


def _run_tool(name: str, args: dict, phone: str, customer_name: str) -> tuple[str, bool]:
    """Ejecuta una herramienta. Devuelve (resultado, escalado)."""
    if name == "registrar_lead":
        store.add_lead(phone, args.get("nombre") or customer_name, args["interes"], args["detalles"])
        return "Lead registrado.", False
    if name == "escalar_a_humano":
        store.add_escalation(phone, args["motivo"], args["resumen"])
        if config.OWNER_PHONE:
            whatsapp.send_text(
                config.OWNER_PHONE,
                f"🔔 *Escalamiento BOCCOS*\nCliente: {customer_name or 'sin nombre'} (+{phone})\n"
                f"Motivo: {args['motivo']}\n{args['resumen']}\n\n"
                f"Responder: /r {phone} <mensaje>\nDevolver al bot: /bot {phone}",
            )
        return "Escalado al equipo. El bot dejará de responder a este cliente.", True
    return f"Herramienta desconocida: {name}", False


def reply(phone: str, customer_name: str, text: str) -> str | None:
    """Procesa un mensaje del cliente y devuelve la respuesta a enviar (o None)."""
    messages, takeover = store.load_conversation(phone)
    messages.append({"role": "user", "content": text})
    if takeover:
        # Una persona está atendiendo: solo guardamos el mensaje.
        store.save_conversation(phone, messages, human_takeover=True)
        return None

    system = _system_prompt()
    escalated = False
    final_text = ""

    for _ in range(5):  # tope de iteraciones de herramientas
        try:
            response = client.beta.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=4000,
                system=system,
                messages=messages,
                tools=TOOLS,
                output_config={"effort": config.CLAUDE_EFFORT},
                cache_control={"type": "ephemeral"},
                betas=["server-side-fallback-2026-07-01"],
                fallbacks="default",
            )
        except anthropic.RateLimitError:
            log.exception("Rate limit de Claude")
            return "Estamos con mucha demanda en este momento 🙏 ¿Me escribes de nuevo en unos minutos?"
        except anthropic.APIStatusError:
            log.exception("Error de la API de Claude")
            return None
        except anthropic.APIConnectionError:
            log.exception("Sin conexión con Claude")
            return None

        # Guardamos el contenido completo (incluye bloques de thinking) para reenviarlo tal cual.
        messages.append(
            {"role": "assistant", "content": [b.model_dump(mode="json", exclude_none=True) for b in response.content]}
        )

        if response.stop_reason == "refusal":
            final_text = "Disculpa, no puedo ayudarte con eso por aquí. ¿Te puedo ayudar con algo más de BOCCOS?"
            break

        texts = [b.text for b in response.content if b.type == "text"]
        tool_uses = [b for b in response.content if b.type == "tool_use"]

        if response.stop_reason != "tool_use" or not tool_uses:
            final_text = "\n".join(t for t in texts if t).strip()
            break

        results = []
        for tu in tool_uses:
            args = tu.input if isinstance(tu.input, dict) else json.loads(tu.input)
            result, did_escalate = _run_tool(tu.name, args, phone, customer_name)
            escalated = escalated or did_escalate
            results.append({"type": "tool_result", "tool_use_id": tu.id, "content": result})
        messages.append({"role": "user", "content": results})

    store.save_conversation(phone, messages, human_takeover=escalated)
    return final_text or None


def handle_owner_command(text: str) -> str:
    """Comandos del dueño desde su WhatsApp (OWNER_PHONE)."""
    parts = text.strip().split(maxsplit=2)
    cmd = parts[0].lower()
    if cmd == "/r" and len(parts) == 3:
        phone, msg = parts[1].lstrip("+"), parts[2]
        whatsapp.send_text(phone, msg)
        messages, _ = store.load_conversation(phone)
        # Se registra como nota para que el bot tenga contexto si retoma la conversación.
        messages.append({"role": "user", "content": f"[Nota interna: el equipo de BOCCOS respondió al cliente: {msg}]"})
        store.save_conversation(phone, messages, human_takeover=True)
        return f"✅ Enviado a +{phone}"
    if cmd == "/bot" and len(parts) >= 2:
        store.set_human_takeover(parts[1].lstrip("+"), False)
        return f"🤖 El bot vuelve a atender a +{parts[1].lstrip('+')}"
    if cmd == "/humano" and len(parts) >= 2:
        phone = parts[1].lstrip("+")
        messages, _ = store.load_conversation(phone)
        store.save_conversation(phone, messages, human_takeover=True)
        return f"🙋 Tomaste la conversación con +{phone}. El bot no le responderá."
    return "Comandos: /r <número> <mensaje> · /humano <número> · /bot <número>"
