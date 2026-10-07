-- Une ligne par remontée réelle d'une station : (station_id, last_reported_at).
-- Les messages Kafka en double (garantie au moins une fois) ne sont comptés qu'une fois.

{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key=['station_id', 'last_reported_at'],
        partition_by={'field': 'last_reported_at', 'data_type': 'timestamp', 'granularity': 'day'}
    )
}}

with status as (
    select *
    from {{ ref('stg_station_status') }}
    {% if is_incremental() %}
    -- Relit les deux derniers jours de la table brute : un chargement en retard est rattrapé, et la
    -- clé unique évite les doublons sur les lignes déjà présentes. Filtrer sur la partition
    -- (ingestion_date) limite le volume lu.
    where ingestion_date >= date_sub(current_date(), interval 2 day)
    {% endif %}
)

select
    station_id,
    last_reported_at,
    num_bikes_available,
    num_docks_available,
    is_installed,
    is_renting,
    is_returning
from status
-- Une même remontée peut figurer plusieurs fois : on n'en garde qu'une.
qualify row_number() over (
    partition by station_id, last_reported_at order by feed_updated_at
) = 1
