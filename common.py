"""Connexions compartides: Notion, Gemini i Telegram."""
import json
import os
import re
import time

import requests

from config import GEMINI_MODEL_DEFAULT, NOTION_DB

NOTION_H = {
    "Authorization": f"Bearer {os.environ.get('NOTION_TOKEN', '')}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json",
}


# ---------- Notion ----------
def notion_query(body):
    out, cursor = [], None
    while True:
        b = dict(body)
        if cursor:
            b["start_cursor"] = cursor
        r = requests.post(f"https://api.notion.com/v1/databases/{NOTION_DB}/query",
                          headers=NOTION_H, json=b, timeout=30)
        r.raise_for_status()
        d = r.json()
        out += d["results"]
        if not d.get("has_more") or b.get("page_size", 100) < 100:
            return out
        cursor = d["next_cursor"]


def notion_create(props):
    r = requests.post("https://api.notion.com/v1/pages", headers=NOTION_H,
                      json={"parent": {"database_id": NOTION_DB}, "properties": props}, timeout=30)
    r.raise_for_status()
    time.sleep(0.4)


def notion_update(page_id, props):
    r = requests.patch(f"https://api.notion.com/v1/pages/{page_id}", headers=NOTION_H,
                       json={"properties": props}, timeout=30)
    r.raise_for_status()


def txt(page, name):
    p = page["properties"].get(name, {})
    t = p.get("type")
    if t in ("title", "rich_text"):
        return "".join(x["plain_text"] for x in p[t])
    if t == "select":
        return (p["select"] or {}).get("name", "")
    if t == "url":
        return p["url"] or ""
    if t == "number":
        return p["number"]
    return ""


def rich(s):
    s = str(s or "")
    return {"rich_text": [{"text": {"content": s[i:i + 1900]}} for i in range(0, min(len(s), 5700), 1900)]}


# ---------- Gemini ----------
class GeminiAturat(Exception):
    """Gemini no pot respondre en aquesta execució (sense quota, model inexistent, clau dolenta...)."""


class QuotaEsgotada(GeminiAturat):
    """Gemini ha dit prou (429)."""


def gemini_json(prompt, tries=3):
    model = os.environ.get("GEMINI_MODEL") or GEMINI_MODEL_DEFAULT
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    body = {"contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}}
    for i in range(tries):
        r = requests.post(url, headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"]}, json=body, timeout=60)
        if r.status_code == 429:
            # Límit diari esgotat -> plegar ja. Límit per minut -> esperar 1 cop i reintentar.
            if "PerDay" in r.text or i > 0:
                raise QuotaEsgotada(r.text[:300])
            print("Gemini 429 (límit per minut), espero 30 s...")
            time.sleep(30)
            continue
        if r.status_code >= 500:
            print(f"Gemini {r.status_code}, reintento...")
            time.sleep(10)
            continue
        if r.status_code in (400, 401, 403, 404):
            raise GeminiAturat(f"{r.status_code} amb el model '{model}': {r.text[:300]}")
        r.raise_for_status()
        text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        text = re.sub(r"```(json)?", "", text).strip()
        return json.loads(text)
    raise RuntimeError("Gemini no respon")


# ---------- Telegram ----------
def _tg(method, **kw):
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        print("(sense Telegram)", kw.get("data", {}).get("text", "")[:200])
        return
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", timeout=60, **kw)
    if not r.ok:
        print("Telegram error:", r.text)


def tg_text(text):
    _tg("sendMessage", data={"chat_id": os.environ.get("TELEGRAM_CHAT_ID"), "text": text,
                             "disable_web_page_preview": True})


def tg_photo(path, caption=""):
    with open(path, "rb") as f:
        _tg("sendPhoto", data={"chat_id": os.environ.get("TELEGRAM_CHAT_ID"), "caption": caption[:1000]},
            files={"photo": f})


# ---------- Utilitats ----------
def norm(t):
    import unicodedata
    t = unicodedata.normalize("NFD", (t or "").lower())
    t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", t)).strip()


def article_text(url, max_chars=4000):
    """Intenta treure el text de la notícia original (paràgrafs <p>)."""
    if "news.google.com" in url:
        return ""
    try:
        r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (ValdeorrasHoxe bot)"})
        html = r.text
    except Exception:
        return ""
    ps = re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S | re.I)
    clean = [re.sub(r"<[^>]+>", "", p).strip() for p in ps]
    clean = [re.sub(r"\s+", " ", p) for p in clean if len(p) > 60]
    return " ".join(clean)[:max_chars]
