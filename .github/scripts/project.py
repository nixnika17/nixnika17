"""Перемальовує assets/project.svg (і project2.svg, project3.svg, ...) на основі
.github/project.txt. Кожен проєкт - окремий блок, блоки розділяються рядком "---".
Картка сама підлаштовує розмір шрифту, ширину і перенос рядків під довжину тексту."""
import os
import re
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, ".github", "project.txt")
README = os.path.join(ROOT, "README.md")

DEFAULTS = {
    "name": "Project Name Here",
    "description": "Short description of what you are building right now",
    "status": "In Progress",
    "tech": "ESP32 | C++",
    "link": "https://github.com/nixnika17",
}

CHAR_W = 0.6  # приблизна ширина символу моноширинного шрифту відносно font-size


def read_configs():
    """Повертає список конфігів - по одному на кожен проєкт, розділений рядком ---."""
    if not os.path.exists(CFG):
        return [dict(DEFAULTS)]
    with open(CFG, encoding="utf-8") as f:
        raw = f.read()
    blocks = re.split(r'(?m)^\s*-{3,}\s*$', raw)
    configs = []
    for block in blocks:
        cfg = dict(DEFAULTS)
        has_any = False
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key = key.strip().lower()
            val = val.strip()
            if key in cfg and val:
                cfg[key] = val
                has_any = True
        if has_any:
            configs.append(cfg)
    return configs or [dict(DEFAULTS)]


def out_path(i):
    name = "project.svg" if i == 0 else f"project{i+1}.svg"
    return os.path.join(ROOT, "assets", name), name


def update_readme_link(filename, link):
    """Синхронізує href навколо assets/<filename> в README.md зі значенням link.
    Якщо картинка ще не обгорнута в <a href>, бот сам додає обгортку.
    Якщо такої картинки в README ще немає взагалі - нічого не робить (її треба
    додати в README вручну один раз)."""
    if not os.path.exists(README):
        return False
    with open(README, encoding="utf-8") as f:
        content = f.read()

    esc_name = re.escape(filename)

    wrapped = re.compile(r'(<a href=")[^"]*("\s*>\s*<img[^>]*assets/' + esc_name + r'[^>]*>\s*</a>)')
    new_content, n = wrapped.subn(lambda m: m.group(1) + link + m.group(2), content)

    if not n:
        bare = re.compile(r'(<img[^>]*assets/' + esc_name + r'[^>]*/?>)')
        new_content, n = bare.subn(lambda m: f'<a href="{link}">{m.group(1)}</a>', content, count=1)

    if n and new_content != content:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def text_w(s, fs):
    return len(s) * fs * CHAR_W


def wrap_to_width(s, fs, max_w):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if text_w(trial, fs) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


STYLE = """<style>
text{font-family:'Courier New',Consolas,monospace}
.s{animation-name:tw;animation-iteration-count:infinite;animation-timing-function:ease-in-out}
@keyframes tw{0%,100%{opacity:.12}50%{opacity:1}}
.glow{filter:url(#glow)}
</style>"""

DEFS = """<defs>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="txt" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff3399"/><stop offset=".5" stop-color="#c77dff"/><stop offset="1" stop-color="#7b9cff"/></linearGradient>
<linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff3399"/><stop offset="1" stop-color="#7b2ff7"/></linearGradient>
<linearGradient id="fadeL" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#7b2ff7" stop-opacity="0"/><stop offset="1" stop-color="#c77dff" stop-opacity=".9"/></linearGradient>
<linearGradient id="fadeR" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#c77dff" stop-opacity=".9"/><stop offset="1" stop-color="#7b2ff7" stop-opacity="0"/></linearGradient>
<radialGradient id="nebV"><stop offset="0" stop-color="#7b2ff7" stop-opacity=".35"/><stop offset="1" stop-color="#7b2ff7" stop-opacity="0"/></radialGradient>
</defs>"""


