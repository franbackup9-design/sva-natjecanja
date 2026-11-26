import os
import urllib.request

MAPA_PDF = "pdf"
DATOTEKA_LINKOVI = "linkovi.txt"

os.makedirs(MAPA_PDF, exist_ok=True)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

with open(DATOTEKA_LINKOVI, "r", encoding="utf-8") as f:
    linije = [linija.strip() for linija in f if linija.strip() and not linija.startswith("#")]

uspjesno = 0
greske = 0

for linija in linije:
    dijelovi = linija.split(maxsplit=1)
    if len(dijelovi) != 2:
        print(f"[PRESKOČENO] Neispravan redak: {linija}")
        continue

    sifra, url = dijelovi
    putanja = os.path.join(MAPA_PDF, f"{sifra}.pdf")

    if os.path.exists(putanja):
        print(f"[VEĆ POSTOJI] {sifra}.pdf")
        continue

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as odgovor:
            with open(putanja, "wb") as out:
                out.write(odgovor.read())
        print(f"[OK] Preuzeto: {sifra}.pdf")
        uspjesno += 1
    except Exception as e:
        print(f"[GREŠKA] {sifra}.pdf -> {e}")
        greske += 1

print(f"\nGotovo! Novo preuzeto: {uspjesno} | Greške: {greske}")
