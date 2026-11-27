import os
import io
import re
import json
import zipfile
import urllib.request

MAPA_PDF = "pdf"
DATOTEKA_LINKOVI = "linkovi.txt"
DATOTEKA_POPIS = "popis.json"

os.makedirs(MAPA_PDF, exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def prepoznaj_naziv_iz_zipa(bazna_sifra, unutarnja_putanja):
    cisto_ime = os.path.basename(unutarnja_putanja)
    bez_ekst = os.path.splitext(cisto_ime)[0].lower()
    puna_putanja = unutarnja_putanja.lower()

    dijelovi_sifre = bazna_sifra.split("-")
    ima_razred_u_sifri = bool(re.match(r"^([1-8]rs?|[os]s)$", dijelovi_sifre[0]))

    razred = dijelovi_sifre[0] if ima_razred_u_sifri else ""
    ostatak_sifre = "-".join(dijelovi_sifre[1:]) if ima_razred_u_sifri else bazna_sifra

    if not razred:
        m_raz = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:skupin|raz|r\b|_r|-r|a\b|b\b)", puna_putanja)
        if m_raz:
            broj = m_raz.group(1)
            if broj in ["1", "2", "3", "4"] and "mat" not in bazna_sifra.lower():
                razred = f"{broj}rs"
            else:
                je_ss = any(k in puna_putanja for k in ["skupina", "rsš", "rss", "ss", "srednj", "gimn", "struk"])
                razred = f"{broj}{'rs' if je_ss else 'r'}"
        else:
            je_ss = any(k in puna_putanja for k in ["skupina", "rsš", "rss", "ss", "srednj", "gimn", "struk"])
            razred = "ss" if je_ss else "os"

    varijanta = ""
    if re.search(r"(?:^|[^a-z0-9])(2\s*a|4\s*a|kat\s*a|kategorija\s*a|varijanta\s*a|_a\b|-a\b)", puna_putanja):
        varijanta = "-A"
    elif re.search(r"(?:^|[^a-z0-9])(2\s*b|4\s*b|kat\s*b|kategorija\s*b|varijanta\s*b|_b\b|-b\b)", puna_putanja):
        varijanta = "-B"
    elif re.search(r"(?:^|[^a-z0-9])(lista\s*c|list\s*c|kat\s*c|kategorija\s*c|_c\b|-c\b)", puna_putanja):
        varijanta = "-C"

    je_prakticni = any(k in bez_ekst for k in ["eksp", "praktičn", "prakticn"])
    je_rj = bool(
        any(k in bez_ekst for k in ["rjes", "rješ", "rj_", "_rj", "-rj", "key", "odgovor", "kljuc", "ključ", "ispravak"])
        or re.search(r"(?:_r\b|_r_|2026-2$)", bez_ekst)
    )

    dodatak = ""
    if any(k in bez_ekst for k in ["answer sheet", "answer_sheet", "answer-sheet", "list_za", "list-za", "obrazac"]):
        dodatak = "-list"
    elif any(k in bez_ekst for k in ["transkript", "transcript", "slusanje", "slušanje"]):
        dodatak = "-transkript"
    elif je_prakticni and je_rj:
        dodatak = "-prakticni-rj"
    elif je_prakticni:
        dodatak = "-prakticni"
    elif je_rj:
        dodatak = "-rj"

    return f"{razred}-{ostatak_sifre}{varijanta}{dodatak}.pdf"


def obradi_zip(zip_bytes, bazna_sifra):
    with zipfile.ZipFile(zip_bytes) as zf:
        for unutarnje_ime in zf.namelist():
            if unutarnje_ime.startswith("__MACOSX") or unutarnje_ime.endswith("/"):
                continue

            donje_ime = unutarnje_ime.lower()

            if donje_ime.endswith(".zip"):
                obradi_zip(io.BytesIO(zf.read(unutarnje_ime)), bazna_sifra)
                continue

            if not donje_ime.endswith(".pdf"):
                continue

            ciljno_ime = prepoznaj_naziv_iz_zipa(bazna_sifra, unutarnje_ime)
            ciljna_putanja = os.path.join(MAPA_PDF, ciljno_ime)

            brojac = 2
            while os.path.exists(ciljna_putanja):
                baza, ekst = os.path.splitext(ciljno_ime)
                ciljna_putanja = os.path.join(MAPA_PDF, f"{baza}-{brojac}{ekst}")
                brojac += 1

            with open(ciljna_putanja, "wb") as out:
                out.write(zf.read(unutarnje_ime))
            print(f"[OK ZIP] {os.path.basename(unutarnje_ime)} -> {os.path.basename(ciljna_putanja)}")


if os.path.exists(DATOTEKA_LINKOVI):
    with open(DATOTEKA_LINKOVI, "r", encoding="utf-8") as f:
        linije = [linija.strip() for linija in f if linija.strip() and not linija.startswith("#")]

    for linija in linije:
        dijelovi = linija.split(maxsplit=1)
        if len(dijelovi) != 2:
            continue

        sifra, url = dijelovi

        if url.lower().endswith(".zip"):
            dijelovi_s = sifra.split("-")
            kljuc_provjere = "-".join(dijelovi_s[1:]) if re.match(r"^([1-8]rs?|[os]s)$", dijelovi_s[0]) else sifra
            vec_skinuto = any(kljuc_provjere in f for f in os.listdir(MAPA_PDF))

            if vec_skinuto:
                print(f"[VEĆ POSTOJI] {sifra}")
                continue

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=30) as odgovor:
                    zip_podaci = io.BytesIO(odgovor.read())
                obradi_zip(zip_podaci, sifra)
            except Exception as e:
                print(f"[GREŠKA ZIP] {sifra} -> {e}")

        else:
            putanja_glavna = os.path.join(MAPA_PDF, f"{sifra}.pdf")
            if os.path.exists(putanja_glavna):
                continue
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as odgovor:
                    with open(putanja_glavna, "wb") as out:
                        out.write(odgovor.read())
                print(f"[OK] Preuzeto: {sifra}.pdf")
            except Exception as e:
                print(f"[GREŠKA] {sifra}.pdf -> {e}")

svi_pdfovi = sorted([f for f in os.listdir(MAPA_PDF) if f.lower().endswith(".pdf")])
with open(DATOTEKA_POPIS, "w", encoding="utf-8") as out:
    json.dump(svi_pdfovi, out, ensure_ascii=False, indent=2)

print(f"\nAžuriran {DATOTEKA_POPIS} (ukupno PDF-ova: {len(svi_pdfovi)})")