def stars(seed, w, h, n):
    import random
    r = random.Random(seed)
    out = []
    for _ in range(n):
        x = r.uniform(8, w - 8)
        y = r.uniform(0, h)
        rad = r.choice([.6, .8, 1, 1.3, 1.6])
        col = r.choice(["#fff", "#ffd6ec", "#d9c8ff", "#c3e4ff"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rad}" fill="{col}" class="s" '
                    f'style="animation-delay:{r.uniform(0,4):.2f}s;animation-duration:{r.uniform(2,5):.2f}s"/>')
    return "\n".join(out)


def heading(y, text, fs=24, ls=6):
    def star4(x, y, r, fill="#ff3399"):
        return (f'<path d="M{x},{y-r} Q{x},{y} {x+r},{y} Q{x},{y} {x},{y+r} '
                f'Q{x},{y} {x-r},{y} Q{x},{y} {x},{y-r} Z" fill="{fill}"/>')
    cw = fs * 0.6 + ls
    half = len(text) * cw / 2
    sx1, sx2 = 500 - half - 26, 500 + half + 26
    ly = y - fs * 0.32
    return (f'<text x="500" y="{y}" text-anchor="middle" font-size="{fs}" font-weight="bold" '
            f'letter-spacing="{ls}" fill="url(#txt)">{escape(text)}</text>'
            + star4(sx1, ly, 8) + star4(sx2, ly, 8)
            + f'<rect x="{sx1-12-150}" y="{ly-.75}" width="150" height="1.5" fill="url(#fadeL)"/>'
            + f'<rect x="{sx2+12}" y="{ly-.75}" width="150" height="1.5" fill="url(#fadeR)"/>')


def chip(x, y, l, r, cl, cr, wl, wr):
    return (f'<rect x="{x}" y="{y}" width="{wl}" height="24" rx="4" fill="{cl}"/>'
            f'<rect x="{x+wl}" y="{y}" width="{wr}" height="24" rx="4" fill="{cr}"/>'
            f'<rect x="{x+wl-6}" y="{y}" width="8" height="24" fill="{cr}"/>'
            f'<text x="{x+wl/2}" y="{y+17}" text-anchor="middle" font-size="12" font-weight="bold" fill="#fff">{escape(l)}</text>'
            f'<text x="{x+wl+wr/2}" y="{y+17}" text-anchor="middle" font-size="12" font-weight="bold" fill="#fff">{escape(r)}</text>')


