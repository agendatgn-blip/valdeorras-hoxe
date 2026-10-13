"""Workflow 1 · Captura: llegeix els feeds, la IA puntua i crea les notícies noves a Notion."""
import re
import time
from datetime import datetime, timedelta, timezone

import feedparser
import requests

from common import GeminiAturat, gemini_json, norm, notion_create, notion_query, rich, tg_text, txt
from config import ESTATALS, FEEDS, MITJANS, MUNICIPIS, TEMES

ARA = datetime.now(timezone.utc)
INICI = time.time()
MAX_NOTICIES = 20      # màxim de notícies que passen per la IA a cada execució
PAUSA_IA = 7           # segons entre crides a Gemini (límit gratuït ~10/min)
TEMPS_MAX = 12 * 60    # si passem de 12 min, plegar (el workflow talla als 15)

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

    noves.sort(key=lambda n: n["data"], reverse=True)  # primer les més recents
    if len(noves) > MAX_NOTICIES:
        print(f"Només analitzo les {MAX_NOTICIES} més recents")
        noves = noves[:MAX_NOTICIES]

    creades = 0
    for i, n in enumerate(noves, 1):
        if time.time() - INICI > TEMPS_MAX:
            print("Temps màxim superat, plego. La resta, a la pròxima execució.")
            break
        print(f"[{i}/{len(noves)}] {n['titol'][:80]}")
        try:
            ia = gemini_json(PROMPT.format(mun=MUNICIPIS, tem=TEMES, **n))
        except GeminiAturat as e:
            print("Gemini aturat, plego:", e)
            tg_text(f"⚠️ Captura: Gemini no respon ({str(e)[:150]}). Analitzades {i - 1}/{len(noves)}, creades {creades}.")
            break
        except Exception as e:
            print("IA fallada, la salto:", e)  # no creem fitxes buides a Notion
            continue
        time.sleep(PAUSA_IA)  # límit gratuït de Gemini (també quan la notícia es descarta)
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
    print(f"{creades} notícies creades a Notion")


if __name__ == "__main__":
    main()
