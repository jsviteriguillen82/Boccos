# BOCCOS — Asistente de WhatsApp (ventas y soporte)

Bot que atiende el WhatsApp Business de BOCCOS usando Claude: responde preguntas, recomienda productos, registra clientes interesados (leads) y pasa a una persona los casos que no puede resolver.

## Qué hace
- **Ventas**: responde con el catálogo, precios y promociones de `knowledge/boccos.md` y registra leads.
- **Soporte**: envíos, cambios, devoluciones y preguntas frecuentes según tus políticas.
- **Escalamiento a humano**: ante reclamos, pagos, consultas de pedidos o datos que no tiene, te avisa por WhatsApp con un resumen y deja de responder a ese cliente hasta que lo devuelvas al bot.
- **No inventa**: solo usa lo que está en la base de conocimiento.

## Cómo intervienes tú
- **Con coexistencia (recomendado):** respondes al cliente desde la app WhatsApp Business del 098 784 3771 y el bot se aparta solo.
- **Con un segundo número (`OWNER_PHONE`, opcional):** recibes avisos y puedes usar estos comandos:
| Comando | Acción |
|---|---|
| `/r 5939XXXXXXXX Hola, ya revisé tu pedido…` | Responder al cliente como BOCCOS |
| `/humano 5939XXXXXXXX` | Tomar la conversación (el bot se calla) |
| `/bot 5939XXXXXXXX` | Devolver la conversación al bot |

## Puesta en marcha
1. **Llena `knowledge/boccos.md`** con la información real de BOCCOS (lo más importante).
2. **WhatsApp Cloud API** (developers.facebook.com → crea una app tipo *Business* → producto *WhatsApp*):
   - Copia el *Phone number ID* y genera un *token permanente* (usuario del sistema en Business Manager).
   - Copia el *App Secret* (Configuración → Básica).
   - Número del bot: **+593 98 784 3771** (el WhatsApp oficial de BOCCOS).
   - **Recomendado: conéctalo en modo _coexistencia_** (en el registro, elige conectar un número que ya usa la app WhatsApp Business). Así el número sigue funcionando en el celular: ves todos los chats y puedes responder desde la app. Suscribe el webhook también al campo `smb_message_echoes`.
   - Cuando alguien del equipo responde desde la app, el bot se calla con ese cliente durante `HUMAN_PAUSE_HOURS` (12 h por defecto) y luego vuelve a atender.
   - `OWNER_PHONE` es opcional y debe ser **otro** número: el bot no puede enviarse avisos a sí mismo. Con coexistencia, los casos escalados los ves directamente en la app.
3. **Claude**: crea una API key en platform.claude.com.
4. Copia `.env.example` a `.env` y completa los valores.
5. Ejecuta:
   ```bash
   pip install -r requirements.txt
   set -a; source .env; set +a
   uvicorn bot.app:app --host 0.0.0.0 --port 8000
   ```
6. Publica el servidor con HTTPS (Render, Railway, Fly.io, un VPS…) y en Meta configura el webhook:
   URL `https://TU-DOMINIO/webhook`, *Verify token* = `WHATSAPP_VERIFY_TOKEN`, y suscríbete al campo `messages`.

> WhatsApp solo permite mensajes libres dentro de las 24 h desde el último mensaje del destinatario. Para recibir los avisos de escalamiento, escríbele al número del bot desde `OWNER_PHONE` al menos una vez al día (o configura una plantilla aprobada).

## Datos
Todo se guarda en SQLite (`boccos.db`): conversaciones, `leads` y `escalations`.
```bash
sqlite3 boccos.db "select datetime(created_at,'unixepoch'), phone, nombre, interes, detalles from leads"
```

## Tests
```bash
pip install pytest && python -m pytest -q
```

## Notas técnicas
- Modelo: `claude-opus-5-5` con esfuerzo `low` (rápido para chat); configurable con `CLAUDE_MODEL` / `CLAUDE_EFFORT`.
- Tiene activado el *fallback* del lado del servidor (`fallbacks: "default"`): si el modelo rechaza una solicitud, la API la reintenta con otro modelo.
- Las conversaciones se reinician tras 24 h sin mensajes (`CONVERSATION_TTL_HOURS`).
- Audios, imágenes y stickers todavía no se interpretan; el bot avisa que no puede verlos.