def build_one(cfg, seed, with_heading):
    name, desc, status, tech = cfg["name"], cfg["description"], cfg["status"], cfg["tech"]

    MAX_CARD_W = 860
    MIN_CARD_W = 500
    LEFT_OFF = 82
    RIGHT_PAD = 40

    name_fs, name_min_fs = 30, 17
    ideal_w = text_w(name, name_fs) + LEFT_OFF + RIGHT_PAD
    card_w = max(MIN_CARD_W, min(MAX_CARD_W, ideal_w))
    avail = card_w - LEFT_OFF - RIGHT_PAD
    if text_w(name, name_fs) > avail:
        name_fs = max(name_min_fs, name_fs * avail / text_w(name, name_fs))

    # опис: намагаємось в один рядок, інакше зменшуємо шрифт, інакше переносимо -
    # без обмеження кількості рядків (ніколи не обрізаємо текст користувача мовчки)
    desc_fs, desc_min_fs = 17, 13
    desc_lines = [desc]
    if text_w(desc, desc_fs) > avail:
        shrunk_fs = max(desc_min_fs, desc_fs * avail / text_w(desc, desc_fs))
        if text_w(desc, shrunk_fs) <= avail:
            desc_fs = shrunk_fs
        else:
            desc_fs = desc_min_fs
            desc_lines = wrap_to_width(desc, desc_fs, avail)

    card_x = 500 - card_w / 2
    text_x = card_x + LEFT_OFF
    icon_x = card_x + 46

    extra_h = max(0, len(desc_lines) - 1) * (desc_fs + 8)

    # чіпи: рахуємо ЗАЗДАЛЕГІДЬ, чи влазять поруч, щоб висота картки одразу
    # враховувала другий рядок чіпів (а не "росла" вже після того як рамка намальована)
    status_w = max(70, len(status) * 8 + 24)
    tech_w = max(70, len(tech) * 8 + 24)
    chips_total = 72 + status_w + 30 + 56 + tech_w
    chips_wrap = text_x + chips_total > card_x + card_w - RIGHT_PAD / 2

    # підстраховка: якщо навіть один чіп (TECH або STATUS) не влазить у картку
    # навіть на своєму окремому рядку - розширюємо картку під нього (в межах MAX_CARD_W)
    if chips_wrap:
        widest_chip = max(72 + status_w, 56 + tech_w)
        needed_w = LEFT_OFF + widest_chip + RIGHT_PAD
        if needed_w > card_w:
            card_w = min(MAX_CARD_W, needed_w)
            card_x = 500 - card_w / 2
            text_x = card_x + LEFT_OFF
            icon_x = card_x + 46

    card_h = 150 + extra_h + (32 if chips_wrap else 0)
    top_pad = 72 if with_heading else 40
    card_y = top_pad + 36
    H = card_y + card_h + 50

    body = ""
    if with_heading:
        body += heading(72, "CURRENTLY WORKING ON")

    body += (f'<rect x="{card_x:.1f}" y="{card_y}" width="{card_w:.1f}" height="{card_h:.1f}" rx="18" '
             f'fill="#120726" stroke="url(#bar)" stroke-width="2"/>')
    body += (f'<path transform="translate({icon_x:.1f},{card_y+58}) scale(0.9)" '
             f'd="M6,-22 L-12,4 L-1,4 L-6,22 L12,-4 L1,-4 Z" fill="#ffd166" class="glow"/>')
    body += f'<text x="{text_x:.1f}" y="{card_y+64}" font-size="{name_fs:.1f}" font-weight="bold" fill="#ff3399">{escape(name)}</text>'

    dy = card_y + 96
    for line in desc_lines:
        body += f'<text x="{text_x:.1f}" y="{dy}" font-size="{desc_fs:.1f}" fill="#c9b6ff">{escape(line)}</text>'
        dy += desc_fs + 8

    chip_y = card_y + 116 + extra_h
    if chips_wrap:
        body += chip(text_x, chip_y, "STATUS", status, "#3a3350", "#ff69b4", 72, status_w)
        body += chip(text_x, chip_y + 32, "TECH", tech, "#3a3350", "#7b2ff7", 56, tech_w)
    else:
        body += chip(text_x, chip_y, "STATUS", status, "#3a3350", "#ff69b4", 72, status_w)
        body += chip(text_x + 72 + status_w + 30, chip_y, "TECH", tech, "#3a3350", "#7b2ff7", 56, tech_w)

    nebs = f'<ellipse cx="500" cy="{card_y+40}" rx="{card_w/2+60:.0f}" ry="120" fill="url(#nebV)"/>'

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {H}" width="1000" height="{H}">\n'
           f'{STYLE}\n{DEFS}\n'
           f'<rect width="1000" height="{H}" fill="#0a0418"/>\n{nebs}\n'
           f'{stars(seed, 1000, H, 40)}\n'
           f'<rect x="0" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'<rect x="998" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'{body}\n</svg>')
    return svg


def build():
    configs = read_configs()
    for i, cfg in enumerate(configs):
        svg = build_one(cfg, seed=21 + i, with_heading=(i == 0))
        path, filename = out_path(i)
        with open(path, "w", encoding="utf-8") as f:
            f.write(svg)
        update_readme_link(filename, cfg["link"])


if __name__ == "__main__":
    build()
