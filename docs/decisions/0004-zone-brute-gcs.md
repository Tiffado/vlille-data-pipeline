# 0004 — Zone brute dans Cloud Storage

- Date : 2026-10-06
- Statut : accepté

## Contexte
Les réponses GBFS doivent être conservées telles que reçues avant tout chargement dans BigQuery :
pour pouvoir rejouer un chargement, analyser une anomalie de la source et découpler la collecte du
chargement. La collecte peut être relancée plusieurs fois sur le même état de la source.

## Décision
- Bucket `gs://vlille-pipeline-raw` (`europe-west1`, classe Standard), accès uniforme au niveau du
  bucket, accès public bloqué.
- Une réponse = un objet, contenu inchangé, compressé en gzip.
- Nom déduit du `last_updated` du flux, partitionné par jour à la manière de Hive :
  `gbfs/<flux>/dt=AAAA-MM-JJ/<flux>_<AAAAMMJJTHHMMSSZ>.json.gz`.
- Écriture conditionnelle (`if_generation_match=0`) : un objet existant n'est jamais réécrit.
- Archivage avant validation : une réponse invalide est conservée, la commande se termine en erreur.
- Règle de cycle de vie : suppression après 30 jours (`infra/gcs-lifecycle.json`).

## Justification
- Nom issu de la source et non de l'heure de collecte : deux collectes du même état produisent le même
  objet, sans doublon (idempotence).
- Compression avec date d'en-tête fixée (`mtime=0`) : même contenu, mêmes octets.
- L'écriture conditionnelle est atomique côté GCS : pas de course entre vérification et écriture.
- Le partitionnement `dt=` permet de ne lire, recharger ou purger qu'un jour.
- Volume mesuré : environ 3 Ko compressés par réponse `station_status` (environ 100 Ko en JSON).

## Alternatives écartées
- Stocker l'objet validé plutôt que la réponse : on perdrait la preuve de ce qui a été reçu en cas
  d'anomalie.
- Nommer par l'heure de collecte : chaque relance créerait un doublon.
- Conservation illimitée : coût croissant ; les données restent disponibles dans BigQuery.

## Conséquences
- Une réponse sans `last_updated` lisible ne peut pas être nommée : elle n'est pas archivée et la
  collecte échoue.
- Au-delà de 30 jours, un rechargement depuis le brut n'est plus possible.
- À une collecte par minute, le coût dominant est celui des opérations d'écriture (quelques dizaines
  de centimes par mois), pas celui du stockage.
