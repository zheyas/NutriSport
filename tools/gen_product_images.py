"""
Генерирует SVG-иллюстрации упаковок для товаров NutriSport.
Картинка выбирается по названию/категории товара, цвет — детерминированно по id.

    python tools/gen_product_images.py            # сгенерировать и прописать пути в БД
    python tools/gen_product_images.py --no-db    # только сгенерировать файлы
"""
import argparse
import hashlib
import html
import os
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT_DIR = ROOT / "static" / "img" / "products"

ACCENTS = [
    ("#FFF500", "#FF79FE"),  # жёлтый / розовый — фирменные цвета
    ("#FF79FE", "#8A5CFF"),
    ("#00E5FF", "#2F6BFF"),
    ("#00FF88", "#00B3A4"),
    ("#FF9F1C", "#FF4D6D"),
    ("#FF4D6D", "#B5179E"),
    ("#B4FF39", "#1FAA59"),
    ("#FFD166", "#EF476F"),
]


def pick_accent(key: str):
    h = int(hashlib.md5(key.encode()).hexdigest(), 16)
    return ACCENTS[h % len(ACCENTS)]


def clean_name(name: str) -> str:
    return re.sub(r"\s+\d+$", "", name or "").strip()


def kind_of(name: str, category: str) -> str:
    n = (name or "").lower()
    c = (category or "").upper()
    if "t-shirt" in n or "футболк" in n: return "tshirt"
    if "hoodie" in n or "худи" in n: return "hoodie"
    if n.split()[:1] == ["cap"] or "кепк" in n: return "cap"
    if "bag" in n or "сумк" in n: return "gymbag"
    if "bar" in n or "батонч" in n: return "bar"
    if "cookie" in n or "печень" in n: return "cookie"
    if "chips" in n or "чипс" in n: return "chips"
    if "gel" in n or "гель" in n: return "gel"
    if c == "ОДЕЖДА": return "tshirt"
    if c == "СНЕКИ": return "bar"
    if c == "ГЕЙНЕРЫ" or "gainer" in n or "mass" in n or "carbo" in n: return "pouch"
    if c == "ВИТАМИНЫ" or any(k in n for k in ("vitamin", "omega", "zinc", "magnes")): return "pills"
    if c == "АМИНОКИСЛОТЫ": return "amino"
    return "tub"


