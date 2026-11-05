const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2500);
}

async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || res.statusText);
  return data;
}

const eur = (n) => (n == null ? "—" : Number(n).toLocaleString("fr-FR", { style: "currency", currency: "EUR" }));
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

function badgeTranche(t) {
  const cls = { "À échoir": "gris", "0-30 j": "bleu", "31-60 j": "orange", "61-90 j": "orange", "> 90 j": "rouge" }[t] || "gris";
  return `<span class="badge ${cls}">${esc(t)}</span>`;
}
function badgeStatut(s) {
  const cls = { "Ouvert": "rouge", "En cours": "orange", "Payée": "vert", "Partielle": "orange", "Impayée": "rouge",
    "Résolu": "vert", "Litige": "rouge", "Recouvrement externe": "rouge", "Irrécouvrable": "gris", "Actif": "vert", "Inactif": "gris", "À échoir": "gris" }[s] || "gris";
  return `<span class="badge ${cls}">${esc(s)}</span>`;
}

async function loadDashboard() {
  const d = await api("/api/dashboard");
  $("#kpis").innerHTML = `
    <div class="kpi"><div class="label">Encours impayé</div><div class="value">${eur(d.encours_impaye)}</div><div class="sub">${d.nb_impayes_ouverts} impayé(s) ouvert(s)</div></div>
    <div class="kpi"><div class="label">Tranches</div><div class="value" style="font-size:1rem;line-height:1.9">
      0–30 j : ${d.repartition_tranches["0-30 j"]} · 31–60 j : ${d.repartition_tranches["31-60 j"]}<br>
      61–90 j : ${d.repartition_tranches["61-90 j"]} · &gt; 90 j : ${d.repartition_tranches["> 90 j"]}</div></div>
    <div class="kpi"><div class="label">Relances (7 jours)</div><div class="value">${d.relances_7_jours}</div></div>
    <div class="kpi"><div class="label">Recouvré ce mois</div><div class="value">${eur(d.recouvre_ce_mois)}</div></div>
    <div class="kpi"><div class="label">DSO</div><div class="value">${d.dso_jours == null ? "—" : d.dso_jours + " j"}</div><div class="sub">délai moyen de paiement</div></div>`;
  const imp = await api("/api/impayes?filtre=a-relancer");
  $("#dash-impayes").innerHTML = imp.length ? `<table><tr><th>Impayé</th><th>Facture</th><th>Client</th><th>Reste dû</th><th>Échéance</th><th>Retard</th><th>Tranche</th><th>Prochaine action</th><th>Statut</th></tr>` +
    imp.map((r) => `<tr><td>${esc(r.code)}</td><td>${esc(r.facture)}</td><td>${esc(r.client_prenom + " " + r.client_nom)}</td>
      <td class="montant">${eur(r.reste_du)}</td><td>${esc(r.date_echeance)}</td><td>${r.anciennete} j</td>
      <td>${badgeTranche(r.tranche)}</td><td>${esc(r.prochaine_action)}</td><td>${badgeStatut(r.statut)}</td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucun impayé à relancer aujourd\'hui. ✅</p>';
}

async function loadImpayes() {
  const f = $("#filtre-a-relancer").checked ? "?filtre=a-relancer" : "";
  const rows = await api("/api/impayes" + f);
  $("#liste-impayes").innerHTML = rows.length ? `<table><tr><th>Impayé</th><th>Facture</th><th>Client</th><th>Contact</th><th>Reste dû</th><th>Échéance</th><th>Retard</th><th>Tranche</th><th>Niveau</th><th>Prochaine action</th><th>Responsable</th><th>Statut</th><th></th></tr>` +
    rows.map((r) => `<tr>
      <td>${esc(r.code)}</td><td>${esc(r.facture)}</td>
      <td><a class="client-link" onclick="showClientByCode('${esc(r.client_code)}')">${esc(r.client_prenom + " " + r.client_nom)}</a></td>
      <td>${esc(r.telephone)}<br>${esc(r.email)}</td>
      <td class="montant">${eur(r.reste_du)}</td><td>${esc(r.date_echeance)}</td><td>${r.anciennete} j</td>
      <td>${badgeTranche(r.tranche)}</td><td>${esc(r.niveau_relance)}</td><td>${esc(r.prochaine_action)}</td>
      <td>${esc(r.responsable)}</td><td>${badgeStatut(r.statut)}</td>
      <td class="ligne-actions">
        <button class="btn small" onclick="openForm('relance', {impaye_id: ${r.id}})">+ Relance</button>
        <button class="btn small" onclick="editImpaye(${r.id}, '${esc(r.statut)}', '${esc(r.niveau_relance)}', '${esc(r.responsable)}')">✏️</button>
      </td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucun impayé ouvert.</p>';
}

async function loadFactures() {
  const rows = await api("/api/factures");
  $("#liste-factures").innerHTML = rows.length ? `<table><tr><th>N°</th><th>Date</th><th>Client</th><th>Animal</th><th>Prestation</th><th>Catégorie</th><th>MTTC</th><th>Payé</th><th>Reste dû</th><th>Échéance</th><th>Statut</th><th></th></tr>` +
    rows.map((r) => `<tr>
      <td>${esc(r.numero)}</td><td>${esc(r.date_facture)}</td><td>${esc(r.client_prenom + " " + r.client_nom)}</td>
      <td>${esc(r.animal_nom || "—")}</td><td>${esc(r.prestation)}</td><td>${esc(r.categorie)}</td>
      <td class="montant">${eur(r.montant_ttc)}</td><td class="montant">${eur(r.paye + r.acompte)}</td>
      <td class="montant">${eur(r.reste_du)}</td><td>${esc(r.date_echeance)}</td><td>${badgeStatut(r.statut)}</td>
      <td class="ligne-actions">
        ${r.statut !== "Payée" ? `<button class="btn small" onclick="openForm('paiement', {facture_id: ${r.id}})">+ Paiement</button>` : ""}
        <button class="btn small danger" onclick="del('factures', ${r.id}, loadFactures)">🗑</button>
      </td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucune facture.</p>';
}

async function loadClients() {
  const rows = await api("/api/clients");
  $("#liste-clients").innerHTML = rows.length ? `<table><tr><th>Code</th><th>Nom</th><th>Téléphone</th><th>Email</th><th>Ville</th><th>Canal pref.</th><th>Nb impayés</th><th>Total impayé</th><th>Statut</th><th></th></tr>` +
    rows.map((r) => `<tr>
      <td>${esc(r.code)}</td>
      <td><a class="client-link" onclick="showClient(${r.id})">${esc(r.prenom + " " + r.nom)}</a></td>
      <td>${esc(r.telephone)}</td><td>${esc(r.email)}</td><td>${esc(r.ville)}</td><td>${esc(r.canal_prefere)}</td>
      <td>${r.nb_impayes}</td><td class="montant">${eur(r.total_impaye)}</td><td>${badgeStatut(r.statut)}</td>
      <td><button class="btn small danger" onclick="del('clients', ${r.id}, loadClients)">🗑</button></td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucun client.</p>';
}

async function loadRelances() {
  const rows = await api("/api/relances");
  $("#liste-relances").innerHTML = rows.length ? `<table><tr><th>Date</th><th>Impayé</th><th>Facture</th><th>Client</th><th>Canal</th><th>Par</th><th>Résumé</th><th>Réponse client</th><th>Promesse</th><th>Résultat</th><th></th></tr>` +
    rows.map((r) => `<tr><td>${esc(r.date)}</td><td>${esc(r.impaye_code)}</td><td>${esc(r.facture)}</td>
      <td>${esc(r.client_prenom + " " + r.client_nom)}</td><td>${esc(r.canal)}</td><td>${esc(r.effectuee_par)}</td>
      <td>${esc(r.resume)}</td><td>${esc(r.reponse_client)}</td><td>${esc(r.date_promesse || "—")}</td>
      <td>${esc(r.resultat)}</td>
      <td><button class="btn small danger" onclick="del('relances', ${r.id}, loadRelances)">🗑</button></td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucune relance enregistrée.</p>';
}

async function loadPaiements() {
  const rows = await api("/api/paiements");
  $("#liste-paiements").innerHTML = rows.length ? `<table><tr><th>Date</th><th>Facture</th><th>Client</th><th>Montant</th><th>Moyen</th><th>Référence</th><th>Notes</th><th></th></tr>` +
    rows.map((r) => `<tr><td>${esc(r.date)}</td><td>${esc(r.facture)}</td><td>${esc(r.client_prenom + " " + r.client_nom)}</td>
      <td class="montant">${eur(r.montant)}</td><td>${esc(r.moyen)}</td><td>${esc(r.reference)}</td><td>${esc(r.notes)}</td>
      <td><button class="btn small danger" onclick="del('paiements', ${r.id}, loadPaiements)">🗑</button></td></tr>`).join("") + "</table>"
    : '<p class="hint">Aucun paiement.</p>';
}

async function loadModeles() {
  const m = await api("/api/modeles");
  $("#liste-modeles").innerHTML = Object.entries(m).map(([k, v]) => `
    <div class="modele"><h3>${esc(k)}</h3><div class="objet">Objet : ${esc(v.objet)}</div>
    <pre>${esc(v.corps)}</pre></div>`).join("");
}

async function del(table, id, reload) {
  if (!confirm("Supprimer cet élément ?")) return;
  await api(`/api/${table}/${id}`, { method: "DELETE" });
  toast("Supprimé");
  reload();
}

async function showClient(id) {
  const c = await api("/api/clients/" + id);
  $("#detail-client").innerHTML = `<div class="box"><h3>${esc(c.prenom + " " + c.nom)} (${esc(c.code)})</h3>
    <p>${esc(c.telephone)} · ${esc(c.email)}<br>${esc(c.adresse)} ${esc(c.code_postal)} ${esc(c.ville)}<br>
    Canal pref. : ${esc(c.canal_prefere)} · Paiement : ${esc(c.mode_paiement)} · Consentement relance : ${c.consentement_relance ? "oui" : "non"}</p>
    <h4>Animaux</h4><ul>${c.animaux.map((a) => `<li>${esc(a.nom)} — ${esc(a.espece)} ${esc(a.race)}</li>`).join("") || "<li>Aucun</li>"}</ul>
    <h4>Factures</h4><table><tr><th>N°</th><th>Date</th><th>Prestation</th><th>Reste dû</th><th>Statut</th></tr>
      ${c.factures.map((f) => `<tr><td>${esc(f.numero)}</td><td>${esc(f.date_facture)}</td><td>${esc(f.prestation)}</td><td class="montant">${eur(Math.max(0, f.reste_du))}</td><td>${badgeStatut(f.statut)}</td></tr>`).join("")}</table>
    <h4>Historique des relances</h4><table><tr><th>Date</th><th>Canal</th><th>Résumé</th><th>Réponse</th></tr>
      ${c.relances.map((r) => `<tr><td>${esc(r.date)}</td><td>${esc(r.canal)}</td><td>${esc(r.resume)}</td><td>${esc(r.reponse_client)}</td></tr>`).join("") || "<tr><td colspan=4>Aucune</td></tr>"}</table>
    <div class="actions"><button class="btn" onclick="closeModal('detail-client')">Fermer</button></div></div>`;
  $("#detail-client").classList.remove("hidden");
}
let clientCodeMap = {};
async function showClientByCode(code) {
  if (!Object.keys(clientCodeMap).length) {
    const list = await api("/api/clients");
    list.forEach((c) => (clientCodeMap[c.code] = c.id));
  }
  if (clientCodeMap[code]) showClient(clientCodeMap[code]);
}
function closeModal(id) { $("#" + id).classList.add("hidden"); }

async function editImpaye(id, statut, niveau, responsable) {
  const ns = prompt("Statut (Ouvert / En cours / Échelonnement signé / Résolu / Litige / Recouvrement externe / Irrécouvrable) :", statut);
  if (ns === null) return;
  const nn = prompt("Niveau de relance (Aucun / J+7 / J+15 / J+30 / J+60) :", niveau);
  await api(`/api/impayes/${id}`, { method: "PATCH", body: { statut: ns, niveau_relance: nn ?? niveau, responsable } });
  toast("Mis à jour");
  loadImpayes();
}

async function openForm(type, preset = {}) {
  const clients = await api("/api/clients");
  const factures = await api("/api/factures");
  const impayes = await api("/api/impayes");
  const today = new Date().toISOString().slice(0, 10);
  const sel = (name, options, def) => `<select name="${name}">${options.map((o) => `<option ${o === def ? "selected" : ""}>${esc(o)}</option>`).join("")}</select>`;
  const inp = (name, label, type = "text", def = "") => `<label>${label}<input name="${name}" type="${type}" value="${esc(def)}"></label>`;
  let html = "";
  if (type === "client") {
    html = `<div class="box"><h3>Nouveau client</h3>
      ${inp("nom", "Nom *")}${inp("prenom", "Prénom")}${inp("telephone", "Téléphone", "tel")}${inp("email", "Email", "email")}
      ${inp("adresse", "Adresse")}${inp("code_postal", "Code postal")}${inp("ville", "Ville")}
      ${sel("canal_prefere", ["Email", "SMS", "Courrier", "Téléphone"], "Email")}
      ${sel("mode_paiement", ["CB", "Virement", "Chèque", "Espèces", "Autre"], "CB")}
      <label><input type="checkbox" name="consentement_relance" style="width:auto"> Consentement aux relances (RGPD)</label>
      <div class="actions"><button class="btn" onclick="closeModal('form-client')">Annuler</button>
      <button class="btn primary" onclick="submitForm('client','form-client',loadClients)">Enregistrer</button></div></div>`;
  } else if (type === "facture") {
    html = `<div class="box"><h3>Nouvelle facture</h3>
      ${inp("numero", "N° (auto si vide)")}${inp("date_facture", "Date", "date", today)}
      <label>Client *<select name="client_id">${clients.map((c) => `<option value="${c.id}">${esc(c.code + " — " + c.prenom + " " + c.nom)}</option>`).join("")}</select></label>
      ${inp("prestation", "Prestation / motif")}
      ${sel("categorie", ["Consultation", "Vaccination", "Chirurgie", "Imagerie", "Analyses", "Hospitalisation", "Pharmacie", "Alimentation", "Pension", "Autre"], "Consultation")}
      ${inp("montant_ht", "Montant HT (€)", "number", "0")}${inp("tva_pct", "TVA (%)", "number", "10")}
      ${inp("acompte", "Acompte versé (€)", "number", "0")}${inp("date_echeance", "Échéance", "date", new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10))}
      <div class="actions"><button class="btn" onclick="closeModal('form-facture')">Annuler</button>
      <button class="btn primary" onclick="submitForm('facture','form-facture',loadFactures)">Enregistrer</button></div></div>`;
  } else if (type === "paiement") {
    html = `<div class="box"><h3>Nouveau paiement</h3>
      ${inp("date", "Date", "date", today)}
      <label>Facture *<select name="facture_id">${factures.map((f) => `<option value="${f.id}" ${f.id === preset.facture_id ? "selected" : ""}>${esc(f.numero + " — " + f.client_nom + " — reste " + f.reste_du.toFixed(2) + " €")}</option>`).join("")}</select></label>
      ${inp("montant", "Montant (€) *", "number", "0")}
      ${sel("moyen", ["CB", "Virement", "Chèque", "Espèces", "Avoir", "Autre"], "CB")}
      ${inp("reference", "Référence (chèque, virement)")}${inp("notes", "Notes")}
      <div class="actions"><button class="btn" onclick="closeModal('form-paiement')">Annuler</button>
      <button class="btn primary" onclick="submitForm('paiement','form-paiement',()=>{loadPaiements();loadFactures();loadImpayes();loadDashboard();})">Enregistrer</button></div></div>`;
  } else if (type === "relance") {
    html = `<div class="box"><h3>Nouvelle relance</h3>
      ${inp("date", "Date", "date", today)}
      <label>Impayé *<select name="impaye_id">${impayes.map((i) => `<option value="${i.id}" ${i.id === preset.impaye_id ? "selected" : ""}>${esc(i.code + " — " + i.client_nom + " — " + Number(i.reste_du).toFixed(2) + " €")}</option>`).join("")}</select></label>
      ${sel("canal", ["Téléphone", "Email", "SMS", "Courrier simple", "LRAR"], "Email")}
      ${inp("effectuee_par", "Effectuée par")}${inp("contact", "Contact (personne jointe)")}
      ${inp("resume", "Résumé")}${sel("reponse_client", ["Aucune", "Promesse de payer", "Paiement partiel", "Contestation", "Demande d'échelonnement", "Injoignable"], "Aucune")}
      ${inp("date_promesse", "Date de promesse de paiement", "date")}${sel("resultat", ["À relancer", "En attente", "Résolu", "Escalader"], "À relancer")}
      <div class="actions"><button class="btn" onclick="closeModal('form-relance')">Annuler</button>
      <button class="btn primary" onclick="submitForm('relance','form-relance',()=>{loadRelances();loadImpayes();loadDashboard();})">Enregistrer</button></div></div>`;
  }
  const target = { client: "form-client", facture: "form-facture", paiement: "form-paiement", relance: "form-relance" }[type];
  $("#" + target).innerHTML = html;
  $("#" + target).classList.remove("hidden");
}

async function submitForm(type, modalId, reload) {
  const box = $("#" + modalId + " .box");
  const body = {};
  box.querySelectorAll("input, select, textarea").forEach((el) => {
    body[el.name] = el.type === "checkbox" ? el.checked : el.value;
  });
  await api("/api/" + (type === "client" ? "clients" : type + "s"), { method: "POST", body });
  closeModal(modalId);
  toast("Enregistré ✅");
  reload();
}

$$("#tabs button").forEach((b) => b.addEventListener("click", () => {
  $$("#tabs button").forEach((x) => x.classList.remove("active"));
  $$(".tab").forEach((x) => x.classList.remove("active"));
  b.classList.add("active");
  $("#tab-" + b.dataset.tab).classList.add("active");
  ({ dashboard: loadDashboard, impayes: loadImpayes, factures: loadFactures, clients: loadClients, relances: loadRelances, paiements: loadPaiements, modeles: loadModeles })[b.dataset.tab]();
}));

$("#filtre-a-relancer").addEventListener("change", loadImpayes);
loadDashboard();
