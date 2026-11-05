"""Päivittää polls.json-tiedoston Wikipedian mittauskoosteesta.

Hakee uusimman Taloustutkimuksen (Yle) ja Verianin (HS) eduskuntavaalimittauksen
sivulta "Opinion polling for the 2027 Finnish parliamentary election" ja kirjoittaa
ne polls.json-tiedostoon, jos keruujakso on uudempi kuin tiedostossa jo oleva.

Käyttö:  python scripts/update_polls.py [polls.json] [--html tiedosto.html]
Palauttaa: tulostaa "UPDATED" tai "NO CHANGE".
"""
import datetime as dt
import json
import math
import re
import sys
import urllib.request

from bs4 import BeautifulSoup

WIKI_TITLE = "Opinion_polling_for_the_2027_Finnish_parliamentary_election"
WIKI_URL = f"https://en.wikipedia.org/wiki/{WIKI_TITLE}"
RENDER_URL = f"https://en.wikipedia.org/w/index.php?title={WIKI_TITLE}&action=render"
USER_AGENT = "hallituspohjat-updater/1.0 (static site poll updater)"

# Wikipedian sarake -> sivun puoluetunnus
COLS = {"KOK": "KOK", "PS": "PS", "SDP": "SDP", "KESK": "KESK", "VAS": "VAS",
        "VIHR": "VIHR", "SFP": "RKP", "RKP": "RKP", "KD": "KD", "LIIK": "LIIK"}
PARTIES = ["SDP", "PS", "KOK", "KESK", "VAS", "VIHR", "RKP", "KD", "LIIK"]
FIRMS = {"yle": "taloustutkimus", "hs": "verian"}
MONTHS = {m: i for i, m in enumerate(
    ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"], 1)}


def fetch_html():
    req = urllib.request.Request(RENDER_URL, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def clean(cell):
    for sup in cell.find_all("sup"):
        sup.decompose()
    return " ".join(cell.get_text(" ", strip=True).split())


def num(text):
    m = re.search(r"\d+(?:[.,]\d+)?", text.replace(" ", "").replace(",", ""))
    return float(m.group()) if m else None


def parse_dates(text):
    """'15 Sep–19 Oct 2026' -> (start, end) date objects."""
    t = text.replace("–", "-").replace("—", "-").replace(" ", " ")
    parts = [p.strip() for p in t.split("-") if p.strip()]
    if len(parts) != 2:
        return None
    right = re.match(r"(\d{1,2})\s+([A-Za-z]{3})[a-z]*\.?\s+(\d{4})", parts[1])
    if not right:
        return None
    d2, m2, y2 = int(right.group(1)), MONTHS.get(right.group(2).lower()), int(right.group(3))
    left = re.match(r"(\d{1,2})(?:\s+([A-Za-z]{3})[a-z]*\.?)?(?:\s+(\d{4}))?", parts[0])
    if not left or not m2:
        return None
    d1 = int(left.group(1))
    m1 = MONTHS.get((left.group(2) or "").lower(), m2)
    y1 = int(left.group(3)) if left.group(3) else (y2 if m1 <= m2 else y2 - 1)
    return dt.date(y1, m1, d1), dt.date(y2, m2, d2)


def fi_range(start, end):
    left = f"{start.day}.{start.month}." + (f"{start.year}" if start.year != end.year else "")
    return f"{left}–{end.day}.{end.month}.{end.year}"


def latest_polls(html):
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for table in soup.find_all("table", class_="wikitable"):
        header = None
        for tr in table.find_all("tr"):
            cells = [clean(c) for c in tr.find_all(["th", "td"])]
            if header is None:
                if "SDP" in cells and "KOK" in cells:
                    header = cells
                continue
            if len(cells) < len(header) - 1:
                continue  # tapahtumarivit (yksi leveä solu)
            firm = cells[1].lower()
            key = next((k for k, f in FIRMS.items() if f in firm), None)
            if not key or key in found:
                continue
            dates = parse_dates(cells[0])
            if not dates:
                continue
            shares = {}
            for i, h in enumerate(header):
                pid = COLS.get(h.upper())
                if pid and i < len(cells):
                    v = num(cells[i])
                    if v is not None:
                        shares[pid] = round(v, 1)
            others = None
            if "Others" in header:
                others = num(cells[header.index("Others")])
            found[key] = {"dates": dates, "sample": num(cells[2]), "shares": shares, "others": others}
        if len(found) == len(FIRMS):
            break
    return found


def valid(p):
    s = p["shares"]
    if set(s) != set(PARTIES) or not all(0 <= v <= 60 for v in s.values()):
        return False
    total = sum(s.values()) + (p["others"] or 0)
    return 97.5 <= total <= 102.5


def end_of(entry):
    if entry.get("collectedEnd"):
        return dt.date.fromisoformat(entry["collectedEnd"])
    m = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\s*$", entry.get("collected", ""))
    return dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1))) if m else dt.date(1900, 1, 1)


def main():
    path = "polls.json"
    html = None
    args = sys.argv[1:]
    if "--html" in args:
        i = args.index("--html")
        html = open(args[i + 1], encoding="utf-8").read()
        args = args[:i] + args[i + 2:]
    if args:
        path = args[0]
    data = json.load(open(path, encoding="utf-8"))
    polls = latest_polls(html or fetch_html())
    for key, p in polls.items():
        print(f"FOUND {key}: {p['dates'][0]}–{p['dates'][1]} n={p['sample']} {p['shares']}")
    if not polls:
        print("WARNING: Wikipediasta ei löytynyt yhtään mittausriviä", file=sys.stderr)
    changed = []
    for key, p in polls.items():
        cur = data["polls"][key]
        start, end = p["dates"]
        if end <= end_of(cur):
            continue
        if not valid(p):
            print(f"SKIP {key}: luvut eivät läpäisseet tarkistusta {p['shares']}", file=sys.stderr)
            continue
        sample = int(p["sample"] or 2000)
        n = round(sample * 0.7)
        moe = 1.96 * math.sqrt(0.25 / n) * 100
        cur.update({
            "collected": fi_range(start, end),
            "collectedEnd": end.isoformat(),
            "published": "",
            "n": n,
            "nLabel": f"{sample:,} vastaajaa".replace(",", " "),
            "moe": f"virhemarginaali enintään noin ±{moe:.1f} %-yks. (laskennallinen)".replace(".", ",", 1),
            "note": "",
            "links": [{"title": "Wikipedian mittauskooste", "url": WIKI_URL}],
            "shares": {k: p["shares"][k] for k in PARTIES},
        })
        changed.append(key)
    if changed:
        data["updated"] = dt.date.today().isoformat()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print("UPDATED " + ",".join(changed))
    else:
        print("NO CHANGE")


if __name__ == "__main__":
    main()