def wrap_label(text: str, max_len: int = 12):
    words, lines, cur = text.upper().replace("+", "+ ").split(), [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > max_len:
            lines.append(cur); cur = w
        else:
            cur = f"{cur} {w}".strip()
    if cur: lines.append(cur)
    return lines[:3]


def label_text(lines, x, y, size, fill, lh=None, anchor="middle", weight=900, max_chars=None):
    longest = max((len(l) for l in lines), default=1)
    if max_chars and longest > max_chars:
        size = round(size * max_chars / longest)
    lh = lh or size * 1.1
    out = []
    for i, line in enumerate(lines):
        out.append(
            f'<text x="{x}" y="{y + i * lh:.1f}" text-anchor="{anchor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" font-family="Arial Black, Impact, Helvetica, sans-serif" '
            f'letter-spacing="0.5">{html.escape(line)}</text>'
        )
    return "\n".join(out)


def brand(x, y, size=22, fill="#FFF500"):
    return (f'<text x="{x}" y="{y}" text-anchor="middle" font-size="{size}" font-weight="900" '
            f'fill="{fill}" font-family="Arial Black, Impact, Helvetica, sans-serif" letter-spacing="3">NUTRISPORT</text>')


# ---------- упаковки ----------

def tub(a, b, title, sub):
    lines = wrap_label(title, 11)
    return f'''
  <ellipse cx="300" cy="505" rx="150" ry="18" fill="#000" opacity=".45"/>
  <rect x="160" y="150" width="280" height="350" rx="28" fill="url(#body)"/>
  <rect x="160" y="150" width="280" height="350" rx="28" fill="url(#shine)"/>
  <rect x="150" y="110" width="300" height="62" rx="14" fill="#111"/>
  <rect x="150" y="110" width="300" height="62" rx="14" fill="url(#shine)" opacity=".6"/>
  <rect x="150" y="160" width="300" height="10" fill="{a}" opacity=".9"/>
  <rect x="160" y="250" width="280" height="170" fill="url(#band)"/>
  {brand(300, 222, 24, a)}
  {label_text(lines, 300, 346 - (len(lines) - 1) * 16, 30, "#111", max_chars=13)}
  <text x="300" y="460" text-anchor="middle" font-size="18" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
'''


def pouch(a, b, title, sub):
    lines = wrap_label(title, 10)
    return f'''
  <ellipse cx="300" cy="512" rx="140" ry="16" fill="#000" opacity=".45"/>
  <path d="M180 120 H420 L440 490 Q300 515 160 490 Z" fill="url(#body)"/>
  <path d="M180 120 H420 L440 490 Q300 515 160 490 Z" fill="url(#shine)"/>
  <rect x="180" y="120" width="240" height="26" fill="#0d0d0d"/>
  <line x1="190" y1="160" x2="410" y2="160" stroke="{a}" stroke-width="3" stroke-dasharray="6 6"/>
  <path d="M168 260 H432 L438 400 H162 Z" fill="url(#band)"/>
  {brand(300, 215, 26, a)}
  {label_text(lines, 300, 342 - (len(lines) - 1) * 17, 32, "#111", max_chars=12)}
  <text x="300" y="455" text-anchor="middle" font-size="18" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
'''


def amino(a, b, title, sub):
    lines = wrap_label(title, 9)
    return f'''
  <ellipse cx="300" cy="505" rx="110" ry="15" fill="#000" opacity=".45"/>
  <rect x="200" y="175" width="200" height="325" rx="22" fill="url(#body)"/>
  <rect x="200" y="175" width="200" height="325" rx="22" fill="url(#shine)"/>
  <rect x="212" y="120" width="176" height="70" rx="12" fill="{a}"/>
  <rect x="212" y="120" width="176" height="70" rx="12" fill="url(#shine)" opacity=".5"/>
  <g stroke="#000" stroke-opacity=".25" stroke-width="3">
    <line x1="232" y1="128" x2="232" y2="182"/><line x1="262" y1="128" x2="262" y2="182"/>
    <line x1="292" y1="128" x2="292" y2="182"/><line x1="322" y1="128" x2="322" y2="182"/>
    <line x1="352" y1="128" x2="352" y2="182"/>
  </g>
  <rect x="200" y="265" width="200" height="150" fill="url(#band)"/>
  {brand(300, 240, 18, a)}
  {label_text(lines, 300, 350 - (len(lines) - 1) * 15, 28, "#111", max_chars=10)}
  <text x="300" y="455" text-anchor="middle" font-size="16" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
'''


def pills(a, b, title, sub):
    lines = wrap_label(title, 9)
    return f'''
  <ellipse cx="270" cy="505" rx="105" ry="14" fill="#000" opacity=".45"/>
  <rect x="180" y="205" width="180" height="295" rx="30" fill="url(#body)"/>
  <rect x="180" y="205" width="180" height="295" rx="30" fill="url(#shine)"/>
  <rect x="205" y="160" width="130" height="58" rx="10" fill="#f2f2f2"/>
  <rect x="205" y="160" width="130" height="58" rx="10" fill="url(#shine)" opacity=".5"/>
  <rect x="180" y="285" width="180" height="140" fill="url(#band)"/>
  {brand(270, 260, 17, a)}
  {label_text(lines, 270, 364 - (len(lines) - 1) * 14, 26, "#111", max_chars=10)}
  <text x="270" y="465" text-anchor="middle" font-size="15" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
  <g transform="translate(420 440) rotate(-25)">
    <rect x="-38" y="-15" width="76" height="30" rx="15" fill="{a}"/>
    <rect x="0" y="-15" width="38" height="30" rx="15" fill="#fff" opacity=".9"/>
    <rect x="0" y="-15" width="10" height="30" fill="#fff" opacity=".9"/>
  </g>
  <g transform="translate(395 492) rotate(15)">
    <rect x="-34" y="-13" width="68" height="26" rx="13" fill="{b}"/>
    <rect x="0" y="-13" width="34" height="26" rx="13" fill="#fff" opacity=".85"/>
    <rect x="0" y="-13" width="10" height="26" fill="#fff" opacity=".85"/>
  </g>
'''


def bar(a, b, title, sub):
    lines = wrap_label(title, 14)
    return f'''
  <ellipse cx="300" cy="420" rx="210" ry="18" fill="#000" opacity=".45"/>
  <g transform="rotate(-12 300 320)">
    <path d="M90 250 l20 -8 l-10 14 l12 8 l-12 8 l12 8 l-12 8 l12 8 l-12 8 l12 8 l-12 8 l10 14 l-20 -8 Z" fill="{a}"/>
    <path d="M510 250 l-20 -8 l10 14 l-12 8 l12 8 l-12 8 l12 8 l-12 8 l12 8 l-12 8 l12 8 l-10 14 l20 -8 Z" fill="{a}"/>
    <rect x="100" y="245" width="400" height="120" rx="10" fill="url(#body)"/>
    <rect x="100" y="245" width="400" height="120" rx="10" fill="url(#shine)"/>
    <rect x="100" y="245" width="130" height="120" fill="url(#band)"/>
    <text x="165" y="300" text-anchor="middle" font-size="34" font-weight="900" fill="#111" font-family="Arial Black, Impact, sans-serif">20g</text>
    <text x="165" y="330" text-anchor="middle" font-size="15" font-weight="700" fill="#111" font-family="Arial, Helvetica, sans-serif">PROTEIN</text>
    {brand(365, 285, 18, a)}
    {label_text(lines, 365, 322, 22, "#fff", max_chars=16)}
  </g>
'''


def cookie(a, b, title, sub):
    lines = wrap_label(title, 14)
    chips = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="#3b2314"/>'
        for x, y, r in [(250, 250, 12), (310, 220, 9), (350, 280, 13), (280, 310, 10), (215, 300, 8), (330, 340, 9)]
    )
    return f'''
  <ellipse cx="300" cy="470" rx="190" ry="18" fill="#000" opacity=".45"/>
  <rect x="120" y="330" width="360" height="130" rx="16" fill="url(#body)"/>
  <rect x="120" y="330" width="360" height="130" rx="16" fill="url(#shine)"/>
  <rect x="120" y="330" width="120" height="130" fill="url(#band)"/>
  <text x="180" y="405" text-anchor="middle" font-size="26" font-weight="900" fill="#111" font-family="Arial Black, Impact, sans-serif">16g</text>
  {brand(360, 370, 17, a)}
  {label_text(lines, 360, 408, 22, "#fff", max_chars=14)}
  <circle cx="285" cy="270" r="105" fill="#c98b4e"/>
  <circle cx="285" cy="270" r="105" fill="url(#shine)" opacity=".5"/>
  {chips}
'''


