import os
import json
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
        putanja = os.path.join(MAPA_PDF, f"{sifra}.pdf")
        if not os.path.exists(putanja):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=15) as odgovor:
                    with open(putanja, "wb") as out:
                        out.write(odgovor.read())
                print(f"[OK] Preuzeto: {sifra}.pdf")
            except Exception as e:
                print(f"[GREŠKA] {sifra}.pdf -> {e}")

svi_pdfovi = sorted([f for f in os.listdir(MAPA_PDF) if f.lower().endswith(".pdf")])
with open(DATOTEKA_POPIS, "w", encoding="utf-8") as out:
    json.dump(svi_pdfovi, out, ensure_ascii=False, indent=2)

print(f"Ažuriran {DATOTEKA_POPIS} (ukupno PDF-ova: {len(svi_pdfovi)})")
