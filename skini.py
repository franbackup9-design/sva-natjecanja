import os, io, re, json, hashlib, zipfile, subprocess, urllib.request

MAPA = "pdf"
os.makedirs(MAPA, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Učitaj postojeći popis.json da NIKAD ne izgubimo već uploadane godine (npr. 2026.)
stari_popis = set()
if os.path.exists("popis.json"):
    try:
        stari_popis = set(json.load(open("popis.json", encoding="utf-8")))
    except Exception:
        pass

postojeci_otisci = set()
for f in os.listdir(MAPA):
    if f.lower().endswith(".pdf"):
        postojeci_otisci.add(hashlib.md5(open(os.path.join(MAPA, f), "rb").read()).hexdigest())

def prepoznaj_iz_sadrzaja(putanja_pdf, bazna_sifra, izvorno_ime):
    ime = izvorno_ime.lower()
    dijelovi = bazna_sifra.split("-")
    godina = dijelovi.pop()
    predmet = ""
    for p in ["hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf"]:
        if p in dijelovi:
            predmet = p
            break

    try:
        txt = subprocess.check_output(["pdftotext", "-l", "2", putanja_pdf, "-"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore").lower()
    except Exception:
        txt = ""

    spojeno = f"{ime} {txt}"

    # 1. Razina
    if "drz" in dijelovi or any(k in spojeno for k in ["državno natjecanje", "drzavno natjecanje", "državna razina", "drzavna razina"]):
        razina = "drz"
    elif "zup" in dijelovi or any(k in spojeno for k in ["županijsko natjecanje", "zupanijsko natjecanje", "županijska razina", "zupanijska razina"]):
        razina = "zup"
    else:
        razina = "sko"

    # 2. Razred
    razred = ""
    if dijelovi and re.match(r"^([1-8]rs?|os|ss)$", dijelovi[0]):
        razred = dijelovi[0]
    elif predmet == "geo" and any(k in txt for k in ["a-kategorija", "kategorija a", "b-kategorija", "kategorija b", "strukovnih i umjetničkih"]):
        razred = "ss"
    elif any(k in txt for k in ["5. razred", "5.razred", "peti razred"]): razred = "5r"
    elif any(k in txt for k in ["6. razred", "6.razred", "šesti razred"]): razred = "6r"
    elif any(k in txt for k in ["7. razred", "7.razred", "sedmi razred", "sedmi (vii.)", "7os"]): razred = "7r"
    elif any(k in txt for k in ["8. razred", "8.razred", "osmi razred", "osmi (viii.)", "8os"]): razred = "8r"
    elif any(k in txt for k in ["1. razred", "1.razred", "prvi razred", "prvi (i.)", "razred: 1", "razred: prvi", "1ss", "1. skupina"]): razred = "1rs"
    elif any(k in txt for k in ["2. razred", "2.razred", "drugi razred", "drugi (ii.)", "razred: 2", "razred: drugi", "2ss", "2. skupina"]): razred = "2rs"
    elif any(k in txt for k in ["3. razred", "3.razred", "treći razred", "treći (iii.)", "razred: 3", "razred: treći", "3ss", "3. skupina"]): razred = "3rs"
    elif any(k in txt for k in ["4. razred", "4.razred", "četvrti razred", "četvrti (iv.)", "razred: 4", "razred: četvrti", "4ss", "4. skupina"]): razred = "4rs"
    else:
        m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r)", ime)
        if m:
            br = m.group(1)
            je_ss = (br in ["1", "2", "3", "4"] and predmet != "mat") or any(k in ime for k in ["ss", "sš", "srednj", "skupin"])
            razred = f"{br}{'rs' if je_ss else 'r'}"
        else:
            razred = "ss" if any(k in spojeno for k in ["srednje škole", "srednjih škola", "gimnazij", "strukovn", "ss", "sš"]) else "os"

    # 3. Varijanta (A, B)
    var = ""
    if predmet in ["eng", "geo", "mat"]:
        if any(k in spojeno for k in ["b-kategorija", "kategorija b", "strukovnih"]) or re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*b(?:[^a-z0-9]|$)", ime):
            var = "-B"
        elif any(k in spojeno for k in ["a-kategorija", "kategorija a"]) or re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*a(?:[^a-z0-9]|$)", ime):
            var = "-A"

    # 4. Tip (zadaci, rješenja, praktični, transkript, list)
    je_rj = ("-rj" in bazna_sifra) or any(k in ime for k in ["rjes", "rješ", "rj_", "_rj", "-rj", "key", "odgovor", "kljuc", "ključ"]) or any(k in txt for k in ["rješenja i bodovanje", "bodovanje ispitnih zadataka", "točni odgovori", "rješenja"])
    je_prakt = ("pokus" in txt) or ("provjera geografskih vještina" in txt) or any(k in ime for k in ["eksp", "prakt"])

    if any(k in ime for k in ["answer sheet", "answer_sheet", "list_za", "list-za", "obrazac"]):
        tip = "-list"
    elif any(k in ime for k in ["transkript", "transcript"]):
        tip = "-transkript"
    elif je_prakt and je_rj:
        tip = "-prakticni-rj"
    elif je_prakt:
        tip = "-prakticni"
    elif je_rj:
        tip = "-rj"
    else:
        tip = ""

    return f"{razred}-{predmet}-{razina}-{godina}{var}{tip}.pdf"

def spremi_pametno(sadrzaj_bytes, bazna_sifra, izvorno_ime):
    otisak = hashlib.md5(sadrzaj_bytes).hexdigest()
    if otisak in postojeci_otisci:
        return

    tmp_put = os.path.join(MAPA, "_temp_provjera.pdf")
    open(tmp_put, "wb").write(sadrzaj_bytes)

    zeljeno_ime = prepoznaj_iz_sadrzaja(tmp_put, bazna_sifra, izvorno_ime)
    if zeljeno_ime in stari_popis:
        os.remove(tmp_put)
        return

    put = os.path.join(MAPA, zeljeno_ime)
    n = 2
    while os.path.exists(put) or os.path.basename(put) in stari_popis:
        b, e = os.path.splitext(zeljeno_ime)
        put = os.path.join(MAPA, f"{b}-{n}{e}")
        n += 1

    os.rename(tmp_put, put)
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
                spremi_pametno(zf.read(f), sifra, os.path.basename(f))

with open("linkovi.txt", encoding="utf-8") as f:
    for linija in f:
        linija = linija.strip()
        if not linija or linija.startswith("#"):
            continue
        sifra, url = linija.split(maxsplit=1)
        god = sifra.split("-").pop()
        if any(f"-{god}" in x for x in stari_popis):
            continue
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            podaci = urllib.request.urlopen(req, timeout=30).read()
            if url.lower().endswith(".zip"):
                print(f"[ZIP] {sifra}")
                raspakiraj(io.BytesIO(podaci), sifra)
            else:
                spremi_pametno(podaci, sifra, f"{sifra}.pdf")
        except Exception as e:
            print(f"[GREŠKA] {sifra}: {e}")

novi_pdfovi = set(x for x in os.listdir(MAPA) if x.lower().endswith(".pdf"))
svi_pdfovi = sorted(stari_popis | novi_pdfovi)
json.dump(svi_pdfovi, open("popis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nGotovo! Ukupno u popis.json: {len(svi_pdfovi)} (novih na disku: {len(novi_pdfovi)})")
