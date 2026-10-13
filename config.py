"""Configuració de Valdeorras Hoxe. Per afegir una font, afegeix una línia a FEEDS."""

NOTION_DB = "fbdb5f84f25c4596a0ee495e404bcc21"
NOTION_URL = "https://app.notion.com/p/" + NOTION_DB
GEMINI_MODEL_DEFAULT = "gemini-2.5-flash"


def gn(q, lang="es"):
    return f"https://news.google.com/rss/search?q={q}&hl={lang}&gl=ES&ceid=ES:{lang}"


FEEDS = [
    "https://www.valdeorrasdecerca.com/feed/",
    "https://osil.info/feed/",
    "https://www.somoscomarca.es/feed/",
    "https://valdeorrasesvino.com/feed",
    "https://dovaldeorras.gal/feed/",
    gn("Valdeorras"),
    gn("Valdeorras+site:laregion.es"),
    gn("Valdeorras+site:farodevigo.es"),
    gn("Valdeorras+site:lavozdegalicia.es"),
    gn("Valdeorras+site:elcorreogallego.es"),
    gn("Valdeorras+site:nosdiario.gal", "gl"),
    gn('"O+Barco+de+Valdeorras"'),
    gn('"A+Rúa"+Valdeorras'),
    gn("Larouco"),
    gn('"DO+Valdeorras"'),
    gn('(Valdeorras+OR+"O+Barco+de+Valdeorras"+OR+Larouco+OR+Godello)+'
       '(site:elpais.com+OR+site:elmundo.es+OR+site:abc.es+OR+site:lavanguardia.com+'
       'OR+site:20minutos.es+OR+site:elespanol.com+OR+site:eldiario.es+OR+site:rtve.es+'
       'OR+site:europapress.es+OR+site:efe.com)'),
]

# pista dins del domini o del nom del mitjà -> nom a Notion
MITJANS = [
    ("valdeorrasdecerca", "Valdeorras de Cerca"), ("valdeorras de cerca", "Valdeorras de Cerca"),
    ("osil.info", "O Sil"), ("o sil", "O Sil"),
    ("somoscomarca", "Somos Comarca"), ("somos comarca", "Somos Comarca"),
    ("laregion", "La Región"), ("la región", "La Región"), ("la region", "La Región"),
    ("farodevigo", "Faro de Vigo"), ("faro de vigo", "Faro de Vigo"),
    ("lavozdegalicia", "La Voz de Galicia"), ("la voz de galicia", "La Voz de Galicia"),
    ("elcorreogallego", "El Correo Gallego"), ("el correo gallego", "El Correo Gallego"),
    ("nosdiario", "Nós Diario"), ("nós diario", "Nós Diario"),
    ("dovaldeorras", "DO Valdeorras"), ("valdeorrasesvino", "Valdeorras é viño"),
]
ESTATALS = ["el país", "el mundo", "abc", "la vanguardia", "20minutos", "el español",
            "eldiario", "rtve", "europa press", "efe"]

MUNICIPIS = ["O Barco", "A Rúa", "O Bolo", "Carballeda", "Larouco", "Petín", "Rubiá",
             "A Veiga", "Vilamartín", "Comarca"]
TEMES = ["Sucessos", "Festes", "Cultura", "Vi", "Política", "Esports", "Economia", "Gent"]

# Nom complet per al copy (GEO)
NOM_COMPLET = {
    "O Barco": "O Barco de Valdeorras", "A Rúa": "A Rúa", "O Bolo": "O Bolo",
    "Carballeda": "Carballeda de Valdeorras", "Larouco": "Larouco", "Petín": "Petín",
    "Rubiá": "Rubiá", "A Veiga": "A Veiga", "Vilamartín": "Vilamartín de Valdeorras",
    "Comarca": "Valdeorras",
}
# Etiqueta en gallec per a la imatge
TEMA_GL = {"Sucessos": "SUCESOS", "Festes": "FESTAS", "Cultura": "CULTURA", "Vi": "VIÑO",
           "Política": "POLÍTICA", "Esports": "DEPORTES", "Economia": "ECONOMÍA", "Gent": "XENTE"}
