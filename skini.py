import os, io, re, json, hashlib, zipfile, subprocess, urllib.request

MAPA = "pdf"
os.makedirs(MAPA, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}

stari_popis = set()
if os.path.exists("popis.json"):
    try:
        stari_popis = set(json.load(open("popis.json", encoding="utf-8")))
    except Exception:
        pass

postojeci_otisci = set()
for f in os.listdir(MAPA):
    if f.lower().endswith(".pdf"):
        podaci = open(os.path.join(MAPA, f), "rb").read()
        postojeci_otisci.add((len(podaci), hashlib.md5(podaci).hexdigest()))

def je_nebitan(txt, ime_low):
    lose = (
        "competizione", "competizioni", "такмичење", "такимичење", "таkмичење", "шkолсkо",
        "решења", "verseny", "soutěž", "listić sa zaporkom", "poveznice na snimke",
        "dopune rješenja", "tablica s bodovima", "obrazac - 1 prijava",
        "ljestvica konačnog poretka", "privremena ljestvica", "globe škola",
        "crvenog križa", "izvješće sa", ".wav", "transekt 3", "hrvatsko kemijsko društvo"
    )
    if any(k in txt for k in lose):
        return True
    return any(k in ime_low for k in ("pozvan", "ljestvic", "poredak", "prijevoz", "autobus", "pravila", "upute_za_provedbu", "globe", "hck"))

def odredi_razred(predmet, prvi_dio, txt, ime_low):
    if re.match(r"^([1-8]rs?|os|ss)$", prvi_dio):
        return prvi_dio
    if predmet == "geo" and any(k in txt for k in ("a-kategorija", "a kategorija", "b-kategorija", "b kategorija", "strukovnih i umjetničkih")):
        return "ss"
    if predmet == "bio":
        for s, r in (("1. skupina", "7r"), ("2. skupina", "8r"), ("3. skupina", "1rs"), ("4. skupina", "2rs"), ("5. skupina", "3rs"), ("6. skupina", "4rs")):
            if s in txt: return r
    if predmet == "pov":
        if any(k in txt for k in ("1. kategorija", "1. skupina", "skupina 1", "vii.", "7. razred", "sedmi")): return "7r"
        if any(k in txt for k in ("2. kategorija", "2. skupina", "skupina 2", "viii.", "8. razred", "osmi")): return "8r"
        if any(k in txt for k in ("3. kategorija", "3. skupina", "skupina 3", "i. razred", "1. razred", "prvi")): return "1rs"
        if any(k in txt for k in ("4. kategorija", "4. skupina", "skupina 4", "ii. razred", "2. razred", "drugi")): return "2rs"
        if any(k in txt for k in ("5. kategorija", "5. skupina", "skupina 5", "iii. razred", "3. razred", "treći")): return "3rs"
        if any(k in txt for k in ("6. kategorija", "6. skupina", "skupina 6", "iv. razred", "4. razred", "četvrti")): return "4rs"
    if predmet == "fiz":
        for g, r in (("1. grupa", "1rs"), ("2. grupa", "2rs"), ("3. grupa", "3rs"), ("4. grupa", "4rs")):
            if g in txt: return r

    for uzorci, r in (
        (("8. razred", "8.razred", "osmi razred", "viii. razred", "8os"), "8r"),
        (("7. razred", "7.razred", "sedmi razred", "vii. razred", "7os"), "7r"),
        (("6. razred", "6.razred", "šesti razred"), "6r"),
        (("5. razred", "5.razred", "peti razred"), "5r"),
        (("4. razred", "4.razred", "četvrti razred", "iv. razred", "razred: 4", "razred: četvrti", "4ss"), "4rs"),
        (("3. razred", "3.razred", "treći razred", "iii. razred", "razred: 3", "razred: treći", "3ss"), "3rs"),
        (("2. razred", "2.razred", "drugi razred", "ii. razred", "razred: 2", "razred: drugi", "2ss"), "2rs"),
        (("1. razred", "1.razred", "prvi razred", "i. razred", "razred: 1", "razred: prvi", "1ss"), "1rs"),
    ):
        if any(k in txt for k in uzorci): return r

    m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r)", ime_low)
    if m:
        br = m.group(1)
        je_ss = (br in ("1", "2", "3", "4") and predmet != "mat") or any(k in ime_low for k in ("ss", "sš", "srednj", "skupin"))
        return f"{br}{'rs' if je_ss else 'r'}"
    return "ss" if any(k in f"{ime_low} {txt}" for k in ("srednje škole", "srednjih škola", "gimnazij", "strukovn", "ss", "sš")) else "os"

