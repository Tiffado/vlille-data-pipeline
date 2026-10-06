# 0003 — GCP : région, authentification et maîtrise des coûts

- Date : 2026-10-06
- Statut : accepté

## Contexte
Projet personnel sur un compte GCP facturé à titre privé : le coût doit rester proche de zéro et aucun
secret ne doit pouvoir fuiter. La facturation est néanmoins activée, car le sandbox BigQuery interdit
le DML (`MERGE`), nécessaire aux modèles incrémentaux et snapshots dbt.

## Décision
- **Région unique `europe-west1`** pour le bucket GCS et les datasets BigQuery.
- **Authentification sans clé** : Application Default Credentials en local
  (`gcloud auth application-default login`) ; la CI n'accède pas à GCP (tests sans réseau).
- **Budget** de 5 € par mois sur le compte de facturation, alertes à 50 %, 90 %, 100 % du coût réel
  et 100 % du coût prévisionnel.
- Seules les API utilisées sont activées (BigQuery, Cloud Storage, Billing Budget).
- Kafka et Airflow tournent en local sous Docker, pas en service managé.

## Justification
- Bucket et dataset dans la même région : chargements sans transfert inter-régions.
- `europe-west1` : tarifs inférieurs à `europe-west9` (Paris), services complets.
- Aucune clé de service account : rien à faire fuiter, rien à faire tourner.
- Cloud Composer et Kafka managé coûtent plusieurs dizaines d'euros par mois au minimum.

## Alternatives écartées
- Régions américaines : niveau gratuit Cloud Storage, mais données européennes hébergées hors d'Europe
  pour un gain de quelques centimes.
- Clé JSON de service account : secret longue durée, risque de fuite.
- Plafond de dépenses GCP (spend cap) : disponible seulement pour quelques services (Gemini API,
  Vertex AI, Cloud Run, Cloud Run Functions), pas pour BigQuery ni Cloud Storage.

## Conséquences
- Le budget alerte, il ne coupe pas : les coûts restent bas par conception (partitionnement avec filtre
  obligatoire, cycle de vie sur la zone brute).
- Le stockage GCS en Europe est payant dès le premier octet (quelques centimes par mois attendus).
- Le déploiement n'est pas un environnement de production : Kafka et Airflow locaux tournent quand le
  poste est allumé.
