# 07 — Guide pas à pas : recréer la base dans Notion ou Airtable

## Option A — Notion

1. **Nouvelle page** → « + » → « Base de données » → « Table » (plein écran).
2. Renommez la base : « Clients ». Ajoutez les propriétés une par une (clic « + » en haut de colonne) selon `docs/01-structure-bases.md` :
   - Texte, Nombre, Date, Sélection, Case, Email, Téléphone, Personne, Fichier, Texte long…
   - Pour les liens : propriété « Relation » → « Choisir une base de données » (créez-la d'abord à vide).
   - Pour les agrégats : propriété « Rollup » → choisir la relation, la propriété à agréger (sum / count / max) et le filtre éventuel.
   - Pour les formules : propriété « Formule » → coller les formules de `docs/03` en adaptant les noms de propriétés entre accolades `{...}`.
3. Répétez pour les 6 tables : Clients, Animaux, Factures, Paiements, Impayés, Relances, en configurant les relations croisées.
4. Créez les vues de `docs/02` : onglet « + » → « Vue ajoutée » → filtres/tri/groupes.
5. Créez une page « Dashboard » et liez-y les bases filtrées (Slash « /linked »).
6. Automatisations : en haut de la base → « ... » → « Automatisations » → « Nouveau déclencheur » (ex. « Quand la date d'échéance est dépassée » ou « Quand le statut change ») → action « Envoyer un email » (nécessite une intégration email connectée) ou « Créer une page dans… » (tâche dans une base « Tâches de relance »).
7. Importez les exemples : dans chaque base, « ... » → « Fusionner avec CSV » ou « Importer » → CSV, en mappant les colonnes.

## Option B — Airtable

1. **Create** → « Base from scratch » → renommez « Suivi impayés veto ».
2. Créez les 6 tables (onglets) : même libellés de champs que `docs/01`.
3. Types de champs : Single line text, Phone, Email, Currency (EUR), Percent, Date, Single select / Multiple select, Checkbox, Single link / Multiple link (vers la table cible), Rollup (agrégation sum/count/max + condition), Formula (formules de `docs/03`, syntaxe proche d'Excel : `MAX(0, ...)`, `TODAY()`, `DATETIME_DIFF(...)`, `IF(...)`).
4. Vues : « + Create view » → Grid (filtres, tris) ou Kanban (champ de groupement = « Tranche »).
5. Automatisations : « Automations » (en haut) → « New automation » → déclencheur « When record matches conditions » (ex. Statut = Impayée ET ancienneté >= 7) → actions « Send email » (modèles personnalisables avec champs fusionnés), ou « Run a script » pour des cas avancés. Pour les SMS : connecteur « Send SMS » via extension ou via Make/Zapier.
6. Dashboard : « Extensions » → « Dashboard » ou créez une interface (« Interfaces » en plan supérieur) avec les KPIs de `docs/02`.
7. Import : table vide → « ... » → « Import data » → CSV.

## Vérification après import

- Ouvrez la vue « À relancer aujourd'hui » : elle doit lister les impayés de `exemples/` dont la date de prochaine action est passée.
- Vérifiez le calcul de « Reste dû » sur chaque facture exemple.
- Testez une relance : changez le statut d'un impayé et vérifiez que la tâche/l'email se déclenche (en mode test d'abord).
