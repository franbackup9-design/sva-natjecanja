const GITHUB_USER = "franbackup9-design";
const GITHUB_REPO = "sva-natjecanja";
const PDF_FOLDER = "pdf";

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

async function ucitajPdfoveSGitHuba() {
  try {
    const apiUrl = `https://github.com{GITHUB_USER}/${GITHUB_REPO}/contents/${PDF_FOLDER}`;
    const response = await fetch(apiUrl);
    
    if (!response.ok) {
      throw new Error("Mapa pdf još ne postoji na GitHubu ili je prazna.");
    }

    const files = await response.json();
    const pdfImena = new Set(
      files
        .filter(f => f.name.toLowerCase().endsWith(".pdf"))
        .map(f => f.name)
    );

    const ispitneDatoteke = [...pdfImena].filter(ime => !ime.toLowerCase().endsWith("-rj.pdf"));

    svaNatjecanja = ispitneDatoteke.map(ime => {
      const bazniKod = ime.replace(/\.pdf$/i, "");
      const [razred, predmet, razina, godina] = bazniKod.split("-");
      const rjIme = `${bazniKod}-rj.pdf`;
      const imaRjesenja = pdfImena.has(rjIme);

      return {
        kod: bazniKod,
        razred: razred || "",
        predmet: predmet || "",
        razina: razina || "",
        godina: godina || "",
        naziv: `${naziviPredmeta[predmet] || predmet} - ${naziviRazina[razina] || razina} (${godina}.)`,
        zadaciUrl: `${PDF_FOLDER}/${ime}`,
        rjesenjaUrl: imaRjesenja ? `${PDF_FOLDER}/${rjIme}` : ""
      };
    });

    // Sortiraj od najnovije godine prema starijima
    svaNatjecanja.sort((a, b) => Number(b.godina) - Number(a.godina));

    popuniGodineFilter();
    prikaziNatjecanja();
  } catch (error) {
    resultsCount.textContent = "Prikazano: 0";
    listContainer.innerHTML = `<div class="empty-state">Dodaj prve PDF datoteke u mapu <strong>pdf/</strong> i pošalji ih na GitHub kako bi se prikazale ovdje.</div>`;
  }
}

function popuniGodineFilter() {
  const jedinstveneGodine = [...new Set(svaNatjecanja.map(n => n.godina).filter(Boolean))]
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
          <span class="tag">${naziviRazreda[n.razred] || n.razred}</span>
          <span class="tag">${naziviPredmeta[n.predmet] || n.predmet}</span>
          <span class="tag">${naziviRazina[n.razina] || n.razina}</span>
          <span class="tag">${n.godina}.</span>
          <span class="tag">${n.kod}</span>
        </div>
      </div>
      <div class="item-actions">
        <a href="${n.zadaciUrl}" target="_blank" rel="noopener" class="btn-link btn-primary">Zadaci</a>
        ${n.rjesenjaUrl ? `<a href="${n.rjesenjaUrl}" target="_blank" rel="noopener" class="btn-link">Rješenja</a>` : ""}
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

ucitajPdfoveSGitHuba();
