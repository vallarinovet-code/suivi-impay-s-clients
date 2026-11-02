# 01 — Structure des bases (tables, champs, liens)

Base unique : **« Suivi impayés — [Nom de la clinique] »**

## Table 1 — Clients

| Champ | Type (Notion / Airtable) | Détail |
|---|---|---|
| ID client | Formule / Autonumber | Ex. `CLI-001` (Airtable : champ autonumber) |
| Nom | Texte | |
| Prénom | Texte | |
| Téléphone | Téléphone | Format FR |
| Email | Email | |
| Adresse | Texte | |
| Code postal | Texte | |
| Ville | Texte | |
| Animaux | Lien → Animaux | Plusieurs |
| Factures | Lien → Factures (lookup) | Toutes |
| Nb factures impayées | Rollup (count, filtre statut = impayée) | |
| Total impayé | Rollup (sum « Reste dû », filtre impayé) | |
| Consentement relance | Case à cocher | Email/SMS/courrier — requis RGPD |
| Canal de relance préféré | Sélection : Email / SMS / Courrier / Téléphone | |
| Mode de paiement habituel | Sélection : CB / Virement / Chèque / Espèces / Autre | |
| Notes | Texte long | Ex. accord d'échelonnement en cours |
| Statut | Sélection : Actif / Inactif / Litige | |

## Table 2 — Animaux

| Champ | Type | Détail |
|---|---|---|
| ID animal | Autonumber | Ex. `ANI-001` |
| Nom | Texte | |
| Espèce | Sélection : Chien / Chat / NAC / Équin / Bovin / Autre | |
| Race | Texte | |
| Sexe | Sélection : M / F / M stérilisé / F stérilisée | |
| Date de naissance | Date | |
| N° d'identification (puce) | Texte | |
| Propriétaire | Lien → Clients (obligatoire) | |
| Notes | Texte long | Allergies, antécédents utiles pour le recouvrement (ex. soins en urgence) |

## Table 3 — Factures

| Champ | Type | Détail |
|---|---|---|
| N° facture | Autonumber / Texte | Format `FAC-2026-0001` |
| Date de facture | Date | |
| Client | Lien → Clients | |
| Animal(x) concerné(s) | Lien → Animaux | Plusieurs possibles |
| Prestation / motif | Texte long | Ex. « Consultation + vaccination CHPPI », « Chirurgie stérilisation », « Aliments thérapeutiques renal 12 kg » |
| Catégorie | Sélection : Consultation / Vaccination / Chirurgie / Imagerie / Analyses / Hospitalisation / Pharmacie / Alimentation / Pension / Autre | |
| Montant HT | Devise (EUR) | |
| TVA (%) | Nombre | 10 % (soins) ou 20 % (marchandises) selon la ligne |
| Montant TTC | Formule | `Montant HT * (1 + TVA/100)` |
| Acompte versé | Devise | Montant versé à la facturation |
| Paiements reçus | Rollup (sum → Paiements.Montant) | |
| **Reste dû** | **Formule** | `MAX(0, Montant TTC - Acompte versé - Paiements reçus)` |
| Date d'échéance | Formule | `Date de facture + 30 jours` (ajuster selon CGV) |
| Moyen de paiement prévu | Sélection | Idem client |
| Statut | Sélection : Payée / Partielle / Impayée / Avoir / Litige | Formule possible : `SI Reste dû = 0 → Payée ; SI Reste dû < TTC → Partielle ; sinon Impayée` |
| Envoyée le / par | Date + Sélection (Email / Papier / Portail client) | |
| Notes | Texte long | |

## Table 4 — Paiements

| Champ | Type | Détail |
|---|---|---|
| ID paiement | Autonumber | `PAY-001` |
| Date | Date | |
| Facture | Lien → Factures | |
| Client (lookup via facture) | Lookup | |
| Montant | Devise | |
| Moyen | Sélection : CB / Virement / Chèque / Espèces / Avoir / Autre | |
| Référence (chèque, virement) | Texte | |
| Notes | Texte | |

## Table 5 — Impayés (cœur du dispositif)

| Champ | Type | Détail |
|---|---|---|
| ID impayé | Autonumber | `IMP-001` |
| Facture | Lien → Factures | Une facture = un impayé (créer quand statut passe à Impayée) |
| Client (lookup) | Lookup | |
| Montant impayé | Lookup de « Reste dû » (ou formule) | |
| Date d'échéance | Lookup | |
| **Ancienneté (jours)** | **Formule** | `TODAY() - Date d'échéance` (positif = en retard) |
| **Tranche** | **Formule** | `SI ancienneté < 0 → "À échoir" ; <=30 → "0–30 j" ; <=60 → "31–60 j" ; <=90 → "61–90 j" ; sinon "> 90 j"` |
| Niveau de relance atteint | Sélection : Aucun / J+7 / J+15 / J+30 (mise en demeure) / J+60 / Recouvrement externe | |
| Dernière relance (rollup max date Relances) | Rollup | |
| **Prochaine action** | Formule | Selon le niveau : J+7 email, J+15 email+SMS, J+30 LRAR, J+60 échelonnement ou injonction |
| Date de prochaine action | Formule | `SI tranche = 0–30 j → échéance+7 ; 31–60 → échéance+15 ; 61–90 → échéance+30 ; >90 → échéance+60` |
| Responsable | Personne (Notion) / Collaborateur (Airtable) | Secrétaire, vétérinaire ou gérant |
| Statut | Sélection : Ouvert / En cours / Échelonnement signé / Résolu / Litige / Recouvrement externe / Irrécouvrable | |
| Date de clôture | Date | Renseignée quand Résolu / Irrécouvrable |
| Notes | Texte long | Réponses du client, promesses de paiement, litiges |

## Table 6 — Relances (historique de toutes les actions)

| Champ | Type | Détail |
|---|---|---|
| ID relance | Autonumber | `REL-001` |
| Date et heure | Date (avec heure) | |
| Impayé | Lien → Impayés | |
| Client (lookup) | Lookup | |
| Canal | Sélection : Téléphone / Email / SMS / Courrier simple / LRAR / Visite | |
| Effectuée par | Personne / Collaborateur | |
| Contact | Texte | Nom de la personne jointe |
| Résumé | Texte long | Ce qui a été dit / écrit |
| Réponse du client | Sélection : Aucune / Promesse de payer (date) / Paiement partiel / Contestation / Demande d'échelonnement / Injoignable | |
| Date de promesse de paiement | Date | Si promesse |
| Résultat | Sélection : À relancer / En attente / Résolu / Escalader | |
| Pièces jointes (email, LRAR) | Fichier | Preuve d'envoi indispensable |

## Liens entre tables

- Clients 1—n Animaux, Clients 1—n Factures, Factures 1—n Paiements, Factures 1—1 Impayés, Impayés 1—n Relances.
- Dans Airtable : champs de type « Linked record ». Dans Notion : propriétés « Relation » + « Rollup ».
