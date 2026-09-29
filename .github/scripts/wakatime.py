"""Малює assets/wakatime.svg на основі публічних даних WakaTime (без сторонніх сервісів).

Період беремо той, який сам WakaTime готовий віддати публічно (залежить від
налаштування "Display code time publicly" в профілі й від тарифного плану -
безкоштовні акаунти зберігають детальну статистику по мовах лише за короткий
період, повна історія за весь час доступна тільки на Premium)."""
import json
import os
import urllib.error
import urllib.request
from html import escape

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "assets", "wakatime.svg")

WAKA_USER = "2c21fab2-044d-474d-96bf-3bcf013cc7ed"
# без range в шляху - WakaTime сам віддасть той період, який дозволяє тариф/налаштування приватності
API_URL = f"https://wakatime.com/api/v1/users/{WAKA_USER}/stats/?is_including_today=true"

STYLE = """<style>
text{font-family:'Courier New',Consolas,monospace}
.s{animation-name:tw;animation-iteration-count:infinite;animation-timing-function:ease-in-out}
@keyframes tw{0%,100%{opacity:.12}50%{opacity:1}}
.glow{filter:url(#glow)}
.bar{animation:grow 1.2s ease-out forwards;transform-origin:left}
@keyframes grow{from{transform:scaleX(0)}to{transform:scaleX(1)}}
</style>"""

DEFS = """<defs>
<filter id="glow" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation="4" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
<linearGradient id="txt" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff3399"/><stop offset=".5" stop-color="#c77dff"/><stop offset="1" stop-color="#7b9cff"/></linearGradient>
<linearGradient id="barfill" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#ff3399"/><stop offset="1" stop-color="#7b2ff7"/></linearGradient>
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


def heading(y, text, fs=22, ls=5):
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


def fetch_data():
    req = urllib.request.Request(API_URL, headers={"User-Agent": "profile-readme-bot"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.load(resp)


def build():
    langs, range_label, error = [], "RECENT ACTIVITY", None
    try:
        payload = fetch_data()
        data = payload.get("data", {}) or {}
        langs = [l for l in (data.get("languages") or [])
                  if l.get("text") and l.get("total_seconds", 0) > 0][:6]
        range_label = (data.get("human_readable_range") or "RECENT ACTIVITY").upper()
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "ignore")[:300]
        except Exception:
            body = ""
        error = f"HTTP {e.code}: {body}"
        print("WakaTime API error:", error)
    except Exception as e:
        error = str(e)
        print("WakaTime fetch failed:", error)

    ROW_H = 34
    TOP = 100
    n = len(langs) if langs else 1
    H = TOP + n * ROW_H + 50

    body = heading(60, f"WAKATIME ANALYTICS · {range_label}")
    body += '<rect x="60" y="82" width="880" height="2" fill="url(#barfill)" opacity=".25"/>'

    if not langs:
        if error:
            msg = "waiting for data - check the Action log for details"
        else:
            msg = "no public language data for this period yet"
        body += f'<text x="500" y="{TOP+30}" text-anchor="middle" font-size="15" fill="#7b9cff">{escape(msg)}</text>'
    else:
        max_pct = max(l.get("percent", 0) for l in langs) or 1
        name_w = 150
        bar_x = 100 + name_w
        bar_max_w = 620
        for i, l in enumerate(langs):
            y = TOP + i * ROW_H
            name = l.get("name", "?")
            human = l.get("text", "")
            pct = l.get("percent", 0)
            w = max(4, bar_max_w * (pct / max_pct))
            body += f'<text x="90" y="{y+15}" font-size="14" font-weight="bold" fill="#ff7fc4" text-anchor="end">{escape(name)}</text>'
            body += f'<rect x="{bar_x}" y="{y+2}" width="{bar_max_w}" height="14" rx="7" fill="#1d0f3d"/>'
            body += (f'<rect class="bar" x="{bar_x}" y="{y+2}" width="{w:.1f}" height="14" rx="7" '
                      f'fill="url(#barfill)" style="animation-delay:{i*0.12:.2f}s"/>')
            body += f'<text x="{bar_x+bar_max_w+14}" y="{y+15}" font-size="13" fill="#c9b6ff">{escape(human)}</text>'

    nebs = '<ellipse cx="500" cy="120" rx="460" ry="130" fill="url(#nebV)"/>'
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 {H}" width="1000" height="{H}">\n'
           f'{STYLE}\n{DEFS}\n'
           f'<rect width="1000" height="{H}" fill="#0a0418"/>\n{nebs}\n'
           f'{stars(31, 1000, H, 45)}\n'
           f'<rect x="0" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'<rect x="998" y="0" width="2" height="{H}" fill="#5a26b8"/>'
           f'{body}\n</svg>')
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)


if __name__ == "__main__":
    build()
