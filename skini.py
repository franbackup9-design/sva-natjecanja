import os, io, re, json, zipfile, urllib.request

MAPA = "pdf"
os.makedirs(MAPA, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}

def ime_iz_zipa(sifra, putanja):
    ime = os.path.basename(putanja).lower()
    puna = putanja.lower()
    dijelovi = sifra.split("-")
    prvi = dijelovi[0]

    # 1. Razred: ako ga već nema u šifri (npr. "hrj-zup-2026"), izvuci ga iz naziva datoteke/mape
    if re.match(r"^([1-8]rs?|os|ss)$", prvi):
        razred = prvi
        ostatak = "-".join(dijelovi[1:])
    else:
        ostatak = sifra
        m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r|a\b|b\b)", puna)
        if m:
            br = m.group(1)
            je_ss = (br in ["1", "2", "3", "4"] and "mat" not in sifra) or any(
                k in puna for k in ["ss", "sš", "srednj", "gimn", "struk", "skupin"]
            )
            razred = f"{br}{'rs' if je_ss else 'r'}"
        else:
            razred = "ss" if any(k in puna for k in ["ss", "sš", "srednj"]) else "os"

    # 2. Varijanta (A, B)
    var = ""
    if re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*a(?:[^a-z0-9]|$)", puna) and "eng" in sifra:
        var = "-A"
    elif re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*b(?:[^a-z0-9]|$)", puna) and "eng" in sifra:
        var = "-B"

    # 3. Tip dokumenta (zadaci, rješenja, transkript, list)
    if any(k in ime for k in ["answer sheet", "answer_sheet", "list_za", "list-za", "obrazac"]):
        tip = "-list"
    elif any(k in ime for k in ["transkript", "transcript"]):
        tip = "-transkript"
    elif any(k in ime for k in ["rjes", "rješ", "rj_", "_rj", "-rj", "key", "odgovor", "kljuc", "ključ"]) or re.search(r"_r\b|_r_", ime):
        tip = "-rj"
    else:
        tip = ""

    return f"{razred}-{ostatak}{var}{tip}.pdf"

def raspakiraj(podaci_zipa, sifra):
    with zipfile.ZipFile(podaci_zipa) as zf:
        for f in zf.namelist():
            if f.startswith("__MACOSX") or f.endswith("/"):
                continue
            if f.lower().endswith(".zip"):
                raspakiraj(io.BytesIO(zf.read(f)), sifra)
            elif f.lower().endswith(".pdf"):
                novo_ime = ime_iz_zipa(sifra, f)
                put = os.path.join(MAPA, novo_ime)
                n = 2
                while os.path.exists(put):
                    b, e = os.path.splitext(novo_ime)
                    put = os.path.join(MAPA, f"{b}-{n}{e}")
                    n += 1
                open(put, "wb").write(zf.read(f))
                print(f"  + {os.path.basename(put)}")

with open("linkovi.txt", encoding="utf-8") as f:
    for linija in f:
        linija = linija.strip()
        if not linija or linija.startswith("#"):
            continue
        sifra, url = linija.split(maxsplit=1)
        if not url.lower().endswith(".zip") and os.path.exists(os.path.join(MAPA, f"{sifra}.pdf")):
            continue
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            podaci = urllib.request.urlopen(req, timeout=30).read()
            if url.lower().endswith(".zip"):
                print(f"[ZIP] {sifra}")
                raspakiraj(io.BytesIO(podaci), sifra)
            else:
                open(os.path.join(MAPA, f"{sifra}.pdf"), "wb").write(podaci)
                print(f"[PDF] {sifra}.pdf")
        except Exception as e:
            print(f"[GREŠKA] {sifra}: {e}")

pdfovi = sorted(x for x in os.listdir(MAPA) if x.lower().endswith(".pdf"))
json.dump(pdfovi, open("popis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nGotovo! Ukupno PDF-ova: {len(pdfovi)}")
