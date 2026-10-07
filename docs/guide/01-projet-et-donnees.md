# 1. Le projet et les données

## Objectif

Suivre la disponibilité des stations V'Lille (vélos en libre-service de la métropole lilloise) pour
répondre à deux questions :

- quelles stations sont souvent **vides** (aucun vélo) ou **pleines** (aucune place pour rendre) ;
- lesquelles demandent un **rééquilibrage** (apporter ou retirer des vélos).

## La source : un flux GBFS

[GBFS](https://gbfs.org/) (*General Bikeshare Feed Specification*) est un standard ouvert, utilisé par
des centaines de réseaux de vélos et trottinettes partagés. Un réseau publie un fichier d'entrée,
`gbfs.json`, qui liste des flux JSON. Ilévia publie celui de V'Lille sans clé d'accès, sous Licence
Ouverte 2.0 (jeu de données référencé sur
[data.gouv.fr](https://www.data.gouv.fr/datasets/vlille-disponibilite-en-temps-reel-3)).

Point d'entrée : <https://media.ilevia.fr/opendata/gbfs.json>

```json
{
  "ttl": 0,
  "version": "2.3",
  "data": {
    "en": {
      "feeds": [
        { "name": "station_information", "url": "https://media.ilevia.fr/opendata/station_information.json" },
        { "name": "station_status",      "url": "https://media.ilevia.fr/opendata/station_status.json" }
      ]
    }
  },
  "last_updated": 1791299520
}
```

Le projet utilise deux flux :

| Flux | Contenu | Rôle en modélisation |
|---|---|---|
| `station_information` | 268 stations : identifiant, nom, capacité, latitude, longitude | **dimension** (référentiel), collecté par le batch |
| `station_status` | par station : vélos disponibles, places libres, état, date de dernière remontée | **faits** (mesures horodatées), collecté par Kafka |

Exemple de statut d'une station :

```json
{
  "station_id": "2",
  "num_bikes_available": 0,
  "num_docks_available": 31,
  "is_installed": true,
  "is_renting": true,
  "is_returning": true,
  "last_reported": 1791299410
}
```

Les horodatages sont en secondes depuis le 1er janvier 1970 (epoch), en UTC.

## Particularités observées

- `ttl` vaut 0 : le flux n'indique pas sa durée de validité, la cadence de collecte est à notre choix.
- Une station qui n'a rien remonté entre deux lectures réapparaît avec le même `last_reported` : il
  faut dédoublonner sur `(station_id, last_reported)`.
- Une station figure dans le référentiel sans aucun statut, et une douzaine sont hors service
  (`is_installed` ou `is_renting` à faux) : cas de qualité de données traités par des tests et filtres.

## Pour voir

- Les flux bruts dans un navigateur :
  [station_status.json](https://media.ilevia.fr/opendata/station_status.json),
  [station_information.json](https://media.ilevia.fr/opendata/station_information.json).
- Des extraits réduits à 3 stations servent aux tests : [`tests/fixtures/`](../../tests/fixtures/).

Décision correspondante : [ADR 0001](../decisions/0001-source-gbfs-vlille.md).
