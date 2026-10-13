# Valdeorras Hoxe · automatización

Recolle as noticias de Valdeorras, puntúaas con IA, gárdaas en Notion e prepara os posts de Instagram en galego.

| Workflow | Cando | Que fai |
|---|---|---|
| 1 · Captura | 7, 14 e 20 h | Le os feeds de `config.py`, a IA puntúa e crea as novas en Notion (Estado "Nova") |
| 2 · Aviso | 8 h | Envía por Telegram o top 5 do día |
| 3 · Produción | cada 15 min | Para cada noticia "Escollida": titular, texto, copy, imaxe → "Per aprovar" + Telegram |

Segredos necesarios (Settings → Secrets and variables → Actions): `NOTION_TOKEN`, `GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.
Variable opcional: `GEMINI_MODEL` (por defecto `gemini-2.5-flash`).

Tipografías Anton e Archivo baixo licenza SIL OFL (ver `fonts/`).
