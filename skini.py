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
    if len(txt.strip()) < 25:
        return True
    lose = (
        "competizione", "competizioni", "такмичење", "такимичење", "таkмичење", "шkолсkо",
        "решења", "verseny", "soutěž", "listić sa zaporkom", "poveznice na snimke",
        "dopune rješenja", "tablica s bodovima", "obrazac - 1 prijava",
        "ljestvica konačnog poretka", "privremena ljestvica", "globe škola",
        "crvenog križa", "izvješće sa", ".wav", "transekt", "hrvatsko kemijsko društvo",
        "obrazac za prijavu", "suglasnost roditelja", "vremenik natjecanja"
    )
    if any(k in txt for k in lose):
        return True
    return any(k in ime_low for k in (
        "pozvan", "ljestvic", "poredak", "prijevoz", "autobus", "pravila",
        "upute_za_provedbu", "upute-za-provedbu", "globe", "hck", "vremenik", "program"
    ))

def odredi_razred(predmet, prvi_dio, txt, ime_low):
    if re.match(r"^([1-8]rs?|os|ss)$", prvi_dio):
        return prvi_dio

    if predmet == "geo" and any(k in txt for k in ("a-kategorija", "a kategorija", "b-kategorija", "b kategorija", "strukovnih i umjetničkih")):
        return "ss"

    if predmet == "bio":
        for s, r in (("1. skupina", "7r"), ("2. skupina", "8r"), ("3. skupina", "1rs"), ("4. skupina", "2rs"), ("5. skupina", "3rs"), ("6. skupina", "4rs")):
            if s in txt:
                return r

    if predmet == "pov":
        if any(k in txt for k in ("1. kategorija", "1. skupina", "skupina 1")): return "7r"
        if any(k in txt for k in ("2. kategorija", "2. skupina", "skupina 2")): return "8r"
        if any(k in txt for k in ("3. kategorija", "3. skupina", "skupina 3")): return "1rs"
        if any(k in txt for k in ("4. kategorija", "4. skupina", "skupina 4")): return "2rs"
        if any(k in txt for k in ("5. kategorija", "5. skupina", "skupina 5")): return "3rs"
        if any(k in txt for k in ("6. kategorija", "6. skupina", "skupina 6")): return "4rs"

    if predmet == "fiz":
        for g, r in (("1. grupa", "1rs"), ("2. grupa", "2rs"), ("3. grupa", "3rs"), ("4. grupa", "4rs")):
            if g in txt:
                return r

    pravila_razreda = (
        (r"\b(?:8\s*\.\s*(?:razred|r\b)|osmi\s+razred|viii\s*\.\s*(?:razred|r\b)|8os)\b", "8r"),
        (r"\b(?:7\s*\.\s*(?:razred|r\b)|sedmi\s+razred|vii\s*\.\s*(?:razred|r\b)|7os)\b", "7r"),
        (r"\b(?:6\s*\.\s*(?:razred|r\b)|šesti\s+razred|vi\s*\.\s*(?:razred|r\b)|6os)\b", "6r"),
        (r"\b(?:5\s*\.\s*(?:razred|r\b)|peti\s+razred|v\s*\.\s*(?:razred|r\b)|5os)\b", "5r"),
        (r"\b(?:4\s*\.\s*(?:razred|r\b)|četvrti\s+razred|iv\s*\.\s*(?:razred|r\b)|razred:\s*4|razred:\s*četvrti|4ss)\b", "4rs"),
        (r"\b(?:3\s*\.\s*(?:razred|r\b)|treći\s+razred|iii\s*\.\s*(?:razred|r\b)|razred:\s*3|razred:\s*treći|3ss)\b", "3rs"),
        (r"\b(?:2\s*\.\s*(?:razred|r\b)|drugi\s+razred|ii\s*\.\s*(?:razred|r\b)|razred:\s*2|razred:\s*drugi|2ss)\b", "2rs"),
        (r"\b(?:1\s*\.\s*(?:razred|r\b)|prvi\s+razred|i\s*\.\s*(?:razred|r\b)|razred:\s*1|razred:\s*prvi|1ss)\b", "1rs"),
    )
    for uzorak, r in pravila_razreda:
        if re.search(uzorak, txt):
            return r

    je_os_tekst = any(k in txt for k in ("osnovn", "o. š.", "o.š.", "7os", "8os"))
    je_ss_tekst = any(k in txt for k in ("srednj", "gimnazij", "strukovn", "1ss", "2ss", "3ss", "4ss"))
    ignoriraj_iza = r"(?!\s*(?:zadatak|dio|svjetsk|stolj|mjesto|dan|put|kolo|list))"

    if je_os_tekst:
        if re.search(rf"\b(8|viii)\s*\.{ignoriraj_iza}", txt): return "8r"
        if re.search(rf"\b(7|vii)\s*\.{ignoriraj_iza}", txt): return "7r"
        if re.search(rf"\b(6|vi)\s*\.{ignoriraj_iza}", txt): return "6r"
        if re.search(rf"\b(5|v)\s*\.{ignoriraj_iza}", txt): return "5r"

    if je_ss_tekst:
        if re.search(rf"\b(4|iv)\s*\.{ignoriraj_iza}", txt): return "4rs"
        if re.search(rf"\b(3|iii)\s*\.{ignoriraj_iza}", txt): return "3rs"
        if re.search(rf"\b(2|ii)\s*\.{ignoriraj_iza}", txt): return "2rs"
        if re.search(rf"\b(1|i)\s*\.{ignoriraj_iza}", txt): return "1rs"

    m = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r)", ime_low)
    if m:
        br = m.group(1)
        je_ss = (br in ("1", "2", "3", "4") and predmet != "mat") or any(k in ime_low for k in ("ss", "sš", "srednj", "skupin"))
        return f"{br}{'rs' if je_ss else 'r'}"

    return "ss" if (je_ss_tekst or any(k in ime_low for k in ("ss", "sš", "srednj", "gimnazij"))) else "os"

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
    if "drz" in svi_d or any(k in spojeno for k in ("državno natjecanje", "drzavno natjecanje", "državna razina", "drzavna razina")):
        razina = "drz"
    elif "zup" in svi_d or any(k in spojeno for k in ("županijsko natjecanje", "zupanijsko natjecanje", "županijska razina", "zupanijska razina")):
        razina = "zup"
    else:
        razina = "sko"

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
        if "sudionik natjecanja" in txt or "uspjeh na natjecanju" in txt:
            je_list = False
            je_rj = False
        else:
            je_rj = "rješenja pisane zadaće" in txt
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
    if not zipfile.is_zipfile(podaci):
        return
    podaci.seek(0)
    with zipfile.ZipFile(podaci) as zf:
        for f in zf.namelist():
            if f.startswith("__MACOSX") or f.endswith("/"):
                continue
            if f.lower().endswith(".zip"):
                raspakiraj(io.BytesIO(zf.read(f)), sifra)
            elif f.lower().endswith(".pdf"):
                spremi(zf.read(f), sifra, os.path.basename(f))

with open("linkovi.txt", encoding="utf-8") as f:
    for linija in f:
        linija = linija.strip()
        if not linija or linija.startswith("#"):
            continue
        sifra, url = linija.split(maxsplit=1)
        dijelovi = sifra.split("-")
        god = dijelovi.pop() if dijelovi else ""
        svi_d = sifra.split("-")
        pred = next((p for p in ("hrj", "eng", "mat", "fiz", "kem", "pov", "geo", "bio", "inf") if p in svi_d), "")

        if god in ("2026", "2025", "2024", "2023") or pred == "mat":
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