def chips(a, b, title, sub):
    lines = wrap_label(title, 10)
    return f'''
  <ellipse cx="300" cy="505" rx="150" ry="16" fill="#000" opacity=".45"/>
  <path d="M170 120 Q300 140 430 120 L445 300 L430 485 Q300 505 170 485 L155 300 Z" fill="url(#body)"/>
  <path d="M170 120 Q300 140 430 120 L445 300 L430 485 Q300 505 170 485 L155 300 Z" fill="url(#shine)"/>
  <path d="M170 120 Q300 140 430 120 L432 150 Q300 170 168 150 Z" fill="#0d0d0d"/>
  <circle cx="300" cy="330" r="95" fill="url(#band)"/>
  {brand(300, 205, 24, a)}
  {label_text(lines, 300, 330 - (len(lines) - 1) * 15, 28, "#111", max_chars=9)}
  <text x="300" y="460" text-anchor="middle" font-size="17" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
'''


def gel(a, b, title, sub):
    lines = wrap_label(title, 9)
    return f'''
  <ellipse cx="300" cy="505" rx="110" ry="14" fill="#000" opacity=".45"/>
  <path d="M215 150 H385 V470 Q300 500 215 470 Z" fill="url(#body)"/>
  <path d="M215 150 H385 V470 Q300 500 215 470 Z" fill="url(#shine)"/>
  <path d="M270 150 V110 H330 V150 Z" fill="url(#body)"/>
  <rect x="270" y="98" width="60" height="16" rx="4" fill="{a}"/>
  <rect x="215" y="270" width="170" height="140" fill="url(#band)"/>
  {brand(300, 215, 18, a)}
  {label_text(lines, 300, 335 - (len(lines) - 1) * 14, 26, "#111", max_chars=9)}
  <text x="300" y="450" text-anchor="middle" font-size="15" font-weight="700" fill="{a}" font-family="Arial, Helvetica, sans-serif" letter-spacing="2">{html.escape(sub)}</text>
'''


