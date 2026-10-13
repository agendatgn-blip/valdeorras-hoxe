"""Dibuixa la imatge del post (1080x1350) amb la marca de Valdeorras Hoxe."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

F = Path(__file__).parent / "fonts"
PISSARRA, GODELLO, CREMA, VERMELL = "#1E262B", "#E2C044", "#F3EEE3", "#E0483B"
W, H, PAD = 1080, 1350, 72


def archivo(size, weight):
    f = ImageFont.truetype(str(F / "Archivo.ttf"), size)
    try:
        f.set_variation_by_axes([weight, 100])  # pes, amplada
    except Exception:
        pass
    return f


def anton(size):
    return ImageFont.truetype(str(F / "Anton-Regular.ttf"), size)


def tracked(d, xy, text, font, fill, tracking):
    """Text amb espaiat entre lletres. Retorna l'amplada."""
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + tracking
    return x - xy[0] - tracking


def wrap(d, text, font, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if d.textlength(test, font=font) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def render_post(titular, etiqueta, font_text, out_path):
    img = Image.new("RGB", (W, H), PISSARRA)
    d = ImageDraw.Draw(img)

    # Capçalera: VALDEORRAS HOXE + punt vermell
    hoxe = anton(52)
    base_y = PAD + 46
    vw = tracked(d, (PAD, base_y - 30), "VALDEORRAS", archivo(30, 800), CREMA, 6)
    d.text((PAD + vw + 14, base_y), "HOXE", font=hoxe, fill=GODELLO, anchor="ls")
    d.ellipse((W - PAD - 22, PAD + 18, W - PAD, PAD + 40), fill=VERMELL)

    # Peu: barra, font i usuari
    peu_y = H - PAD
    d.text((PAD, peu_y), f"Fonte: {font_text}"[:48], font=archivo(32, 500), fill=CREMA, anchor="ls")
    d.text((W - PAD, peu_y), "@valdeorrashoxe", font=archivo(30, 800), fill=GODELLO, anchor="rs")
    barra_y = peu_y - 40 - 36 - 12
    d.rounded_rectangle((PAD, barra_y, PAD + 140, barra_y + 12), radius=6, fill=GODELLO)

    # Titular: la mida baixa fins que hi cap
    zona_top, zona_bot, ample = PAD + 110, barra_y - 50, W - 2 * PAD
    tag_font = archivo(34, 800)
    for size in range(116, 60, -4):
        f = anton(size)
        lines = wrap(d, titular, f, ample)
        lh = int(size * 1.04)
        alt = 34 + 36 + lh * len(lines)
        if alt <= zona_bot - zona_top and len(lines) <= 5:
            break
    y = zona_top + (zona_bot - zona_top - alt) // 2
    tracked(d, (PAD, y), etiqueta.upper(), tag_font, GODELLO, 6)
    y += 34 + 36
    for line in lines:
        d.text((PAD, y), line, font=f, fill=CREMA)
        y += lh

    img.save(out_path, "PNG", optimize=True)
    return out_path


if __name__ == "__main__":
    render_post("A Feira do Viño múdase ao Malecón para seguir medrando", "O BARCO · VIÑO",
                "Valdeorras é viño", "proba.png")
    print("proba.png feta")
