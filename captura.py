"""Workflow 1 · Captura: llegeix els feeds, la IA puntua i crea les notícies noves a Notion."""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from common import gemini_json, norm, notion_create, notion_query, rich, txt
from config import ESTATALS, FEEDS, MITJANS, MUNICIPIS, TEMES

ARA = datetime.now(timezone.utc)

PROMPT = """Eres el editor de Valdeorras Hoxe, un medio de noticias locales de la comarca de Valdeorras (Ourense, Galicia).
Analiza esta noticia y responde SOLO con un JSON con estas claves:
- relevante: true si trata de la comarca de Valdeorras (O Barco, A Rúa, O Bolo, Carballeda, Larouco, Petín, Rubiá, A Veiga, Vilamartín) o de sus vecinos; si no, false.
- municipi: uno de {mun}
- tema: uno de {tem}
- resum: dos frases en catalán, reescritas, sin copiar.
- puntuacio: entero 0-5 según el interés para Instagram de la gente de Valdeorras (0 si no es relevante). Sube si es útil, cercana, emotiva o si la publica un diario estatal.

MEDIO: {mitja}
TITULAR: {titol}
TEXTO: {extracte}"""


def mitja_de(font, link):
    pista = f"{font} {link}".lower()
    for k, v in MITJANS:
        if k in pista:
            return v
    if any(e in font.lower() for e in ESTATALS):
        return "Estatal"
    return "Altres"


def main():
    recents = notion_query({"page_size": 100, "filter": {"timestamp": "created_time", "created_time": {
        "on_or_after": (ARA - timedelta(days=3)).isoformat()}}})
    ja_links = {txt(p, "Enllaç") for p in recents}
    ja_titols = {norm(txt(p, "Títol")) for p in recents}

    noves, vistos = [], set()
    for url in FEEDS:
        try:
            raw = requests.get(url, timeout=25, headers={"User-Agent": "Mozilla/5.0 (ValdeorrasHoxe bot)"}).content
            feed = feedparser.parse(raw)
        except Exception as e:
            print("Feed fallat:", url, e)
            continue
        for e in feed.entries:
            titol, link = (e.get("title") or "").strip(), e.get("link") or ""
            if not titol or not link:
                continue
            font = ""
            if "news.google.com" in link:
                font = (e.get("source") or {}).get("title", "")
                m = re.match(r"^(.*) - ([^-]+)$", titol)
                if m:
                    titol, font = m.group(1).strip(), font or m.group(2).strip()
            t = e.get("published_parsed") or e.get("updated_parsed")
            data = datetime(*t[:6], tzinfo=timezone.utc) if t else ARA
            if ARA - data > timedelta(hours=24):
                continue
            clau = norm(titol)
            if clau in vistos or clau in ja_titols or link in ja_links:
                continue
            vistos.add(clau)
            extracte = re.sub(r"<[^>]+>", " ", e.get("summary", ""))[:600]
            noves.append(dict(titol=titol, link=link, mitja=mitja_de(font, link), data=data, extracte=extracte))
    print(f"{len(noves)} notícies noves per analitzar")

    creades = 0
    for n in noves:
        try:
            ia = gemini_json(PROMPT.format(mun=MUNICIPIS, tem=TEMES, **n))
        except Exception as e:
            print("IA fallada:", e)
            ia = {"relevante": True, "puntuacio": 1, "resum": "(La IA no ha respost)"}
        punts = int(ia.get("puntuacio") or 0)
        if ia.get("relevante") is False or punts == 0:
            continue
        props = {
            "Títol": {"title": [{"text": {"content": n["titol"][:200]}}]},
            "Enllaç": {"url": n["link"]},
            "Mitjà": {"select": {"name": n["mitja"]}},
            "Data": {"date": {"start": n["data"].isoformat()}},
            "Resum": rich(ia.get("resum")),
            "Puntuació": {"number": punts},
            "Estat": {"select": {"name": "Nova"}},
        }
        if ia.get("municipi") in MUNICIPIS:
            props["Municipi"] = {"select": {"name": ia["municipi"]}}
        if ia.get("tema") in TEMES:
            props["Tema"] = {"select": {"name": ia["tema"]}}
        notion_create(props)
        creades += 1
        time.sleep(7)  # límit gratuït de Gemini
    print(f"{creades} notícies creades a Notion")


if __name__ == "__main__":
    main()
