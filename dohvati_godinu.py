import re, urllib.request, urllib.parse

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

PREDMETI_KLJUCEVI = [
    ("hrvatsk", "hrj"),
    ("englesk", "eng"),
    ("fizik", "fiz"),
    ("kemij", "kem"),
    ("povijes", "pov"),
    ("geograf", "geo"),
    ("biolog", "bio"),
    ("informat", "inf"),
]

def preuzmi_html(url):
    req = urllib.request.Request(url, headers=HEADERS)
    return urllib.request.urlopen(req, timeout=25).read().decode("utf-8", errors="ignore")

def dohvati_azoo_godinu(godina):
    prethodna = godina - 1
    upiti = [f"{prethodna}./{godina}.", f"natjecanja {godina}"]
    pronadjene_stranice = set()
    rezultati = {}

    for u in upiti:
        q = urllib.parse.quote_plus(u)
        for str_br in range(1, 6):
            url_pretrage = f"https://azoo.hr{str_br}/?s={q}"
            try:
                html = preuzmi_html(url_pretrage)
            except Exception:
                break

            linkovi_clanaka = re.findall(
                r'href="(https://www\.azoo\.hr/natjecanja-i-smotre-arhiva/[^"]+)"',
                html
            )
            if not linkovi_clanaka:
                break

            for link in linkovi_clanaka:
                if str(godina) in link or str(prethodna) in link:
                    pronadjene_stranice.add(link)

    print(f"Pronađeno {len(pronadjene_stranice)} AZOO stranica za {godina}. godinu. Izvlačim ZIP/PDF datoteke...")

    for stranica in sorted(pronadjene_stranice):
        try:
            html = preuzmi_html(stranica)
        except Exception as e:
            print(f"  [GREŠKA] {stranica}: {e}")
            continue

        naslov_m = re.search(r"<title>(.*?)</title>", html, flags=re.I | re.S)
        naslov = (naslov_m.group(1) if naslov_m else stranica).lower()

        predmet = ""
        for kljuc, sifra_p in PREDMETI_KLJUCEVI:
            if kljuc in naslov:
                predmet = sifra_p
                break
        if not predmet:
            continue

        if "drzav" in naslov or "držav" in naslov:
            razina = "drz"
        elif "zupan" in naslov or "župan" in naslov:
            razina = "zup"
        elif "skolsk" in naslov or "školsk" in naslov:
            razina = "sko"
        else:
            razina = "sve"

        datoteke = re.findall(r'href="(https?://[^"]+\.(?:zip|pdf))"', html, flags=re.I)
        for d in datoteke:
            sifra = f"{predmet}-{godina}" if razina == "sve" else f"{predmet}-{razina}-{godina}"
            rezultati[d] = sifra

    return rezultati

def dohvati_matematiku_godinu(godina):
    baza = f"http://antonija-horvatek.from.hr{godina}/{godina}"
    kandidati = [
        (f"os-mat-sko-{godina}", f"{baza}-OS-skolsko-45678-zad+rj/{godina}-OS-skolsko-45678-zad.pdf"),
        (f"os-mat-sko-{godina}-rj", f"{baza}-OS-skolsko-45678-zad+rj/{godina}-OS-skolsko-45678-rj.pdf"),
        (f"os-mat-zup-{godina}", f"{baza}-OS-zupanijsko-45678-zad+rj/{godina}-OS-zupanijsko-45678-zad.pdf"),
        (f"os-mat-zup-{godina}-rj", f"{baza}-OS-zupanijsko-45678-zad+rj/{godina}-OS-zupanijsko-45678-rj.pdf"),
        (f"os-mat-drz-{godina}", f"{baza}-OS-drzavno-5678-zad+rj/{godina}-OS-drzavno-5678-zad.pdf"),
        (f"os-mat-drz-{godina}-rj", f"{baza}-OS-drzavno-5678-zad+rj/{godina}-OS-drzavno-5678-rj.pdf"),
        (f"ss-mat-sko-{godina}-A", f"{baza}-SS-skolsko-1234-zad+rj/{godina}-SS-skolsko-A-1234-zad.pdf"),
        (f"ss-mat-sko-{godina}-A-rj", f"{baza}-SS-skolsko-1234-zad+rj/{godina}-SS-skolsko-A-1234-rj.pdf"),
        (f"ss-mat-sko-{godina}-B", f"{baza}-SS-skolsko-1234-zad+rj/{godina}-SS-skolsko-B-1234-zad.pdf"),
        (f"ss-mat-sko-{godina}-B-rj", f"{baza}-SS-skolsko-1234-zad+rj/{godina}-SS-skolsko-B-1234-rj.pdf"),
        (f"ss-mat-zup-{godina}-A", f"{baza}-SS-zupanijsko-1234-zad+rj/{godina}-SS-zupanijsko-A-1234-zad.pdf"),
        (f"ss-mat-zup-{godina}-A-rj", f"{baza}-SS-zupanijsko-1234-zad+rj/{godina}-SS-zupanijsko-A-1234-rj.pdf"),
        (f"ss-mat-zup-{godina}-B", f"{baza}-SS-zupanijsko-1234-zad+rj/{godina}-SS-zupanijsko-B-1234-zad.pdf"),
        (f"ss-mat-zup-{godina}-B-rj", f"{baza}-SS-zupanijsko-1234-zad+rj/{godina}-SS-zupanijsko-B-1234-rj.pdf"),
        (f"ss-mat-drz-{godina}-A", f"{baza}-SS-drzavno-1234-zad+rj/{godina}-SS-drzavno-A-1234-zad.pdf"),
        (f"ss-mat-drz-{godina}-A-rj", f"{baza}-SS-drzavno-1234-zad+rj/{godina}-SS-drzavno-A-1234-rj.pdf"),
        (f"ss-mat-drz-{godina}-B", f"{baza}-SS-drzavno-1234-zad+rj/{godina}-SS-drzavno-B-1234-zad.pdf"),
        (f"ss-mat-drz-{godina}-B-rj", f"{baza}-SS-drzavno-1234-zad+rj/{godina}-SS-drzavno-B-1234-rj.pdf"),
    ]
    valjani = {}
    for sifra, url in kandidati:
        try:
            req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
            if urllib.request.urlopen(req, timeout=10).status == 200:
                valjani[url] = sifra
        except Exception:
            pass
    return valjani

god = int(input("Koju godinu želiš povući (npr. 2025)? ").strip())
print(f"Pretražujem AZOO i Matematiku za {god}. godinu...")

azoo = dohvati_azoo_godinu(god)
mat = dohvati_matematiku_godinu(god)

postojeci = set()
try:
    for l in open("linkovi.txt", encoding="utf-8"):
        if l.strip() and not l.startswith("#"):
            postojeci.add(l.split(maxsplit=1).pop().strip())
except FileNotFoundError:
    pass

novi_redovi = []
for url, sifra in {**mat, **azoo}.items():
    if url not in postojeci:
        novi_redovi.append(f"{sifra} {url}")

with open("linkovi.txt", "a", encoding="utf-8") as out:
    out.write("\n" + "\n".join(novi_redovi) + "\n")

print(f"Dodano {len(novi_redovi)} novih linkova za {god}. godinu u linkovi.txt!")
