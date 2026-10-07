-- Une ligne par remontée réelle d'une station : (station_id, last_reported_at).
-- Une station sans nouvelle information entre deux relevés n'est comptée qu'une fois.

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
    -- Relit les dernières 24 heures : un relevé chargé en retard est rattrapé, et la clé unique
    -- évite les doublons sur les lignes déjà présentes.
    where feed_updated_at >= (
        select timestamp_sub(max(last_reported_at), interval 24 hour) from {{ this }}
    )
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
-- Une même remontée peut figurer dans plusieurs relevés : on n'en garde qu'une.
qualify row_number() over (
    partition by station_id, last_reported_at order by feed_updated_at
) = 1
