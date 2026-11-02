# 06 — RGPD et durées de conservation

## Principes appliqués à cette base

- **Finalité** : les données servent uniquement au suivi des paiements et au recouvrement.
  Ne les utilisez pas pour du marketing sans consentement dédié.
- **Minimisation** : ne stockez que les données utiles (pas de copie de carte bancaire,
  pas de données de santé détaillées dans cette base — les antécédents médicaux restent
  dans le logiciel vétérinaire).
- **Accès restreint** : limitez la base aux personnes habilitées (secrétariat, gérant,
  comptable). Activez l'authentification forte sur Notion/Airtable.
- **Consentement relances** : le champ « Consentement relance » doit être coché pour les
  canaux automatisés (email/SMS). Pour le courrier, l'intérêt légitime du recouvrement
  s'applique, dans la limite de la finalité.
- **Droit d'accès, de rectification et d'effacement** : prévoyez une procédure pour répondre
  aux demandes des clients (délai légal : 1 mois).

## Durées de conservation recommandées

| Donnée | Durée | Justification |
|---|---|---|
| Fiches clients actives | Tant que le client est actif + 3 ans après la dernière prestation | Suivi et obligations comptables |
| Factures, paiements | **10 ans** | Obligation comptable et fiscale (art. L. 123-22 C. com.) |
| Impayés soldés | 5 ans après le solde | Prescription civile (art. 2224 C. civ.) |
| Preuves de relances (emails, LRAR, AR) | 5 ans après la dernière relance | Preuve en cas de litige, aligné sur la prescription |
| Impayés classés « irrécouvrables » | 10 ans (comptable) | Justificatif de créance irrécouvrée |
| Données de clients inactifs | Suppression ou anonymisation 3 ans après la dernière activité, sauf obligation légale | Minimisation (art. 5 RGPD) |

## Sauvegardes

- Exportez la base mensuellement (CSV) vers un emplacement chiffré interne.
- Ne stockez jamais cette base sur un compte personnel ; utilisez le compte professionnel
  de la structure.
