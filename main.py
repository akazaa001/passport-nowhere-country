#!/usr/bin/env python3
"""The Passport Page of a Country That Isn't There.

Composes, at runtime and fully deterministically, one uncaptioned open
passport spread for the invented Republic of Valdoria: a data page with a
portrait and machine-readable strip, and a facing visa page carrying
arrival/departure stamps from neighbouring invented countries plus one
telling piece of paperwork. No network, no randomness.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png),
1024 x 724 px, well under the 1 MiB cap.
"""

import os
import sys

# The grader runs `python3 -P -s /bot/main.py` in the pinned python image,
# which ships no Pillow: vendor it (and the DejaVu fonts) in this repo and
# put the vendor dir on sys.path before importing PIL. -P keeps the script
# dir off sys.path, so resolve it from __file__ explicitly. If the vendored
# wheel cannot load (wrong interpreter), fall back to a system Pillow.
_HERE = os.path.dirname(os.path.abspath(__file__))
_VENDOR = os.path.join(_HERE, "vendor")
if os.path.isdir(_VENDOR) and _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    for _m in [m for m in sys.modules if m == "PIL" or m.startswith("PIL.")]:
        del sys.modules[_m]
    if _VENDOR in sys.path:
        sys.path.remove(_VENDOR)
    from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# The invented country and its travel history (every date must agree:
# passport issued 12 JUN 2023, so no stamp may predate it).
# ---------------------------------------------------------------------------
COUNTRY = "REPUBLIC OF VALDORIA"
COUNTRY_NATIVE = "REPUBLIKA VALDORIJA"
CAPITAL = "MIRELGRAD"

HOLDER = {
    "type": "P",
    "code": "VAL",
    "number": "VLD847291",
    "surname": "KOVAR",
    "given": "ANA",
    "nationality": "VALDORIAN",
    "dob": "14 MAR 1988",
    "pob": "MIRELGRAD",
    "sex": "F",
    "issued": "12 JUN 2023",
    "expiry": "12 JUN 2033",
    "authority": "MINISTRY OF THE INTERIOR",
}

# Stamps: (country, kind, date, border post, officer, ink colour, rotation)
STAMPS = [
    ("ZAVARIA", "ENTRY", "03 SEP 2024", "KRESNA CROSSING", "OFF. 214", (38, 74, 138), -6),
    ("ZAVARIA", "EXIT", "17 SEP 2024", "KRESNA CROSSING", "OFF. 214", (38, 74, 138), -4),
    ("KARNOVIA", "ENTRY", "22 JAN 2025", "DRAVET BRIDGE", "OFF. 087", (112, 46, 112), 4),
    ("KARNOVIA", "EXIT", "05 FEB 2025", "DRAVET BRIDGE", "OFF. 087", (112, 46, 112), 3),
    ("OSTMAR", "ENTRY", "09 OCT 2025", "MIRELGRAD AIRPORT", "OFF. 301", (34, 110, 72), -3),
    ("OSTMAR", "EXIT", "21 OCT 2025", "MIRELGRAD AIRPORT", "OFF. 301", (34, 110, 72), -5),
]

W, H = 1024, 724
PAPER = (247, 243, 232)
INK = (28, 30, 34)
FAINT = (96, 96, 88)
RULE = (120, 118, 106)

FONT_DIR = os.path.join(_HERE, "vendor", "fonts")


def font(name, size):
    """Load a DejaVu font, falling back gracefully if the sandbox lacks it."""
    for path in (
        os.path.join(FONT_DIR, name),
        os.path.join("/usr/share/fonts/truetype/dejavu", name),
        os.path.join("/usr/share/fonts/truetype/liberation", name),
    ):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


SERIF = lambda s: font("DejaVuSerif.ttf", s)          # noqa: E731
SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)   # noqa: E731
SANS = lambda s: font("DejaVuSans.ttf", s)            # noqa: E731
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)     # noqa: E731
MONO = lambda s: font("DejaVuSansMono.ttf", s)        # noqa: E731


def mrz_check(text):
    """ICAO 9303 check digit: values 0-9, A=10..Z=35, '<'=0; weights 7,3,1."""
    total = 0
    for i, ch in enumerate(text):
        if ch == "<":
            value = 0
        elif ch.isdigit():
            value = int(ch)
        else:
            value = ord(ch) - ord("A") + 10
        total += value * (7, 3, 1)[i % 3]
    return str(total % 10)


