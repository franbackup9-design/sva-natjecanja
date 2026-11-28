const PDF_FOLDER = "https://github.com/franbackup9-design/sva-natjecanja/raw/main/pdf";

const naziviPredmeta = {
  hrj: "Hrvatski jezik",
  eng: "Engleski jezik",
  mat: "Matematika",
  fiz: "Fizika",
  kem: "Kemija",
  pov: "Povijest",
  geo: "Geografija",
  bio: "Biologija",
  inf: "Informatika"
};

const naziviRazina = {
  sko: "Školsko",
  zup: "Županijsko",
  drz: "Državno"
};

const naziviRazreda = {
  "1r": "1. razred OŠ",
  "2r": "2. razred OŠ",
  "3r": "3. razred OŠ",
  "4r": "4. razred OŠ",
  "5r": "5. razred OŠ",
  "6r": "6. razred OŠ",
  "7r": "7. razred OŠ",
  "8r": "8. razred OŠ",
  "1rs": "1. razred SŠ",
  "2rs": "2. razred SŠ",
  "3rs": "3. razred SŠ",
  "4rs": "4. razred SŠ",
  "os": "Svi razredi OŠ",
  "ss": "Svi razredi SŠ"
};

let svaNatjecanja = [];

const listContainer = document.getElementById("natjecanjaList");
const resultsCount = document.getElementById("resultsCount");
const razredFilter = document.getElementById("razredFilter");
const predmetFilter = document.getElementById("predmetFilter");
const razinaFilter = document.getElementById("razinaFilter");
const godinaFilter = document.getElementById("godinaFilter");
const resetBtn = document.getElementById("resetBtn");

function opisRazreda(razred, predmet) {
  if (razred === "os") {
    if (predmet === "fiz") return "7. i 8. razred OŠ";
    if (predmet === "mat") return "4. – 8. razred OŠ";
    return "Osnovna škola (svi razredi)";
  }
  if (razred === "ss") {
    if (predmet === "geo") return "1. – 4. razred SŠ (strukovne)";
    if (predmet === "mat") return "1. – 4. razred SŠ";
    if (predmet === "inf") return "1. – 4. razred SŠ";
    return "Srednja škola (svi razredi)";
  }
  return naziviRazreda[razred] || razred;
}

async function ucitajPdfove() {
  try {
    const response = await fetch("popis.json?v=" + Date.now());
    if (!response.ok) {
      throw new Error("Nema popisa.");
    }

    const files = await response.json();
    const pdfImena = new Set(files);

    const cisteDatoteke = [...pdfImena].filter(ime => !/-\d+\.pdf$/i.test(ime));

    const dodatniNastavci = ["-rj.pdf", "-list.pdf", "-transkript.pdf", "-prakticni-rj.pdf"];
    const ispitneDatoteke = cisteDatoteke.filter(
      ime => !dodatniNastavci.some(nastavak => ime.toLowerCase().endsWith(nastavak))
    );

    svaNatjecanja = ispitneDatoteke.map(ime => {
      const bazniKod = ime.replace(/\.pdf$/i, "");
      const dijelovi = bazniKod.split("-");

      const razred = dijelovi.at(0) || "";
      const predmet = dijelovi.at(1) || "";
      const razina = dijelovi.at(2) || "";

      const godinaMatch = bazniKod.match(/(20\d{2})/);
      const godina = godinaMatch ? godinaMatch.at(0) : "";

      const jePrakticni = dijelovi.includes("prakticni");
      const varijanta = dijelovi.includes("A") ? "A" : dijelovi.includes("B") ? "B" : dijelovi.includes("C") ? "C" : "";

      const rjIme = `${bazniKod}-rj.pdf`;
      const listIme = `${bazniKod}-list.pdf`;
      const transkriptIme = `${bazniKod}-transkript.pdf`;

      const oznakaVarijante = varijanta ? ` (${varijanta} varijanta)` : (jePrakticni ? " (Praktični dio)" : "");

      return {
        kod: bazniKod,
        razred,
        predmet,
        razina,
        godina,
        varijanta,
        naziv: `${naziviPredmeta[predmet] || predmet} - ${naziviRazina[razina] || razina}${oznakaVarijante}${godina ? ` (${godina}.)` : ""}`,
        zadaciUrl: `${PDF_FOLDER}/${ime}`,
        rjesenjaUrl: pdfImena.has(rjIme) ? `${PDF_FOLDER}/${rjIme}` : "",
        transkriptUrl: pdfImena.has(transkriptIme) ? `${PDF_FOLDER}/${transkriptIme}` : "",
        listUrl: pdfImena.has(listIme) ? `${PDF_FOLDER}/${listIme}` : ""
      };
    });

    const postojeciKodovi = new Set(svaNatjecanja.map(n => n.kod));
    cisteDatoteke
      .filter(ime => ime.toLowerCase().endsWith("-rj.pdf"))
      .forEach(rjIme => {
        const bazniKod = rjIme.replace(/-rj\.pdf$/i, "");
        if (postojeciKodovi.has(bazniKod)) return;

        const dijelovi = bazniKod.split("-");
        const razred = dijelovi.at(0) || "";
        const predmet = dijelovi.at(1) || "";
        const razina = dijelovi.at(2) || "";
        const godinaMatch = bazniKod.match(/(20\d{2})/);
        const godina = godinaMatch ? godinaMatch.at(0) : "";
        const jePrakticni = dijelovi.includes("prakticni");
        const varijanta = dijelovi.includes("A") ? "A" : dijelovi.includes("B") ? "B" : dijelovi.includes("C") ? "C" : "";
        const oznakaVarijante = varijanta ? ` (${varijanta} varijanta)` : (jePrakticni ? " (Praktični dio)" : "");

        svaNatjecanja.push({
          kod: bazniKod,
          razred,
          predmet,
          razina,
          godina,
          varijanta,
          naziv: `${naziviPredmeta[predmet] || predmet} - ${naziviRazina[razina] || razina}${oznakaVarijante}${godina ? ` (${godina}.)` : ""}`,
          zadaciUrl: "",
          rjesenjaUrl: `${PDF_FOLDER}/${rjIme}`,
          transkriptUrl: "",
          listUrl: ""
        });
      });

    svaNatjecanja.sort((a, b) => Number(b.godina) - Number(a.godina));

    popuniGodineFilter();
    prikaziNatjecanja();
  } catch (error) {
    resultsCount.textContent = "Prikazano: 0";
    listContainer.innerHTML = `<div class="empty-state">Pokreni <strong>python3 skini.py</strong> kako bi se generirao popis PDF datoteka.</div>`;
  }
}

