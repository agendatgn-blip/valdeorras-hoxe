"""Workflow 3 · Producció: per a cada notícia "Escollida", la IA escriu titular, text i copy en gallec
(amb SEO, GEO i AEO), es dibuixa la imatge i tot passa a "Per aprovar" i arriba per Telegram."""
import os
from pathlib import Path

from common import article_text, gemini_json, notion_query, notion_update, rich, tg_photo, tg_text, txt
from config import NOM_COMPLET, TEMA_GL
from render import render_post

PROMPT = """Eres redactor de Valdeorras Hoxe, medio dixital de noticias locais da comarca de Valdeorras (Ourense, Galicia).
Escribe SEMPRE en galego normativo (RAG), claro e próximo, tratando de ti. Sen castelanismos. Topónimos oficiais.
NON inventes nada: nin datas, nin cifras, nin nomes que non estean na noticia. Reescribe, non copies frases.

Responde SÓ cun JSON con estas claves:
- titular: titular para a imaxe, máximo 70 caracteres, directo, sen punto final.
- texto: 2-3 frases que contan o esencial. A primeira responde quen, que e onde (AEO).
- lugar: lugar concreto onde pasa, se a noticia o di (ex. "Paseo do Malecón"); se non, "".
- cando: data ou hora do evento SÓ se a noticia a di (ex. "sábado 14 de xuño"); se non, "".
- emoji: un emoji que represente o tema.
- gancho: primeira liña do copy, curta, despois do nome do municipio (ex. "a Feira do Viño cambia de sitio").
- pregunta: unha pregunta curta para que a xente comente.
- hashtags: lista de 3 a 5 hashtags sen espazos; sempre #Valdeorras e o do municipio se existe (#OBarcoDeValdeorras, #ARúa...), e #Ourense.
- alt: texto alternativo da imaxe: "Titular de Valdeorras Hoxe: <titular>, <municipio completo> (Ourense)."

MUNICIPIO: {municipi}
TEMA: {tema}
MEDIO ORIXINAL: {mitja}
TITULAR ORIXINAL: {titol}
RESUMO: {resum}
TEXTO ORIXINAL: {cos}"""


def copy_de(ia, municipi_complet, mitja):
    linia_lloc = ", ".join(x for x in [ia.get("lugar"), f"{municipi_complet} (Ourense)"] if x)
    if ia.get("cando"):
        linia_lloc += f" · 📅 {ia['cando']}"
    tags = " ".join(ia.get("hashtags", [])[:5])
    return (f"{ia.get('emoji', '📰')} {municipi_complet}: {ia.get('gancho', '')}\n\n"
            f"{ia.get('texto', '')}\n\n"
            f"📍 {linia_lloc}\n\n"
            f"{ia.get('pregunta', '')} 👇\n\n"
            f"📰 Fonte: {mitja}\n"
            f"Valdeorras Hoxe · noticias da comarca de Valdeorras\n\n"
            f"{tags}")


def main():
    repo = os.environ.get("GITHUB_REPOSITORY", "USUARI/valdeorras-hoxe")
    pagines = notion_query({"page_size": 10, "filter": {"property": "Estat", "select": {"equals": "Escollida"}}})
    print(f"{len(pagines)} notícies escollides")
    for p in pagines:
        pid = p["id"]
        municipi = txt(p, "Municipi") or "Comarca"
        tema = txt(p, "Tema") or ""
        mitja = txt(p, "Mitjà") or "medio local"
        dades = dict(municipi=municipi, tema=tema, mitja=mitja, titol=txt(p, "Títol"),
                     resum=txt(p, "Resum"), cos=article_text(txt(p, "Enllaç")) or "(non dispoñible)")
        try:
            ia = gemini_json(PROMPT.format(**dades))
        except Exception as e:
            tg_text(f"⚠️ Non puiden xerar o post de: {dades['titol']}\n{e}")
            continue

        municipi_complet = NOM_COMPLET.get(municipi, "Valdeorras")
        etiqueta = f"{municipi_complet if municipi != 'Comarca' else 'Valdeorras'} · {TEMA_GL.get(tema, 'ACTUALIDADE')}"
        if len(etiqueta) > 34:
            etiqueta = f"{municipi if municipi != 'Comarca' else 'Valdeorras'} · {TEMA_GL.get(tema, 'ACTUALIDADE')}"
        img_path = Path("images") / f"{pid}.png"
        render_post(ia.get("titular") or dades["titol"], etiqueta, mitja, img_path)
        copy = copy_de(ia, municipi_complet, mitja)

        notion_update(pid, {
            "Titular GL": rich(ia.get("titular")),
            "Text GL": rich(ia.get("texto")),
            "Copy": rich(copy + "\n\n[ALT] " + ia.get("alt", "")),
            "Imatge": {"url": f"https://raw.githubusercontent.com/{repo}/main/images/{pid}.png"},
            "Estat": {"select": {"name": "Per aprovar"}},
        })
        tg_photo(img_path, f"🟡 Para aprobar · {ia.get('titular', '')}")
        tg_text(copy + "\n\n— Texto alternativo —\n" + ia.get("alt", ""))
        print("Fet:", ia.get("titular"))


if __name__ == "__main__":
    main()
