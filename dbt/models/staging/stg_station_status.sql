-- Une ligne par message Kafka : l'état d'une station à une remontée.
-- Garantie « au moins une fois » : un même message peut apparaître plusieurs fois,
-- le dédoublonnage est fait dans fct_station_status.

select
    string(payload.station_id) as station_id,
    int64(payload.num_bikes_available) as num_bikes_available,
    int64(payload.num_docks_available) as num_docks_available,
    bool(payload.is_installed) as is_installed,
    bool(payload.is_renting) as is_renting,
    bool(payload.is_returning) as is_returning,
    timestamp(string(payload.last_reported)) as last_reported_at,
    timestamp(string(payload.feed_updated_at)) as feed_updated_at,
    ingestion_date
from {{ source('vlille_raw', 'raw_station_status_stream') }}
where ingestion_date >= '{{ var("start_date") }}'