function popuniGodineFilter() {
  const jedinstveneGodine = [...new Set(svaNatjecanja.map(n => n.godina).filter(g => /^20\d{2}$/.test(g)))]
    .sort((a, b) => Number(b) - Number(a));

  godinaFilter.innerHTML = `<option value="sve">Sve godine</option>` +
    jedinstveneGodine.map(g => `<option value="${g}">${g}.</option>`).join("");
}

function prikaziNatjecanja() {
  const odabraniRazred = razredFilter.value;
  const odabraniPredmet = predmetFilter.value;
  const odabranaRazina = razinaFilter.value;
  const odabranaGodina = godinaFilter.value;

  const filtrirano = svaNatjecanja.filter(n => {
    const jeOsnovna = odabraniRazred.endsWith("r") && n.razred === "os";
    const jeSrednja = odabraniRazred.endsWith("rs") && n.razred === "ss";
    const odgovaraRazred = odabraniRazred === "svi" || n.razred === odabraniRazred || jeOsnovna || jeSrednja;

    const odgovaraPredmet = odabraniPredmet === "svi" || n.predmet === odabraniPredmet;
    const odgovaraRazina = odabranaRazina === "sve" || n.razina === odabranaRazina;
    const odgovaraGodina = odabranaGodina === "sve" || n.godina === odabranaGodina;

    return odgovaraRazred && odgovaraPredmet && odgovaraRazina && odgovaraGodina;
  });

  resultsCount.textContent = `Prikazano: ${filtrirano.length}`;

  if (filtrirano.length === 0) {
    listContainer.innerHTML = `<div class="empty-state">Nema natjecanja za odabrane filtere.</div>`;
    return;
  }

  listContainer.innerHTML = filtrirano.map(n => `
    <article class="item-card">
      <div class="item-info">
        <h2>${n.naziv}</h2>
        <div class="meta-tags">
          <span class="tag">${opisRazreda(n.razred, n.predmet)}</span>
          <span class="tag">${naziviPredmeta[n.predmet] || n.predmet}</span>
          <span class="tag">${naziviRazina[n.razina] || n.razina}</span>
          ${n.varijanta ? `<span class="tag">${n.varijanta} varijanta</span>` : ""}
          ${n.godina ? `<span class="tag">${n.godina}.</span>` : ""}
        </div>
      </div>
      <div class="item-actions">
        ${n.zadaciUrl ? `<a href="${n.zadaciUrl}" target="_blank" rel="noopener" class="btn-link btn-primary">Zadaci</a>` : ""}
        ${n.rjesenjaUrl ? `<a href="${n.rjesenjaUrl}" target="_blank" rel="noopener" class="btn-link ${!n.zadaciUrl ? 'btn-primary' : ''}">Rješenja</a>` : ""}
        ${n.transkriptUrl ? `<a href="${n.transkriptUrl}" target="_blank" rel="noopener" class="btn-link">Transkript</a>` : ""}
        ${n.listUrl ? `<a href="${n.listUrl}" target="_blank" rel="noopener" class="btn-link">List za odgovore</a>` : ""}
      </div>
    </article>
  `).join("");
}

function resetirajFiltere() {
  razredFilter.value = "svi";
  predmetFilter.value = "svi";
  razinaFilter.value = "sve";
  godinaFilter.value = "sve";
  prikaziNatjecanja();
}

razredFilter.addEventListener("change", prikaziNatjecanja);
predmetFilter.addEventListener("change", prikaziNatjecanja);
razinaFilter.addEventListener("change", prikaziNatjecanja);
godinaFilter.addEventListener("change", prikaziNatjecanja);
resetBtn.addEventListener("click", resetirajFiltere);

ucitajPdfove();