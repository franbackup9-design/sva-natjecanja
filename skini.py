import os, io, re, json, hashlib, zipfile, subprocess, urllib.request

MAPA = "pdf"
os.makedirs(MAPA, exist_ok=True)
HEADERS = {"User-Agent": "Mozilla/5.0"}

# Učitaj sve već objavljene datoteke iz popis.json (uključujući i one koje su već na GitHubu, a obrisane s diska)
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

def je_nebitan_dokument(txt, ime_low):
    zabranjeni_tekstovi = [
        "competizione", "такмичење", "такимичење", "решења", "verseny", "soutěž",
        "listić sa zaporkom", "poveznice na snimke", "dopune rješenja",
        "tablica s bodovima", "obrazac - 1 prijava"
    ]
    if any(k in txt for k in zabranjeni_tekstovi):
        return True
    if any(k in ime_low for k in ["pozvan", "ljestvic", "poredak", "prijevoz", "autobus", "pravila"]):
        return True
    return False

def odredi_razred(predmet, dijelovi_sifre, txt, ime_low):
    prvi = dijelovi_sifre[0] if dijelovi_sifre else ""
    if re.match(r"^([1-8]rs?|os|ss)$", prvi):
        return prvi

    if predmet == "geo" and any(k in txt for k in ["a-kategorija", "a kategorija", "b-kategorija", "b kategorija", "strukovnih i umjetničkih"]):
        return "ss"

    if predmet == "bio":
        if "1. skupina" in txt or "7. razred" in txt: return "7r"
        if "2. skupina" in txt or "8. razred" in txt: return "8r"
        if "3. skupina" in txt or "1. razred" in txt: return "1rs"
        if "4. skupina" in txt or "2. razred" in txt: return "2rs"
        if "5. skupina" in txt or "3. razred" in txt: return "3rs"
        if "6. skupina" in txt or "4. razred" in txt: return "4rs"

    if predmet == "pov":
        if any(k in txt for k in ["1. kategorija", "1. skupina", "vii.", "7. razred", "sedmi"]): return "7r"
        if any(k in txt for k in ["2. kategorija", "2. skupina", "viii.", "8. razred", "osmi"]): return "8r"
        if any(k in txt for k in ["3. kategorija", "3. skupina", "i. razred", "1. razred", "prvi"]): return "1rs"
        if any(k in txt for k in ["4. kategorija", "4. skupina", "ii. razred", "2. razred", "drugi"]): return "2rs"
        if any(k in txt for k in ["5. kategorija", "5. skupina", "iii. razred", "3. razred", "treći"]): return "3rs"
        if any(k in txt for k in ["6. kategorija", "6. skupina", "iv. razred", "4. razred", "četvrti"]): return "4rs"

    if any(k in txt for k in ["5. razred", "5.razred", "peti razred"]): return "5r"
    if any(k in txt for k in ["6. razred", "6.razred", "šesti razred"]): return "6r"
    if any(k in txt for k in ["7. razred", "7.razred", "sedmi razred", "vii. razred", "7os"]): return "7r"
    if any(k in txt for k in ["8. razred", "8.razred", "osmi razred", "viii. razred", "8os"]): return "8r"
    if any(k in txt for k in ["1. razred", "1.razred", "prvi razred", "i. razred", "razred: 1", "razred: prvi", "1ss", "1. skupina"]): return "1rs"
    if any(k in txt for k in ["2. razred", "2.razred", "drugi razred", "ii. razred", "razred: 2", "razred: drugi", "2ss", "2. skupina"]): return "2rs"
    if any(k in txt for k in ["3. razred", "3.razred", "treći razred", "iii. razred", "razred: 3", "razred: treći", "3ss", "3. skupina"]): return "3rs"
    if any(k in txt for k in ["4. razred", "4.razred", "četvrti razred", "iv. razred", "razred: 4", "razred: četvrti", "4ss", "4. skupina"]): return "4rs"

    m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r)", ime_low)
    if m:
        br = m.group(1)
        je_ss = (br in ["1", "2", "3", "4"] and predmet != "mat") or any(k in ime_low for k in ["ss", "sš", "srednj", "skupin"])
        return f"{br}{'rs' if je_ss else 'r'}"

    return "ss" if any(k in f"{ime_low} {txt}" for k in ["srednje škole", "srednjih škola", "gimnazij", "strukovn", "ss", "sš"]) else "os"

