"""Перемальовує assets/project.svg на основі .github/project.txt"""
import os
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CFG = os.path.join(ROOT, ".github", "project.txt")
OUT = os.path.join(ROOT, "assets", "project.svg")

DEFAULTS = {
    "name": "Project Name Here",
    "description": "Short description of what you are building right now",
    "status": "In Progress",
    "tech": "ESP32 | C++",
}


def read_config():
    cfg = dict(DEFAULTS)
    if os.path.exists(CFG):
        with open(CFG, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or ":" not in line:
                    continue
                key, _, val = line.partition(":")
                key = key.strip().lower()
                val = val.strip()
                if key in cfg and val:
                    cfg[key] = val
    return cfg


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


def build():
    cfg = read_config()
    H = 300
    name = cfg["name"]
    desc = cfg["description"]
    status = cfg["status"]
    tech = cfg["tech"]

    body = heading(72, "CURRENTLY WORKING ON")
    body += ('<rect x="180" y="108" width="640" height="150" rx="18" fill="#120726" stroke="url(#bar)" stroke-width="2"/>'
             '<path transform="translate(226,166)" d="M6,-22 L-12,4 L-1,4 L-6,22 L12,-4 L1,-4 Z" fill="#ffd166" class="glow"/>')
    body += f'<text x="262" y="172" font-size="30" font-weight="bold" fill="#ff3399">{escape(name)}</text>'
    body += f'<text x="262" y="204" font-size="17" fill="#c9b6ff">{escape(desc)}</text>'

    status_w = max(70, len(status) * 8 + 24)
    tech_w = max(70, len(tech) * 8 + 24)
    body += chip(262, 224, "STATUS", status, "#3a3350", "#ff69b4", 72, status_w)
    body += chip(262 + 72 + status_w + 30, 224, "TECH", tech, "#3a3350", "#7b2ff7", 56, tech_w)

    nebs = '<ellipse cx="500" cy="150" rx="420" ry="120" fill="url(#nebV)"/>'

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {H}" width="1000" height="{H}">\n'
           f'{STYLE}\n{DEFS}\n'
           f'<rect width="1000" height="{H}" fill="#0a0418"/>\n{nebs}\n'
           f'{stars(21, 1000, H, 40)}\n'
           f'<rect x="0" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'<rect x="998" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'{body}\n</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    build()
