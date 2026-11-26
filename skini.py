import os
import io
import json
import zipfile
import urllib.request

MAPA_PDF = "pdf"
DATOTEKA_LINKOVI = "linkovi.txt"
DATOTEKA_POPIS = "popis.json"

os.makedirs(MAPA_PDF, exist_ok=True)
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

if os.path.exists(DATOTEKA_LINKOVI):
    with open(DATOTEKA_LINKOVI, "r", encoding="utf-8") as f:
        linije = [linija.strip() for linija in f if linija.strip() and not linija.startswith("#")]

    for linija in linije:
        dijelovi = linija.split(maxsplit=1)
        if len(dijelovi) != 2:
            continue

        sifra, url = dijelovi
        putanja_glavna = os.path.join(MAPA_PDF, f"{sifra}.pdf")

        # Ako je link ZIP arhiva
        if url.lower().endswith(".zip"):
            if os.path.exists(putanja_glavna):
                print(f"[VEĆ POSTOJI] {sifra}.pdf (iz ZIP-a)")
                continue

            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as odgovor:
                    zip_podaci = io.BytesIO(odgovor.read())

                with zipfile.ZipFile(zip_podaci) as zf:
                    pdf_u_zipu = [
                        ime for ime in zf.namelist()
                        if ime.lower().endswith(".pdf") and not ime.startswith("__MACOSX")
                    ]

                    if not pdf_u_zipu:
                        print(f"[UPOZORENJE] Nema PDF-a u ZIP-u: {sifra}")
                        continue

                    for unutarnje_ime in pdf_u_zipu:
                        cisto_ime = os.path.basename(unutarnje_ime).lower()
                        # Prepoznaje je li datoteka rješenje ili ispit
                        je_rjesenje = any(kljuc in cisto_ime for kljuc in ["rjes", "rješ", "rj_", "_rj", "-rj", "key", "odgovor"])
                        ciljno_ime = f"{sifra}-rj.pdf" if je_rjesenje else f"{sifra}.pdf"
                        ciljna_putanja = os.path.join(MAPA_PDF, ciljno_ime)

                        with open(ciljna_putanja, "wb") as out:
                            out.write(zf.read(unutarnje_ime))
                        print(f"[OK ZIP] Raspakirano: {ciljno_ime}")

            except Exception as e:
                print(f"[GREŠKA ZIP] {sifra} -> {e}")

        # Ako je link obični PDF
        else:
            if os.path.exists(putanja_glavna):
                continue
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as odgovor:
                    with open(putanja_glavna, "wb") as out:
                        out.write(odgovor.read())
                print(f"[OK] Preuzeto: {sifra}.pdf")
            except Exception as e:
                print(f"[GREŠKA] {sifra}.pdf -> {e}")

svi_pdfovi = sorted([f for f in os.listdir(MAPA_PDF) if f.lower().endswith(".pdf")])
with open(DATOTEKA_POPIS, "w", encoding="utf-8") as out:
    json.dump(svi_pdfovi, out, ensure_ascii=False, indent=2)

print(f"\nAžuriran {DATOTEKA_POPIS} (ukupno PDF-ova: {len(svi_pdfovi)})")
