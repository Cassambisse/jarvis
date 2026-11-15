# JARVIS - scarica le notizie dai feed RSS e crea news.json
# Viene eseguito da GitHub Actions in automatico (vedi .github/workflows/notizie.yml)
import json, re, html, urllib.request, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FONTI = {
    "prime":   ["https://www.ansa.it/sito/ansait_rss.xml"],
    "cronaca": ["https://www.ansa.it/sito/notizie/cronaca/cronaca_rss.xml"],
    "abruzzo": ["https://www.ansa.it/abruzzo/notizie/abruzzo_rss.xml"],
}
# le notizie che citano questi luoghi vanno in cima alla sezione Abruzzo
VICINI = ["notaresco", "teramo", "teramano", "roseto", "giulianova", "atri", "pineto", "mosciano",
          "castellalto", "cellino", "morro d'oro", "bellante", "silvi", "montorio", "campli", "val vomano"]

def pulisci(t):
    t = html.unescape(re.sub(r"<[^>]+>", " ", t or ""))
    return re.sub(r"\s+", " ", t).strip()

def leggi(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (JARVIS personale)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        root = ET.fromstring(r.read())
    out = []
    for it in root.iter("item"):
        titolo = pulisci(it.findtext("title"))
        if not titolo:
            continue
        data = it.findtext("pubDate") or ""
        try:
            dt = parsedate_to_datetime(data)
            ora = dt.astimezone().strftime("%d/%m %H:%M")
            ts = dt.timestamp()
        except Exception:
            ora, ts = "", 0
        out.append({"titolo": titolo, "descrizione": pulisci(it.findtext("description"))[:220],
                    "link": (it.findtext("link") or "").strip(), "ora": ora, "ts": ts})
    return out

sezioni = {}
for nome, urls in FONTI.items():
    voci = []
    for u in urls:
        try:
            voci += leggi(u)
        except Exception as e:
            print("Fonte non raggiungibile:", u, e)
    visti, unici = set(), []
    for v in sorted(voci, key=lambda x: x["ts"], reverse=True):
        if v["titolo"] not in visti:
            visti.add(v["titolo"]); unici.append(v)
    if nome == "abruzzo":
        unici.sort(key=lambda x: not any(p in (x["titolo"] + " " + x["descrizione"]).lower() for p in VICINI))
    sezioni[nome] = unici[:10]

with open("news.json", "w", encoding="utf-8") as f:
    json.dump({"aggiornato": datetime.now(timezone.utc).isoformat(), "sezioni": sezioni}, f, ensure_ascii=False, indent=1)
print({k: len(v) for k, v in sezioni.items()})