def tshirt(a, b, title, sub):
    return f'''
  <ellipse cx="300" cy="505" rx="170" ry="16" fill="#000" opacity=".45"/>
  <path d="M225 120 Q300 160 375 120 L480 170 L445 260 L405 245 L405 490 H195 V245 L155 260 L120 170 Z" fill="url(#body)"/>
  <path d="M225 120 Q300 160 375 120 L480 170 L445 260 L405 245 L405 490 H195 V245 L155 260 L120 170 Z" fill="url(#shine)"/>
  <path d="M225 120 Q300 160 375 120 Q300 185 225 120 Z" fill="#0b0b0b"/>
  <path d="M240 290 L380 270 L360 330 L220 350 Z" fill="url(#band)"/>
  {brand(300, 318, 26, "#111").replace('text-anchor="middle"', 'text-anchor="middle" transform="rotate(-8 300 310)"')}
'''


def hoodie(a, b, title, sub):
    return f'''
  <ellipse cx="300" cy="510" rx="180" ry="16" fill="#000" opacity=".45"/>
  <path d="M230 140 Q300 70 370 140 L470 185 L500 440 L440 450 L420 300 L410 495 H190 L180 300 L160 450 L100 440 L130 185 Z" fill="url(#body)"/>
  <path d="M230 140 Q300 70 370 140 L470 185 L500 440 L440 450 L420 300 L410 495 H190 L180 300 L160 450 L100 440 L130 185 Z" fill="url(#shine)"/>
  <path d="M245 150 Q300 100 355 150 Q300 200 245 150 Z" fill="#0b0b0b"/>
  <line x1="285" y1="175" x2="280" y2="235" stroke="{a}" stroke-width="5" stroke-linecap="round"/>
  <line x1="315" y1="175" x2="320" y2="235" stroke="{a}" stroke-width="5" stroke-linecap="round"/>
  <path d="M235 385 H365 L385 470 H215 Z" fill="#000" opacity=".25"/>
  <rect x="215" y="270" width="170" height="54" rx="6" fill="url(#band)"/>
  {brand(300, 306, 22, "#111")}
'''


def cap(a, b, title, sub):
    return f'''
  <ellipse cx="300" cy="455" rx="200" ry="20" fill="#000" opacity=".45"/>
  <path d="M150 360 Q150 190 300 185 Q450 190 450 360 Z" fill="url(#body)"/>
  <path d="M150 360 Q150 190 300 185 Q450 190 450 360 Z" fill="url(#shine)"/>
  <path d="M300 187 V360" stroke="#000" stroke-opacity=".3" stroke-width="3"/>
  <circle cx="300" cy="190" r="10" fill="{a}"/>
  <path d="M140 355 Q300 330 470 360 Q520 380 500 410 Q300 380 120 395 Q110 370 140 355 Z" fill="{a}"/>
  <path d="M140 355 Q300 330 470 360 Q520 380 500 410 Q300 380 120 395 Q110 370 140 355 Z" fill="url(#shine)" opacity=".5"/>
  <rect x="215" y="255" width="170" height="48" rx="6" fill="url(#band)"/>
  {brand(300, 287, 20, "#111")}
'''


def gymbag(a, b, title, sub):
    return f'''
  <ellipse cx="300" cy="480" rx="220" ry="18" fill="#000" opacity=".45"/>
  <path d="M210 250 Q210 150 300 150 Q390 150 390 250" fill="none" stroke="#111" stroke-width="18"/>
  <path d="M210 250 Q210 150 300 150 Q390 150 390 250" fill="none" stroke="{a}" stroke-width="4"/>
  <rect x="100" y="240" width="400" height="220" rx="100" fill="url(#body)"/>
  <rect x="100" y="240" width="400" height="220" rx="100" fill="url(#shine)"/>
  <path d="M150 262 H450" stroke="{a}" stroke-width="5" stroke-dasharray="10 6"/>
  <rect x="210" y="320" width="180" height="60" rx="8" fill="url(#band)"/>
  {brand(300, 358, 22, "#111")}
'''