def prepoznaj_iz_sadrzaja(putanja_pdf, bazna_sifra, izvorno_ime):
    ime_low = izvorno_ime.lower()
    dijelovi = bazna_sifra.split("-")
    godina = dijelovi[-1]

    predmet = ""
    for p in ["hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf"]:
        if p in dijelovi:
            predmet = p
            break

    try:
        txt = subprocess.check_output(["pdftotext", "-l", "2", putanja_pdf, "-"], stderr=subprocess.DEVNULL).decode("utf-8", errors="ignore").lower()
    except Exception:
        txt = ""

    if je_nebitan_dokument(txt, ime_low):
        return None

    spojeno = f"{ime_low} {txt}"

    # 1. Razina
    if "drz" in dijelovi or any(k in spojeno for k in ["državno natjecanje", "drzavno natjecanje", "državna razina", "drzavna razina", "državna smotra"]):
        razina = "drz"
    elif "zup" in dijelovi or any(k in spojeno for k in ["županijsko natjecanje", "zupanijsko natjecanje", "županijska razina", "zupanijska razina"]):
        razina = "zup"
    else:
        razina = "sko"

    # 2. Razred
    razred = odredi_razred(predmet, dijelovi, txt, ime_low)

    # 3. Kategorija A / B
    var = ""
    if predmet == "geo" and razred == "ss":
        if "a-kategorija" in txt or "a kategorija" in txt: var = "-A"
        elif "b-kategorija" in txt or "b kategorija" in txt: var = "-B"
    elif predmet in ["eng", "mat"]:
        if re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*b(?:[^a-z0-9]|$)", ime_low): var = "-B"
        elif re.search(r"(?:^|[^a-z0-9])(2|4)?\s*[\._-]?\s*a(?:[^a-z0-9]|$)", ime_low): var = "-A"

    # 4. Tip dokumenta
    je_list = any(k in ime_low for k in ["answer sheet", "answer_sheet", "list_za", "list-za", "obrazac"]) or ("obrazac za odgovore" in txt) or ("list za odgovore" in txt)
    je_trans = any(k in ime_low for k in ["transkript", "transcript"]) or ("slušanje s razumijevanjem" in txt)
    je_prakt = any(k in ime_low for k in ["eksp", "prakt"]) or any(k in txt for k in ["pokus", "provjera geografskih vještina", "eksperimentalni zadatak"])

    if predmet == "bio":
        if "sudionik natjecanja" in txt or "uspjeh na natjecanju" in txt:
            je_list = False
            je_rj = False
        else:
            je_rj = "rješenja pisane zadaće" in txt
    elif predmet == "hrj":
        je_rj = ("rješenja i bodovanje" in txt) or ("bodovanje ispitnih zadataka" in txt)
    elif predmet == "pov":
        je_rj = any(k in txt for k in ["rješenja testa", "rješenja za", "rješenja ispita", "odgovori –", "odgovori |"])
    elif predmet == "kem":
        je_rj = any(k in txt for k in ["rješenja", "rješe nj a", "rj eš en ja"])
    elif predmet == "fiz" and je_prakt:
        je_rj = "rješenje" in txt or "rješenja" in txt
    else:
        je_rj = ("-rj" in bazna_sifra) or (any(k in spojeno for k in ["rješenja", "točni odgovori", "ključ za odgovore", "smjernice za bodovanje", "answer key"]) and "zaporka" not in txt)

    if je_list: tip = "-list"
    elif je_trans: tip = "-transkript"
    elif je_prakt and je_rj: tip = "-prakticni-rj"
    elif je_prakt: tip = "-prakticni"
    elif je_rj: tip = "-rj"
    else: tip = ""

    return f"{razred}-{predmet}-{razina}-{godina}{var}{tip}.pdf"

def spremi_pametno(sadrzaj_bytes, bazna_sifra, izvorno_ime):
    otisak = (len(sadrzaj_bytes), hashlib.md5(sadrzaj_bytes).hexdigest())
    if otisak in postojeci_otisci:
        return

    tmp_put = os.path.join(MAPA, "_temp_provjera.pdf")
    open(tmp_put, "wb").write(sadrzaj_bytes)

    zeljeno_ime = prepoznaj_iz_sadrzaja(tmp_put, bazna_sifra, izvorno_ime)
    if not zeljeno_ime or zeljeno_ime in stari_popis or os.path.exists(os.path.join(MAPA, zeljeno_ime)):
        os.remove(tmp_put)
        return

    put = os.path.join(MAPA, zeljeno_ime)
    os.rename(tmp_put, put)
    postojeci_otisci.add(otisak)
    print(f"  + {zeljeno_ime}")

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
        dijelovi = sifra.split("-")
        god = dijelovi[-1]
        pred = next((p for p in ["hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf"] if p in dijelovi), "")

        # Preskoči ako su ta godina i taj predmet već u popis.json (da ne skida ponovno ono što je već na GitHubu)
        if pred and any(f"-{pred}-" in x and f"-{god}" in x for x in stari_popis):
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
