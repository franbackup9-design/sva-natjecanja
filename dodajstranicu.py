import os
import re
import urllib.request
from urllib.parse import urljoin, unquote

DATOTEKA_LINKOVI = "linkovi.txt"
GODINA = "2026"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

PREDMETI = {
    "hrvatsk": "hrj",
    "englesk": "eng",
    "matemat": "mat",
    "fizik": "fiz",
    "kemij": "kem",
    "povijest": "pov",
    "geograf": "geo",
    "biolog": "bio",
    "informat": "inf",
}


def obradi_stranicu(url_stranice):
    req = urllib.request.Request(url_stranice, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    m_title = re.search(r"<title>(.*?)</title>", html, flags=re.IGNORECASE | re.DOTALL)
    naslov = m_title.group(1) if m_title else ""
    kontekst = (naslov + " " + unquote(url_stranice)).lower()

    predmet = next((sifra for kljuc, sifra in PREDMETI.items() if kljuc in kontekst), "predmet")
    razina = "drz" if any(k in kontekst for k in ["drzav", "držav", "drz", "drž"]) else (
        "zup" if any(k in kontekst for k in ["zupan", "župan", "zup", "žup"]) else "sko"
    )

    parovi = re.findall(
        r'<a[^>]+href=["\']([^"\']*(?:\.zip|\.pdf|dobavi-dokument)[^"\']*)["\'][^>]*>(.*?)</a>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    postojeci_urlovi = set()
    linije = []
    if os.path.exists(DATOTEKA_LINKOVI):
        with open(DATOTEKA_LINKOVI, "r", encoding="utf-8") as f:
            for l in f:
                cista = l.strip()
                if cista:
                    linije.append(cista)
                    dijelovi = cista.split(maxsplit=1)
                    if len(dijelovi) == 2:
                        postojeci_urlovi.add(dijelovi[1])

    dodano = 0
    for href, tekst_html in parovi:
        puni_url = urljoin(url_stranice, href)
        if puni_url in postojeci_urlovi:
            continue

        tekst = re.sub(r"<[^>]+>", " ", tekst_html).strip()
        sve = (kontekst + " " + tekst + " " + unquote(puni_url)).lower()

        if any(k in sve for k in ["propozicij", "vremenik", "rezultat", "upute", "popis", "prijevoz", "smjestaj", "smještaj", "pozvan", "katalog"]):
            continue

        je_ss = any(k in sve for k in ["ss", "sš", "srednj", "gimn", "struk", "skupin", "1a", "1b", "2a", "2b", "3a", "3b", "4a", "4b"])
        m_raz = re.search(r"(?:^|[^0-9])([1-8])\s*\.?\s*(?:raz|r\b|_r|-r|skupin)", sve)
        razred = f"{m_raz.group(1)}{'rs' if je_ss else 'r'}" if m_raz else ""

        varijanta = ""
        if re.search(r"(?:^|[^a-z0-9])(varijanta\s*a|kat\s*a|_a\b|-a\b)", sve):
            varijanta = "-A"
        elif re.search(r"(?:^|[^a-z0-9])(varijanta\s*b|kat\s*b|_b\b|-b\b)", sve):
            varijanta = "-B"

        je_rj = puni_url.lower().endswith(".pdf") and any(k in sve for k in ["rjes", "rješ", "rj", "odgovor", "kljuc", "ključ"])
        prefiks = f"{razred}-" if razred else ""
        sifra = f"{prefiks}{predmet}-{razina}-{GODINA}{varijanta}{'-rj' if je_rj else ''}"

        linije.append(f"{sifra} {puni_url}")
        postojeci_urlovi.add(puni_url)
        dodano += 1
        print(f"[DODANO] {sifra} -> {puni_url}")

    with open(DATOTEKA_LINKOVI, "w", encoding="utf-8") as f:
        f.write("\n".join(linije) + "\n")

    print(f"\nUkupno dodano {dodano} novih linkova u {DATOTEKA_LINKOVI}!")


if __name__ == "__main__":
    while True:
        unos = input("\nZalijepi link stranice (ili 'kraj' za izlaz): ").strip()
        if not unos or unos.lower() == "kraj":
            break
        try:
            obradi_stranicu(unos)
        except Exception as e:
            print(f"[GREŠKA] {e}")
