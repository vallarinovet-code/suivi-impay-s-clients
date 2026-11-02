# Suivi des impayés — Structure vétérinaire

Application web **locale** (aucune dépendance externe, Python 3 standard uniquement)
pour suivre les factures impayées d'une clinique vétérinaire : clients, animaux,
factures, paiements, impayés, relances, tableau de bord et modèles de relance.

## ▶️ Lancement

```bash
cd app
./run.sh                 # ou : python3 server.py
# puis ouvrir http://127.0.0.1:8000 dans le navigateur
```

Options : `--port 8080` pour changer le port, `--db chemin.db` pour changer la base.

L'application n'écoute que sur `127.0.0.1` (boucle locale) : aucune exposition réseau.

## 🧭 Fonctionnalités

- **Tableau de bord** : encours impayé, répartition par tranche (0–30 / 31–60 / 61–90 / > 90 j),
  relances des 7 derniers jours, montant recouvré ce mois, DSO, liste des impayés à relancer.
- **Impayés** : reste dû calculé automatiquement, ancienneté, tranche, niveau de relance,
  prochaine action suggérée (J+7 email → J+15 email+SMS → J+30 LRAR → J+60 échelonnement/injonction),
  filtre « à relancer aujourd'hui », export CSV.
- **Factures** : création, TVA (10 % soins / 20 % marchandises), acompte, statut auto
  (Payée / Partielle / Impayée), création automatique d'un impayé quand une facture devient impayée.
- **Paiements** : enregistrement d'un paiement → recalcul du reste dû et du statut.
- **Clients** : fiche détaillée (animaux, factures, historique des relances), consentement RGPD.
- **Relances** : historique complet (canal, contact, réponse du client, promesse de paiement), export CSV.
- **Modèles de relance** : emails/SMS/LRAR prêts à l'emploi avec variables `{...}`.

## 📁 Structure

```
app/
├── server.py          # serveur HTTP + API REST (stdlib : http.server, sqlite3, json)
├── db.py              # schéma SQLite + données de démonstration
├── run.sh             # lanceur
├── suivi_impayes.db   # base créée au premier lancement (données fictives de démo)
└── static/
    ├── index.html     # interface (onglets)
    ├── style.css
    └── app.js         # appels API + rendu
```

## 🗃️ Schéma de la base (SQLite)

`clients` 1—n `animaux`, `clients` 1—n `factures`, `factures` 1—n `paiements`,
`factures` 1—1 `impayes`, `impayes` 1—n `relances`.

## ⚖️ Cadre légal (résumé, voir docs/05)

Pénalités de retard au taux légal + indemnité forfaitaire de 40 € (art. L. 441-10 C. com.),
mise en demeure par LRAR à J+30, injonction de payer à J+60+, prescription 5 ans.

## 📦 Ancienne version

Le modèle documentaire Notion/Airtable d'origine est conservé dans `docs/` et `exemples/`
(à titre de référence pour migrer vers Notion/Airtable si besoin).