def mrz_lines():
    line1 = "P<VALKOVAR<<ANA"
    line1 = line1 + "<" * (44 - len(line1))
    doc = HOLDER["number"]
    dob = "880314"      # 14 MAR 1988
    expiry = "330612"   # 12 JUN 2033
    personal = "<" * 14
    body = (
        doc + mrz_check(doc)
        + "VAL"
        + dob + mrz_check(dob)
        + "F"
        + expiry + mrz_check(expiry)
        + personal + mrz_check(personal)
    )
    line2 = body + mrz_check(body)
    return line1, line2


def draw_coat_of_arms(d, cx, cy, s):
    """A small invented arms: shield, three mountain peaks, one star."""
    d.polygon([(cx - s, cy - s * 0.7), (cx + s, cy - s * 0.7),
               (cx + s, cy + s * 0.3), (cx, cy + s), (cx - s, cy + s * 0.3)],
              outline=(58, 66, 84), width=2)
    d.polygon([(cx - s * 0.7, cy + s * 0.35), (cx - s * 0.35, cy - s * 0.35),
               (cx, cy + s * 0.35), (cx + s * 0.3, cy - s * 0.1),
               (cx + s * 0.7, cy + s * 0.35)],
              fill=(58, 66, 84))
    d.regular_polygon((cx, cy - s * 0.45, s * 0.18), 5, fill=(150, 40, 40))


