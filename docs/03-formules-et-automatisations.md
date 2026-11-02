# 03 — Formules et automatisations

## Formules essentielles

### Factures — Reste dû
```
MAX(0, {Montant TTC} - {Acompte versé} - {Paiements reçus (rollup)})
```

### Factures — Statut automatique
```
SI({Reste dû} = 0, "Payée",
  SI({Reste dû} < {Montant TTC}, "Partielle", "Impayée"))
```

### Impayés — Ancienneté (jours de retard)
```
TODAY() - {Date d'échéance}
```
(valleur positive = en retard ; négative = pas encore échu)

### Impayés — Tranche
```
SI({Ancienneté} < 0, "À échoir",
 SI({Ancienneté} <= 30, "0–30 j",
 SI({Ancienneté} <= 60, "31–60 j",
 SI({Ancienneté} <= 90, "61–90 j", "> 90 j"))))
```

### Impayés — Prochaine action et sa date
```
SI({Tranche} = "0–30 j", "Email de relance J+7", "...")
```
Date de prochaine action :
```
SI({Tranche} = "À échoir", {Date d'échéance},
 SI({Tranche} = "0–30 j", {Date d'échéance} + 7,
 SI({Tranche} = "31–60 j", {Date d'échéance} + 15,
 SI({Tranche} = "61–90 j", {Date d'échéance} + 30,
 {Date d'échéance} + 60))))
```

### Dashboard — DSO (jours)
```
MOYENNE(date de paiement - date de facture) sur factures payées
```

## Automatisations de relance (scénario type)

| Déclencheur | Action | Canal |
|---|---|---|
| Facture passe à « Impayée » + 7 jours | Créer une tâche « Relancer » + envoyer email modèle J+7 | Email |
| Toujours impayée à J+15 | Email modèle J+15 + SMS si consentement SMS | Email + SMS |
| J+30 | Générer le courrier de mise en demeure (modèle J+30) + créer tâche LRAR | Courrier LRAR |
| J+45 | Appel téléphonique (tâche attribuée au responsable) | Téléphone |
| J+60 | Proposition d'échelonnement (modèle J+60) ou transmission au recouvrement externe | Email / dossier externe |
| Promesse de paiement non tenue (date dépassée, pas de paiement) | Relance immédiate + escalade d'un niveau | Selon canal préféré |

Dans **Notion** : automatisations natives (bouton « Automatisations » sur la base) déclenchées sur changement de statut/date, avec envoi d'email via intégration. Dans **Airtable** : « Automations » avec étapes « Send email » (nécessite les modèles d'email) ou déclencheur vers Make/Zapier pour SMS et LRAR.

## Rappels internes

- Tâche hebdomadaire (lundi matin) : revue de la vue « À relancer aujourd'hui ».
- Tâche mensuelle : export du tableau de bord, rapprochement comptable (les impayés > 90 j doivent apparaître en comptabilité clients).
