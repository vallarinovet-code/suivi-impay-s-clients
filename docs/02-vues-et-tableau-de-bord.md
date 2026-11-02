# 02 — Vues et tableau de bord

## Vues indispensables

### Dans la table « Impayés »

1. **« À relancer aujourd'hui »** — filtre : `Prochaine action <= Aujourd'hui` ET `Statut = Ouvert/En cours`, tri : ancienneté décroissante.
2. **« Kanban par tranche »** — groupe par `Tranche` (0–30 / 31–60 / 61–90 / > 90 j), tri par montant impayé décroissant.
3. **« Top 10 des plus gros impayés »** — filtre `Statut != Résolu`, tri montant décroissant, limite 10.
4. **« Échelonnements en cours »** — filtre `Statut = Échelonnement signé` (surveillance des échéances d'échelonnement).
5. **« Promesses non tenues »** — dans Relances : filtre `Réponse = Promesse de payer` ET `Date de promesse < Aujourd'hui` ET pas de paiement associé.

### Dans la table « Factures »

6. **« Toutes les impayées »** — filtre `Statut = Impayée ou Partielle`, tri date d'échéance croissante.
7. **« À échoir cette semaine »** — filtre `Date d'échéance` dans les 7 prochains jours, `Statut != Payée`.

### Dans la table « Relances »

8. **« Historique client »** — filtre par client, tri date décroissante.
9. **« Relances sans réponse après J+15 »** — filtre `Réponse = Aucune` ET date < aujourd'hui - 15 j.

## Tableau de bord (page « Dashboard » reliée aux bases)

Indicateurs à afficher (widgets « Linked database » filtrés, ou formules de rollup dans une table « Stats » dédiée) :

| KPI | Comment l'obtenir |
|---|---|
| **Encours impayé total** | Rollup : somme des montants des Impayés `Statut != Résolu` |
| **Nombre de factures impayées** | Count des Impayés ouverts |
| **Répartition par tranche** | 4 compteurs (0–30, 31–60, 61–90, > 90 j) |
| **Taux de recouvrement du mois** | (Paiements reçus ce mois) / (Factures émises ce mois) |
| **DSO (délai moyen de paiement)** | moyenne de `date paiement - date facture` sur les factures payées du trimestre |
| **% de clients avec au moins 1 impayé** | count clients avec impayé / count clients total |
| **Relances effectuées cette semaine** | count dans Relances, filtre date cette semaine |
| **Montant recouvré ce mois-ci** | sum Paiements du mois en cours |
| **Ancienneté moyenne de l'encours** | moyenne de `Ancienneté` sur impayés ouverts |
| **Prochaines actions à venir** | liste filtrée `Prochaine action` = aujourd'hui / demain |

Astuce Notion : créez une table « Stats » avec des formules `count`/`sum` sur les relations, puis affichez-la en vue galerie avec les valeurs en grand.
