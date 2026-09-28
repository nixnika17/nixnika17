"""Оновлює assets/middle.svg реальною статистикою контрибуцій з GitHub."""
import json, os, urllib.request
from datetime import date, datetime, timedelta

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
TEMPLATE = "assets/middle.template.svg"
OUTPUT = "assets/middle.svg"


def gql(query, variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise RuntimeError(data["errors"])
    return data["data"]


def fetch_days():
    created = gql("query($l:String!){user(login:$l){createdAt}}", {"l": USER})["user"]["createdAt"]
    first_year = int(created[:4])
    now = datetime.utcnow()
    q = """query($l:String!,$f:DateTime!,$t:DateTime!){user(login:$l){
      contributionsCollection(from:$f,to:$t){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"""
    days = {}
    for y in range(first_year, now.year + 1):
        f = f"{y}-01-01T00:00:00Z"
        t = now.strftime("%Y-%m-%dT%H:%M:%SZ") if y == now.year else f"{y}-12-31T23:59:59Z"
        cal = gql(q, {"l": USER, "f": f, "t": t})["user"]["contributionsCollection"]["contributionCalendar"]
        for w in cal["weeks"]:
            for d in w["contributionDays"]:
                days[d["date"]] = d["contributionCount"]
    return days


def fmt(d, year=False):
    return f"{d.strftime('%b')} {d.day}" + (f", {d.year}" if year else "")


def rng(a, b, today):
    end = "Present" if b == today else fmt(b)
    return fmt(a) if a == b and b != today else f"{fmt(a)} - {end}"


def compute(days, today=None):
    today = today or date.today()
    items = sorted((date.fromisoformat(k), v) for k, v in days.items() if date.fromisoformat(k) <= today)
    total = sum(v for _, v in items)
    first = next((d for d, v in items if v > 0), today)
    # longest
    best = (0, None, None)
    run, start, prev = 0, None, None
    for d, v in items:
        if v > 0:
            if run and prev and (d - prev).days == 1:
                run += 1
            else:
                run, start = 1, d
            if run > best[0]:
                best = (run, start, d)
        else:
            run = 0
        prev = d
    # current (today may still be empty)
    cmap = {d: v for d, v in items}
    cur_end = today if cmap.get(today, 0) > 0 else today - timedelta(days=1)
    n, d = 0, cur_end
    while cmap.get(d, 0) > 0:
        n += 1
        d -= timedelta(days=1)
    cur_start = d + timedelta(days=1)
    return {
        "@@TOTAL@@": str(total),
        "@@TOTAL_RANGE@@": f"{fmt(first, True)} - Present",
        "@@CUR@@": str(n),
        "@@CUR_RANGE@@": rng(cur_start, cur_end, today) if n else fmt(today),
        "@@LONGEST@@": str(best[0]),
        "@@LONGEST_RANGE@@": rng(best[1], best[2], today) if best[0] else "-",
    }


def render(values):
    s = open(TEMPLATE, encoding="utf-8").read()
    for k, v in values.items():
        s = s.replace(k, v)
    open(OUTPUT, "w", encoding="utf-8").write(s)


if __name__ == "__main__":
    render(compute(fetch_days()))