DRAW = dict(tub=tub, pouch=pouch, amino=amino, pills=pills, bar=bar, cookie=cookie,
            chips=chips, gel=gel, tshirt=tshirt, hoodie=hoodie, cap=cap, gymbag=gymbag)

SUBTITLE = {
    "ПРОТЕИНЫ": "PROTEIN POWDER", "ГЕЙНЕРЫ": "MASS GAINER", "АМИНОКИСЛОТЫ": "AMINO ACIDS",
    "ВИТАМИНЫ": "90 CAPSULES", "СНЕКИ": "HIGH PROTEIN", "ОДЕЖДА": "SPORTSWEAR",
}


def render_svg(product_id: str, name: str, category: str) -> str:
    a, b = pick_accent(product_id)
    kind = kind_of(name, category)
    title = clean_name(name)
    sub = SUBTITLE.get((category or "").upper(), "SPORT NUTRITION")
    body_dark = kind not in ("tshirt", "hoodie", "cap", "gymbag") or int(hashlib.md5(product_id.encode()).hexdigest(), 16) % 2
    body_top, body_bot = ("#2b2b2b", "#0e0e0e") if body_dark else (b, "#1a1a1a")
    shapes = DRAW[kind](a, b, title, sub)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 600" width="600" height="600">
  <title>{html.escape(title)}</title>
  <defs>
    <radialGradient id="glow" cx="50%" cy="45%" r="60%">
      <stop offset="0" stop-color="{a}" stop-opacity=".45"/>
      <stop offset=".55" stop-color="{b}" stop-opacity=".12"/>
      <stop offset="1" stop-color="#141414" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#2a2a2a"/><stop offset="1" stop-color="#121212"/>
    </linearGradient>
    <linearGradient id="body" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{body_top}"/><stop offset="1" stop-color="{body_bot}"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".18" stop-color="#fff" stop-opacity=".16"/>
      <stop offset=".32" stop-color="#fff" stop-opacity="0"/>
      <stop offset=".85" stop-color="#000" stop-opacity="0"/>
      <stop offset="1" stop-color="#000" stop-opacity=".35"/>
    </linearGradient>
    <linearGradient id="band" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{b}"/><stop offset="1" stop-color="{a}"/>
    </linearGradient>
  </defs>
  <rect width="600" height="600" fill="url(#bg)"/>
  <rect width="600" height="600" fill="url(#glow)"/>
  <g opacity=".07" stroke="#fff">
    <line x1="0" y1="540" x2="600" y2="540"/><line x1="0" y1="560" x2="600" y2="560"/>
  </g>
  <g transform="translate(300 300) scale(1.12) translate(-300 -300)">
{shapes}
  </g>
</svg>
'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-db", action="store_true", help="не обновлять пути к картинкам в БД")
    parser.add_argument("--all", action="store_true",
                        help="перезаписать картинку у всех товаров, а не только у тех, где её нет/файл отсутствует")
    parser.add_argument("--db", default=None, help="путь к БД (по умолчанию setting.DB_PATH)")
    args = parser.parse_args()

    if args.db:
        db_path = args.db
    else:
        from setting import DB_PATH as db_path

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, name, category, image FROM products").fetchall()
    updated = 0
    for pid, name, category, image in rows:
        (OUT_DIR / f"{pid}.svg").write_text(render_svg(pid, name, category), encoding="utf-8")
        url = f"/static/img/products/{pid}.svg"
        broken = not image or not (ROOT / image.lstrip("/")).exists()
        if not args.no_db and (args.all or broken) and image != url:
            conn.execute("UPDATE products SET image = ? WHERE id = ?", (url, pid))
            updated += 1
    conn.commit()
    conn.close()
    print(f"Сгенерировано {len(rows)} картинок в {OUT_DIR.relative_to(ROOT)}; обновлено в БД: {updated}")


if __name__ == "__main__":
    main()
