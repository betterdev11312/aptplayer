"""Mascote AptPlayer: gato cyberpunk desenhado por FORMAS.

Escrever matriz de pixels a mao nao estava dando silhueta de gato: cabeca e
corpo saiam fundidos. Aqui cada parte e uma forma geometrica posicionada numa
grade pequena, com contorno automatico - assim a silhueta fica sob controle.

Vista: 3/4 frontal (le melhor em tamanho pequeno que o perfil).
"""
from pathlib import Path

from PIL import Image, ImageDraw

# Grade logica; o PNG final e ampliado por SCALE com vizinho mais proximo.
GW, GH = 32, 32
SCALE = 4

C = {
    "line":   (8, 10, 18, 255),
    "body":   (70, 78, 106, 255),
    "light":  (104, 114, 150, 255),
    "dark":   (46, 52, 74, 255),
    "belly":  (128, 138, 172, 255),
    "visor":  (0, 240, 255, 255),
    "shine":  (210, 255, 255, 255),
    "ear":    (252, 238, 10, 255),
    "nose":   (255, 140, 185, 255),
    "collar": (252, 238, 10, 255),
}


def new():
    img = Image.new("RGBA", (GW, GH), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def draw_cat(d, *, head_dx=0, head_dy=0, tail=0, legs="stand",
             eyes="open", body_dy=0, ear_dy=0):
    """Desenha o gato. Os parametros deslocam partes para gerar as poses."""
    bx, by = 0, body_dy

    # ---- cauda (atras do corpo) ----
    tail_paths = {
        0: [(24, 22 + by), (27, 20 + by), (28, 16 + by), (26, 13 + by)],
        1: [(24, 22 + by), (28, 21 + by), (30, 17 + by), (28, 13 + by)],
        2: [(24, 22 + by), (27, 23 + by), (30, 21 + by), (31, 17 + by)],
        3: [(24, 22 + by), (29, 22 + by), (31, 22 + by)],          # esticada
    }
    d.line(tail_paths[tail], fill=C["line"], width=3, joint="curve")
    d.line(tail_paths[tail], fill=C["body"], width=1, joint="curve")

    # ---- corpo: oval com a base achatada ----
    d.ellipse([7 + bx, 16 + by, 25 + bx, 28 + by], fill=C["line"])
    d.ellipse([8 + bx, 17 + by, 24 + bx, 27 + by], fill=C["body"])
    d.ellipse([10 + bx, 18 + by, 22 + bx, 24 + by], fill=C["light"])
    d.ellipse([11 + bx, 22 + by, 21 + bx, 27 + by], fill=C["dark"])

    # ---- patas ----
    if legs == "stand":
        pos = [(10, 27), (14, 27), (18, 27), (22, 27)]
    elif legs == "walk_a":
        pos = [(9, 27), (14, 28), (18, 27), (23, 28)]
    elif legs == "walk_b":
        pos = [(11, 28), (15, 27), (19, 28), (22, 27)]
    elif legs == "run_a":
        pos = [(8, 28), (13, 26), (19, 28), (24, 26)]
    elif legs == "run_b":
        pos = [(10, 26), (15, 28), (17, 26), (23, 28)]
    else:
        pos = []
    for px, py in pos:
        d.rectangle([px + bx, py + by, px + 2 + bx, py + 3 + by], fill=C["line"])
        d.rectangle([px + 1 + bx, py + by, px + 1 + bx, py + 2 + by], fill=C["belly"])

    if legs == "sit":
        # sentado: base larga, sem patas separadas
        d.ellipse([8 + bx, 22 + by, 24 + bx, 29 + by], fill=C["line"])
        d.ellipse([9 + bx, 23 + by, 23 + bx, 28 + by], fill=C["body"])
        d.rectangle([10 + bx, 27 + by, 13 + bx, 29 + by], fill=C["belly"])
        d.rectangle([19 + bx, 27 + by, 22 + bx, 29 + by], fill=C["belly"])

    # ---- coleira ----
    d.rectangle([12 + bx, 15 + by, 20 + bx, 16 + by], fill=C["collar"])

    # ---- cabeca: circulo grande, claramente destacado ----
    hx, hy = 6 + head_dx, 2 + head_dy + by

    d.ellipse([hx, hy + 1, hx + 20, hy + 15], fill=C["line"])
    d.ellipse([hx + 1, hy + 2, hx + 19, hy + 14], fill=C["body"])
    d.ellipse([hx + 3, hy + 3, hx + 17, hy + 9], fill=C["light"])

    # orelhas por cima da cabeca, grandes e pontudas
    for ex, lean in ((hx + 1, -1), (hx + 13, 1)):
        tip = (ex + 3 + lean * 2, hy - 4 + ear_dy)
        d.polygon([(ex, hy + 5), tip, (ex + 6, hy + 4)], fill=C["line"])
        d.polygon([(ex + 2, hy + 4), (tip[0], tip[1] + 2), (ex + 5, hy + 3)],
                  fill=C["ear"])

    # ---- visor: faixa estreita cruzando a cabeca ----
    vy = hy + 6
    d.rectangle([hx + 1, vy, hx + 19, vy + 4], fill=C["line"])
    if eyes == "open":
        d.rectangle([hx + 2, vy + 1, hx + 18, vy + 3], fill=C["visor"])
        d.rectangle([hx + 4, vy + 1, hx + 6, vy + 2], fill=C["shine"])
        d.rectangle([hx + 14, vy + 1, hx + 15, vy + 2], fill=C["shine"])
    else:  # piscando / dormindo: so uma linha fina
        d.rectangle([hx + 2, vy + 2, hx + 18, vy + 2], fill=C["visor"])

    # ---- focinho ----
    d.rectangle([hx + 9, vy + 6, hx + 11, vy + 7], fill=C["nose"])
    d.line([(hx + 10, vy + 8), (hx + 8, vy + 9)], fill=C["line"])
    d.line([(hx + 10, vy + 8), (hx + 12, vy + 9)], fill=C["line"])


def frame(**kw):
    img, d = new()
    draw_cat(d, **kw)
    return img


FRAMES = [
    ("idle1",  dict(tail=0)),
    ("idle2",  dict(tail=1, body_dy=1, ear_dy=0)),
    ("blink",  dict(tail=0, eyes="shut")),
    ("walk1",  dict(tail=1, legs="walk_a")),
    ("walk2",  dict(tail=2, legs="walk_b")),
    ("sit",    dict(tail=0, legs="sit")),
    ("sleep",  dict(tail=0, legs="sit", eyes="shut", head_dy=2)),
    ("dance1", dict(tail=1, head_dx=-2, ear_dy=-1)),
    ("dance2", dict(tail=2, head_dx=2, ear_dy=-1)),
    ("run1",   dict(tail=3, legs="run_a", head_dx=1)),
    ("run2",   dict(tail=3, legs="run_b", head_dx=1)),
]

OUT = Path(r"C:\Users\Arthur\Sistemas\AptPlayer\ui\sprites")
OUT.mkdir(parents=True, exist_ok=True)

sheet = Image.new("RGBA", (GW * len(FRAMES), GH), (0, 0, 0, 0))
imgs = []
for i, (_name, kw) in enumerate(FRAMES):
    img = frame(**kw)
    imgs.append(img)
    sheet.paste(img, (i * GW, 0))
sheet.resize((sheet.width * SCALE, sheet.height * SCALE), Image.NEAREST).save(OUT / "cat.png")

cols = 4
rows_n = (len(FRAMES) + cols - 1) // cols
prev = Image.new("RGBA", (GW * SCALE * cols, GH * SCALE * rows_n), (10, 12, 20, 255))
for i, img in enumerate(imgs):
    cell = img.resize((GW * SCALE, GH * SCALE), Image.NEAREST)
    prev.paste(cell, ((i % cols) * GW * SCALE, (i // cols) * GH * SCALE), cell)
prev.save(OUT / "cat-preview.png")

imgs[0].resize((GW * 10, GH * 10), Image.NEAREST).save(OUT / "cat-big.png")
print("quadro:", GW * SCALE, "x", GH * SCALE, "| frames:", len(FRAMES))
