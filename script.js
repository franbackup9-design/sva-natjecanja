
      const razred = dijelovi.at(0) || "";
      const predmet = dijelovi.at(1) || "";
      const razina = dijelovi.at(2) || "";
      const godina = dijelovi.find(d => /^20\d{2}$/.test(d)) || "";

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
        const godina = dijelovi.find(d => /^20\d{2}$/.test(d)) || "";
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