def prepoznaj(putanja_pdf, sifra, izvorno_ime):
    ime_low = izvorno_ime.lower()
    dijelovi = sifra.split("-")
    godina = dijelovi.pop() if dijelovi else ""
    prvi_dio = dijelovi.pop(0) if dijelovi else ""
    svi_d = sifra.split("-")
    predmet = next((p for p in ("hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf") if p in svi_d), "")

    try:
        txt = subprocess.check_output(["pdftotext", "-l", "2", putanja_pdf, "-"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore").lower()
    except Exception:
        txt = ""

    if je_nebitan(txt, ime_low):
        return None

    spojeno = f"{ime_low} {txt}"
    razina = "drz" if ("drz" in svi_d or any(k in spojeno for k in ("državno natjecanje", "drzavno natjecanje", "državna razina", "drzavna razina"))) else ("zup" if ("zup" in svi_d or any(k in spojeno for k in ("županijsko natjecanje", "zupanijsko natjecanje", "županijska razina", "zupanijska razina"))) else "sko")
    razred = odredi_razred(predmet, prvi_dio, txt, ime_low)

    var = ""
    if predmet == "geo" and razred == "ss":
        if "a-kategorija" in txt or "a kategorija" in txt: var = "-A"
        elif "b-kategorija" in txt or "b kategorija" in txt: var = "-B"
    elif predmet in ("eng", "mat"):
        if re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*b(?:[^a-z0-9]|$)", ime_low): var = "-B"
        elif re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*a(?:[^a-z0-9]|$)", ime_low): var = "-A"

    je_list = any(k in ime_low for k in ("answer sheet", "answer_sheet", "list_za", "list-za", "obrazac")) or ("obrazac za odgovore" in txt) or ("list za odgovore" in txt)
    je_trans = any(k in ime_low for k in ("transkript", "transcript")) or ("slušanje s razumijevanjem" in txt) or ("tapescript" in txt)
    je_prakt = any(k in ime_low for k in ("eksp", "prakt")) or any(k in txt for k in ("pokus", "provjera geografskih vještina", "eksperimentalni zadatak"))

    if predmet == "bio":
        je_list = False if ("sudionik natjecanja" in txt or "uspjeh na natjecanju" in txt) else je_list
        je_rj = False if ("sudionik natjecanja" in txt or "uspjeh na natjecanju" in txt) else ("rješenja pisane zadaće" in txt)
    elif predmet == "hrj":
        je_rj = ("rješenja i bodovanje" in txt) or ("bodovanje ispitnih zadataka" in txt)
    elif predmet == "pov":
        je_rj = any(k in txt for k in ("rješenja testa", "rješenja za", "rješenja ispita", "odgovori –", "odgovori |", "točni odgovori"))
    elif predmet == "kem":
        je_rj = any(k in txt for k in ("rješenja", "rješe nj a", "rj eš en ja"))
    elif predmet == "fiz" and je_prakt:
        je_rj = "rješenje" in txt or "rješenja" in txt
    else:
        je_rj = ("-rj" in sifra) or (any(k in spojeno for k in ("rješenja", "točni odgovori", "ključ za odgovore", "smjernice za bodovanje", "answer key")) and "zaporka" not in txt)

    tip = "-list" if je_list else ("-transkript" if je_trans else ("-prakticni-rj" if (je_prakt and je_rj) else ("-prakticni" if je_prakt else ("-rj" if je_rj else ""))))
    return f"{razred}-{predmet}-{razina}-{godina}{var}{tip}.pdf"

def spremi(sadrzaj, sifra, izvorno_ime):
    otisak = (len(sadrzaj), hashlib.md5(sadrzaj).hexdigest())
    if otisak in postojeci_otisci:
        return
    tmp = os.path.join(MAPA, "_tmp.pdf")
    open(tmp, "wb").write(sadrzaj)
    ime = prepoznaj(tmp, sifra, izvorno_ime)
    if not ime or ime in stari_popis or os.path.exists(os.path.join(MAPA, ime)):
        os.remove(tmp)
        return
    os.rename(tmp, os.path.join(MAPA, ime))
    postojeci_otisci.add(otisak)
    print(f"  + {ime}")

def raspakiraj(podaci, sifra):
    with zipfile.ZipFile(podaci) as zf:
        for f in zf.namelist():
            if f.startswith("__MACOSX") or f.endswith("/"): continue
            if f.lower().endswith(".zip"): raspakiraj(io.BytesIO(zf.read(f)), sifra)
            elif f.lower().endswith(".pdf"): spremi(zf.read(f), sifra, os.path.basename(f))

with open("linkovi.txt", encoding="utf-8") as f:
    for linija in f:
        linija = linija.strip()
        if not linija or linija.startswith("#"): continue
        sifra, url = linija.split(maxsplit=1)
        dijelovi = sifra.split("-")
        god = dijelovi.pop() if dijelovi else ""
        svi_d = sifra.split("-")
        pred = next((p for p in ("hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf") if p in svi_d), "")
        if god in ("2026", "2025", "2024") or pred == "mat":
            continue
        try:
            podaci = urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30).read()
            if url.lower().endswith(".zip"):
                print(f"[ZIP] {sifra}")
                raspakiraj(io.BytesIO(podaci), sifra)
            else:
                spremi(podaci, sifra, f"{sifra}.pdf")
        except Exception as e:
            print(f"[GREŠKA] {sifra}: {e}")

novi = set(x for x in os.listdir(MAPA) if x.lower().endswith(".pdf"))
svi = sorted(stari_popis | novi)
json.dump(svi, open("popis.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\nGotovo! Ukupno u popis.json: {len(svi)} (novih na disku: {len(novi)})")