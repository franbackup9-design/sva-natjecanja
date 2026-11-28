const PDF_FOLDER = "https://github.com";

const naziviPredmeta = {
  hrj: "Hrvatski jezik", eng: "Engleski jezik", mat: "Matematika",
  fiz: "Fizika", kem: "Kemija", pov: "Povijest",
  geo: "Geografija", bio: "Biologija", inf: "Informatika"
};

const naziviRazina = { sko: "Školsko", zup: "Županijsko", drz: "Državno" };

const naziviRazreda = {
  "1r": "1. razred OŠ", "2r": "2. razred OŠ", "3r": "3. razred OŠ", "4r": "4. razred OŠ",
  "5r": "5. razred OŠ", "6r": "6. razred OŠ", "7r": "7. razred OŠ", "8r": "8. razred OŠ",
  "1rs": "1. razred SŠ", "2rs": "2. razred SŠ", "3rs": "3. razred SŠ", "4rs": "4. razred SŠ",
  "os": "Svi razredi OŠ", "ss": "Svi razredi SŠ"
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
    if (predmet === "mat" || predmet === "inf") return "1. – 4. razred SŠ";
    return "Srednja škola (svi razredi)";
  }
  return naziviRazreda[razred] || razred;
}

async function ucitajPdfove() {
  try {
    const res = await fetch("popis.json?v=" + Date.now());
    const files = await res.json();
    const pdfImena = new Set(files);
    const cisti = files.filter(f => !/-\d{1,2}\.pdf$/i.test(f));

    const jeDodatni = f => f.endsWith("-rj.pdf") || f.endsWith("-list.pdf") || f.endsWith("-transkript.pdf") || f.endsWith("-prakticni-rj.pdf");
    const glavni = cisti.filter(f => !jeDodatni(f));

    svaNatjecanja = glavni.map(ime => {
      const kod = ime.replace(/\.pdf$/i, "");
      const d = kod.split("-");
      const razred = d.at(0) || "";
      const predmet = d.at(1) || "";
      const razina = d.at(2) || "";
      const godina = d.find(x => /^20\d{2}$/.test(x)) || "";
      const prakt = d.includes("prakticni");
      const varSlovo = d.includes("A") ? "A" : d.includes("B") ? "B" : d.includes("C") ? "C" : "";
      const oznaka = varSlovo ? ` (${varSlovo} varijanta)` : (prakt ? " (Praktični dio)" : "");

      return {
        kod, razred, predmet, razina, godina, varijanta: varSlovo,
        naziv: `${naziviPredmeta[predmet] || predmet} - ${naziviRazina[razina] || razina}${oznaka}${godina ? ` (${godina}.)` : ""}`,
        zadaciUrl: `${PDF_FOLDER}/${ime}`,
        rjesenjaUrl: pdfImena.has(`${kod}-rj.pdf`) ? `${PDF_FOLDER}/${kod}-rj.pdf` : "",
        transkriptUrl: pdfImena.has(`${kod}-transkript.pdf`) ? `${PDF_FOLDER}/${kod}-transkript.pdf` : "",
        listUrl: pdfImena.has(`${kod}-list.pdf`) ? `${PDF_FOLDER}/${kod}-list.pdf` : ""
      };
    });

    const postojeci = new Set(svaNatjecanja.map(n => n.kod));
    cisti.filter(f => /-rj\.pdf$/i.test(f)).forEach(rjIme => {
      const kod = rjIme.replace(/-rj\.pdf$/i, "");
      if (postojeci.has(kod)) return;
      const d = kod.split("-");
      const razred = d.at(0) || "";
      const predmet = d.at(1) || "";
      const razina = d.at(2) || "";
      const godina = d.find(x => /^20\d{2}$/.test(x)) || "";
      const prakt = d.includes("prakticni");
      const varSlovo = d.includes("A") ? "A" : d.includes("B") ? "B" : d.includes("C") ? "C" : "";
      const oznaka = varSlovo ? ` (${varSlovo} varijanta)` : (prakt ? " (Praktični dio)" : "");

      svaNatjecanja.push({
        kod, razred, predmet, razina, godina, varijanta: varSlovo,
        naziv: `${naziviPredmeta[predmet] || predmet} - ${naziviRazina[razina] || razina}${oznaka}${godina ? ` (${godina}.)` : ""}`,
        zadaciUrl: "", rjesenjaUrl: `${PDF_FOLDER}/${rjIme}`, transkriptUrl: "", listUrl: ""
      });
    });

    svaNatjecanja.sort((a, b) => Number(b.godina) - Number(a.godina));
    const godine = [...new Set(svaNatjecanja.map(n => n.godina).filter(g => /^20\d{2}$/.test(g)))].sort((a, b) => b - a);
    godinaFilter.innerHTML = `<option value="sve">Sve godine</option>` + godine.map(g => `<option value="${g}">${g}.</option>`).join("");
    prikaziNatjecanja();
  } catch (e) {
    resultsCount.textContent = "Prikazano: 0";
  }
}

function prikaziNatjecanja() {
  const r = razredFilter.value, p = predmetFilter.value, rz = razinaFilter.value, g = godinaFilter.value;
  const filtrirano = svaNatjecanja.filter(n =>
    (r === "svi" || n.razred === r || (r.endsWith("r") && n.razred === "os") || (r.endsWith("rs") && n.razred === "ss")) &&
    (p === "svi" || n.predmet === p) &&
    (rz === "sve" || n.razina === rz) &&
    (g === "sve" || n.godina === g)
  );

  resultsCount.textContent = `Prikazano: ${filtrirano.length}`;
  if (!filtrirano.length) {
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

razredFilter.addEventListener("change", prikaziNatjecanja);
predmetFilter.addEventListener("change", prikaziNatjecanja);
razinaFilter.addEventListener("change", prikaziNatjecanja);
godinaFilter.addEventListener("change", prikaziNatjecanja);
resetBtn.addEventListener("click", () => {
  razredFilter.value = "svi"; predmetFilter.value = "svi"; razinaFilter.value = "sve"; godinaFilter.value = "sve";
  prikaziNatjecanja();
});

ucitajPdfove();