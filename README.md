# Suivi des impayés — Structure vétérinaire

Modèle complet (type Notion / Airtable) pour suivre les factures impayées d'une clinique
vétérinaire : fiches clients, animaux, factures, paiements, impayés, relances et tableau
de bord de recouvrement.

## Contenu

| Dossier / fichier | Description |
|---|---|
| `docs/01-structure-bases.md` | Les 6 tables, leurs champs, types et liens entre elles |
| `docs/02-vues-et-tableau-de-bord.md` | Vues filtrées, tris, kanban et indicateurs (KPI) à reproduire |
| `docs/03-formules-et-automatisations.md` | Formules (reste dû, ancienneté, tranche) et scénarios de relance automatique |
| `docs/04-modeles-relances.md` | Modèles d'emails, SMS et courrier de relance (J+7 à J+60+) |
| `docs/05-procedure-recouvrement-france.md` | Cadre légal français : délais, pénalités, mise en demeure, injonction de payer, prescription |
| `docs/06-rgpd-et-conservation.md` | Conformité RGPD, consentements et durées de conservation |
| `docs/07-guide-import-notion-airtable.md` | Guide pas à pas pour recréer la base dans Notion ou Airtable |
| `exemples/*.csv` | Données fictives pour tester l'import et les formules |

## Schéma global

```
Clients ──┬──< Animaux
          ├──< Factures ──< Paiements
          │      │
          │      └──< Impayés ──< Relances
          └──< Impayés
```

## Démarrage rapide

1. Créez une base dans Notion ou Airtable (voir `docs/07-guide-import-notion-airtable.md`).
2. Créez les 6 tables décrites dans `docs/01-structure-bases.md` avec les liens entre elles.
3. Importez les CSV d'exemple (`exemples/`) pour tester.
4. Ajoutez les formules et vues des `docs/02` et `docs/03`.
5. Configurez les automatisations de relance (`docs/03`) et les modèles de messages (`docs/04`).

Toutes les données dans `exemples/` sont fictives et servent uniquement de test.
