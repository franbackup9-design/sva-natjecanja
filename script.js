const natjecanja = [
  {
    naziv: "Natjecanje iz matematike",
    predmet: "Matematika",
    razina: "Školsko",
    razred: "8. OŠ",
    godina: "2026./2027.",
    zadaciUrl: "https://azoo.hr",
    rjesenjaUrl: "https://azoo.hr"
  },
  {
    naziv: "Hrvatsko otvoreno natjecanje u informatici (HONI)",
    predmet: "Informatika",
    razina: "Ostalo",
    razred: "2. SŠ",
    godina: "2026./2027.",
    zadaciUrl: "https://hsin.hr",
    rjesenjaUrl: "https://hsin.hr"
  },
  {
    naziv: "Natjecanje iz fizike",
    predmet: "Fizika",
    razina: "Županijsko",
    razred: "3. SŠ",
    godina: "2025./2026.",
    zadaciUrl: "https://azoo.hr",
    rjesenjaUrl: ""
  }
];

const listContainer = document.getElementById("natjecanjaList");
const resultsCount = document.getElementById("resultsCount");
const searchInput = document.getElementById("searchInput");
const razinaFilter = document.getElementById("razinaFilter");
const razredFilter = document.getElementById("razredFilter");
const godinaFilter = document.getElementById("godinaFilter");
const resetBtn = document.getElementById("resetBtn");

function prikaziNatjecanja() {
  const tekst = searchInput.value.trim().toLowerCase();
  const razina = razinaFilter.value;
  const razred = razredFilter.value;
  const godina = godinaFilter.value;

  const filtrirano = natjecanja.filter(n => {
    const odgovaraTekst =
      n.naziv.toLowerCase().includes(tekst) ||
      n.predmet.toLowerCase().includes(tekst);
    const odgovaraRazina = razina === "sve" || n.razina === razina;
    const odgovaraRazred = razred === "svi" || n.razred === razred;
    const odgovaraGodina = godina === "sve" || n.godina === godina;

    return odgovaraTekst && odgovaraRazina && odgovaraRazred && odgovaraGodina;
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
          <span class="tag">${n.predmet}</span>
          <span class="tag">${n.razina}</span>
          <span class="tag">${n.razred}</span>
          <span class="tag">${n.godina}</span>
        </div>
      </div>
      <div class="item-actions">
        ${n.zadaciUrl ? `<a href="${n.zadaciUrl}" target="_blank" rel="noopener" class="btn-link btn-primary">Zadaci</a>` : ""}
        ${n.rjesenjaUrl ? `<a href="${n.rjesenjaUrl}" target="_blank" rel="noopener" class="btn-link">Rješenja</a>` : ""}
      </div>
    </article>
  `).join("");
}

function resetirajFiltere() {
  searchInput.value = "";
  razinaFilter.value = "sve";
  razredFilter.value = "svi";
  godinaFilter.value = "sve";
  prikaziNatjecanja();
}

searchInput.addEventListener("input", prikaziNatjecanja);
razinaFilter.addEventListener("change", prikaziNatjecanja);
razredFilter.addEventListener("change", prikaziNatjecanja);
godinaFilter.addEventListener("change", prikaziNatjecanja);
resetBtn.addEventListener("click", resetirajFiltere);

prikaziNatjecanja();
