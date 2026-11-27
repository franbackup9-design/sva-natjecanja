import os, io, re, json, hashlib, zipfile, urllib.request

MAPA = "pdf"
os.makedirs(MAPA, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Zapamti otiske svih postojećih PDF-ova da se nijedan duplikat nikad ne zapiše
postojeci_otisci = set()
for f in os.listdir(MAPA):
    if f.lower().endswith(".pdf"):
        put = os.path.join(MAPA, f)
        postojeci_otisci.add(hashlib.md5(open(put, "rb").read()).hexdigest())

def ime_iz_zipa(sifra, putanja):
    ime = os.path.basename(putanja).lower()
    puna = putanja.lower()
    dijelovi = sifra.split("-")
    prvi = dijelovi.pop(0)
    ostatak_bez_prvog = "-".join(dijelovi)

    if sifra == "inf-2026":
        if any(k in puna for k in ["drzav", "držav", "drz", "drž"]):
            razina = "drz"
        elif any(k in puna for k in ["zupan", "župan", "zup", "žup"]):
            razina = "zup"
        else:
            razina = "sko"
        ostatak = f"inf-{razina}-2026"
    elif re.match(r"^([1-8]rs?|os|ss)$", prvi):
        ostatak = ostatak_bez_prvog
    else:
        ostatak = sifra

    if re.match(r"^([1-8]rs?|os|ss)$", prvi):
        razred = prvi
    else:
        m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r|a\b|b\b|os\b|ss\b)", puna)
        if m:
            br = m.group(1)
            je_ss = (br in ["1", "2", "3", "4"] and "mat" not in sifra) or any(
                k in puna for k in ["ss", "sš", "srednj", "gimn", "struk", "skupin"]
            )
            razred = f"{br}{'rs' if je_ss else 'r'}"
        elif re.search(r"(?:^|[^a-z])i\.\s*razred", puna):
            razred = "1rs"
        elif "geo" in sifra and re.search(r"(?:^|[^a-z0-9])(a|b)[_\s-]*(?:kategorija|ispit|rjesenja)", ime):
            razred = "ss"
        else:
            razred = "ss" if any(k in puna for k in ["ss", "sš", "srednj"]) else "os"

    var = ""
    if ("eng" in sifra or "geo" in sifra) and re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*a(?:[^a-z0-9]|$)", ime):
        var = "-A"
    elif ("eng" in sifra or "geo" in sifra) and re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*b(?:[^a-z0-9]|$)", ime):
        var = "-B"

    if any(k in ime for k in ["answer sheet", "answer_sheet", "list_za", "list-za", "obrazac"]):
        tip = "-list"
    elif any(k in ime for k in ["transkript", "transcript"]):
        tip = "-transkript"
    elif any(k in ime for k in ["rjes", "rješ", "rj_", "_rj", "-rj", "key", "odgovor", "kljuc", "ključ"]) or re.search(r"_r\b|_r_", ime):
        tip = "-rj"
    else:
        tip = ""

    return f"{razred}-{ostatak}{var}{tip}.pdf"

def spremi_bez_duplikata(sadrzaj_bytes, zeljeno_ime):
    otisak = hashlib.md5(sadrzaj_bytes).hexdigest()
    if otisak in postojeci_otisci:
        return

    put = os.path.join(MAPA, zeljeno_ime)
    n = 2
    while os.path.exists(put):
        b, e = os.path.splitext(zeljeno_ime)
        put = os.path.join(MAPA, f"{b}-{n}{e}")
        n += 1

    open(put, "wb").write(sadrzaj_bytes)
    postojeci_otisci.add(otisak)
    print(f"  + {os.path.basename(put)}")

def raspakiraj(podaci_zipa, sifra):
    with zipfile.ZipFile(podaci_zipa) as zf:
        for f in zf.namelist():
            if f.startswith("__MACOSX") or f.endswith("/"):
                continue
            if f.lower().endswith(".zip"):
                raspakiraj(io.BytesIO(zf.read(f)), sifra)
            elif f.lower().endswith(".pdf"):
                novo_ime = ime_iz_zipa(sifra, f)
                spremi_bez_duplikata(zf.read(f), novo_ime)

# Automatski očisti duple URL-ove u linkovi.txt prije skidanja
vidjeni_urlovi = set()
ciste_linije = []
with open("linkovi.txt", encoding="utf-8") as f:
    for linija in f:
        linija = linija.strip()
        if not linija or linija.startswith("#"):
            continue
        dijelovi = linija.split(maxsplit=1)
        if len(dijelovi) == 2:
            url_provjera = dijelovi.pop()
            if url_provjera not in vidjeni_urlovi:
                vidjeni_urlovi.add(url_provjera)
                ciste_linije.append(linija)

open("linkovi.txt", "w", encoding="utf-8").write("\n".join(ciste_linije) + "\n")

for linija in ciste_linije:
    sifra, url = linija.split(maxsplit=1)
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        podaci = urllib.request.urlopen(req, timeout=30).read()
        if url.lower().endswith(".zip"):
            print(f"[ZIP] {sifra}")
            raspakiraj(io.BytesIO(podaci), sifra)
        else:
            spremi_bez_duplikata(podaci, f"{sifra}.pdf")
    except Exception as e:
        print(f"[GREŠKA] {sifra}: {e}")

pdfovi = sorted(x for x in os.listdir(MAPA) if x.lower().endswith(".pdf"))
json.dump(pdfovi, open("popis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nGotovo! Ukupno jedinstvenih PDF-ova: {len(pdfovi)}")
