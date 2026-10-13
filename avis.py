"""Workflow 2 · Avís del matí: envia per Telegram el top 5 de notícies noves."""
from datetime import datetime, timedelta, timezone

from common import notion_query, tg_text, txt
from config import NOTION_URL


def main():
    des_de = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()
    r = notion_query({"page_size": 5,
                      "filter": {"and": [{"property": "Estat", "select": {"equals": "Nova"}},
                                         {"timestamp": "created_time", "created_time": {"on_or_after": des_de}}]},
                      "sorts": [{"property": "Puntuació", "direction": "descending"}]})
    if not r:
        tg_text("☀️ Bo día! Hoxe non entrou ningunha noticia nova de Valdeorras.")
        return
    linies = []
    for i, p in enumerate(r, 1):
        estrelles = "⭐" * int(txt(p, "Puntuació") or 0)
        linies.append(f"{i}. {txt(p, 'Títol')}\n   {txt(p, 'Mitjà')} · {estrelles}")
    tg_text("☀️ Valdeorras Hoxe · top do día\n\n" + "\n\n".join(linies) + f"\n\nEscolle no taboleiro: {NOTION_URL}")


if __name__ == "__main__":
    main()