def text(d, xy, s, f, fill=INK, anchor="la"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def centred(d, cx, y, s, f, fill=INK):
    d.text((cx, y), s, font=f, fill=fill, anchor="ma")


def field(d, x, y, label, value, vfont=None, label_w=118):
    text(d, (x, y), label, SANS(10), fill=FAINT)
    text(d, (x + label_w, y - 1), value, vfont or SANS_B(13))


def draw_stamp(base, cx, cy, country, kind, date, post, officer, colour, angle):
    """One border-control stamp, drawn on its own layer and rotated."""
    sw, sh = 190, 96
    layer = Image.new("RGBA", (sw + 40, sh + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(layer)
    ox, oy = 20, 20
    sd.rounded_rectangle([ox, oy, ox + sw, oy + sh], radius=8,
                         outline=colour + (235,), width=2)
    sd.line([ox + 6, oy + 30, ox + sw - 6, oy + 30], fill=colour + (235,), width=1)
    sd.line([ox + 6, oy + 66, ox + sw - 6, oy + 66], fill=colour + (235,), width=1)
    centred(sd, ox + sw // 2, oy + 5, country, SANS_B(15), fill=colour + (235,))
    centred(sd, ox + sw // 2, oy + 34, f"{kind}  \u2022  {date}", SANS_B(13),
            fill=colour + (235,))
    centred(sd, ox + sw // 2, oy + 71, post, SANS(10), fill=colour + (220,))
    d2 = ImageDraw.Draw(layer)
    d2.text((ox + sw - 8, oy + 80), officer, font=SANS(8),
            fill=colour + (200,), anchor="ra")
    layer = layer.rotate(angle, resample=Image.BICUBIC, expand=False)
    base.alpha_composite(layer, (cx - (sw + 40) // 2, cy - (sh + 40) // 2))


def main():
    img = Image.new("RGBA", (W, H), PAPER + (255,))
    d = ImageDraw.Draw(img, "RGBA")

    # Faint guilloche arcs across the whole spread, deterministic.
    for r in range(120, 1100, 64):
        d.arc([512 - r, 362 - r, 512 + r, 362 + r], 200, 340,
              fill=(190, 184, 164, 22), width=1)
    # Centre seam and page edges.
    d.rectangle([0, 0, W - 1, H - 1], outline=(150, 146, 130), width=2)
    d.rectangle([510, 2, 513, H - 3], fill=(200, 195, 178))
    d.line([512, 0, 512, H], fill=(120, 116, 100), width=1)

    # ------------------------- LEFT PAGE: data page -------------------------
    draw_coat_of_arms(d, 76, 66, 30)
    text(d, (118, 38), COUNTRY, SERIF_B(19))
    text(d, (118, 62), COUNTRY_NATIVE, SANS(11), fill=FAINT)
    centred(d, 256, 92, "PASSPORT  \u2022  PUTOVNICA", SANS_B(11), fill=(58, 66, 84))
    d.line([36, 112, 476, 112], fill=RULE, width=1)

    # Portrait, composited from the generated asset in this repo.
    here = os.path.dirname(os.path.abspath(__file__))
    portrait_path = os.path.join(here, "portrait.png")
    px, py, pw, ph = 36, 128, 148, 188
    if os.path.exists(portrait_path):
        portrait = Image.open(portrait_path).convert("RGB")
        portrait = portrait.resize((pw, ph), Image.LANCZOS)
        img.paste(portrait, (px, py))
    else:  # fallback: a plain stylised silhouette
        d.rectangle([px, py, px + pw, py + ph], fill=(214, 210, 198))
        d.ellipse([px + 44, py + 26, px + 104, py + 106], fill=(120, 116, 108))
        d.pieslice([px + 8, py + 108, px + 140, py + 230], 180, 360, fill=(120, 116, 108))
    d.rectangle([px, py, px + pw, py + ph], outline=INK, width=1)

    # Data fields, two columns of label/value pairs.
    fx, fy = 200, 128
    field(d, fx, fy + 0, "Type / Tip", HOLDER["type"])
    field(d, fx, fy + 28, "Code / Kod", HOLDER["code"])
    field(d, fx, fy + 56, "Passport No.", HOLDER["number"])
    field(d, fx, fy + 84, "Surname", HOLDER["surname"])
    field(d, fx, fy + 112, "Given names", HOLDER["given"])
    field(d, fx, fy + 140, "Nationality", HOLDER["nationality"])
    field(d, 36, 336, "Date of birth", HOLDER["dob"])
    field(d, 36, 364, "Place of birth", HOLDER["pob"])
    field(d, 36, 392, "Sex / Spol", HOLDER["sex"])
    field(d, 256, 336, "Date of issue", HOLDER["issued"])
    field(d, 256, 364, "Date of expiry", HOLDER["expiry"])
    field(d, 256, 392, "Authority", "MIRELGRAD", vfont=SANS_B(11))
    text(d, (256, 410), HOLDER["authority"], SANS(9), fill=FAINT)
    # Signature.
    text(d, (36, 436), "Holder's signature / Potpis", SANS(10), fill=FAINT)
    d.line([36, 468, 210, 468], fill=INK, width=1)
    text(d, (40, 446), "Ana Kovar", SERIF(18))

    # Machine-readable zone.
    d.rectangle([28, 492, 484, 566], fill=(238, 234, 222))
    d.line([28, 492, 484, 492], fill=RULE, width=1)
    line1, line2 = mrz_lines()
    text(d, (40, 500), line1, MONO(15))
    text(d, (40, 528), line2, MONO(15))

    # Holder's address fills the data page the way a real one does.
    text(d, (36, 592), "Address / Adresa", SANS(10), fill=FAINT)
    text(d, (36, 610), "14 Vintar Lane, Mirelgrad, Valdoria", SANS_B(12))

    # Page furniture.
    centred(d, 256, 668, "This passport contains 32 pages  \u2022  Page 2", SANS(9), fill=FAINT)

    # ------------------------- RIGHT PAGE: visa page ------------------------
    centred(d, 768, 36, "VISAS  \u2022  VIZE", SERIF_B(17))
    d.line([548, 62, 988, 62], fill=RULE, width=1)

    draw_stamp(img, 660, 140, *STAMPS[0])
    draw_stamp(img, 870, 150, *STAMPS[1])
    draw_stamp(img, 660, 268, *STAMPS[2])
    draw_stamp(img, 870, 278, *STAMPS[3])
    draw_stamp(img, 660, 396, *STAMPS[4])
    draw_stamp(img, 870, 406, *STAMPS[5])

    # The telling paperwork detail: a visa-condition box.
    bx, by, bw, bh = 548, 486, 440, 118
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=4,
                        outline=(58, 66, 84), width=2)
    text(d, (bx + 12, by + 8), "CONDITIONS OF STAY  \u2022  UVJETI BORAVKA",
         SANS_B(11), fill=(58, 66, 84))
    d.line([bx + 12, by + 28, bx + bw - 12, by + 28], fill=RULE, width=1)
    cond = ("Holder is exempt from visa for the Zavarian Confederation\n"
            "under the Mirelgrad Accord, 2019. Work in Zavaria only\n"
            "under a seasonal harvest permit (Art. 14).")
    text(d, (bx + 12, by + 36), cond, SANS(11))
    text(d, (bx + 12, by + 88), "DEPARTURE TAX PAID \u2014 25 KR \u2014 MIRELGRAD AIRPORT",
         SANS_B(10), fill=(150, 40, 40))

    centred(d, 768, 668, "Page 3", SANS(9), fill=FAINT)

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "entry.png")
    img.convert("RGB").save(out_path, "PNG")
    print(f"wrote {out_path} ({os.path.getsize(out_path)} bytes)")


if __name__ == "__main__":
    main()
