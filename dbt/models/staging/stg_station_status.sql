-- Une ligne par station et par relevé du flux station_status.

with raw as (
    select
        last_updated,
        payload
    from {{ source('vlille_raw', 'raw_station_status') }}
    where date(last_updated) >= '{{ var("start_date") }}'
)

select
    string(station.station_id) as station_id,
    int64(station.num_bikes_available) as num_bikes_available,
    int64(station.num_docks_available) as num_docks_available,
    bool(station.is_installed) as is_installed,
    bool(station.is_renting) as is_renting,
    bool(station.is_returning) as is_returning,
    timestamp_seconds(int64(station.last_reported)) as last_reported_at,
    raw.last_updated as feed_updated_at
from raw
cross join unnest(json_query_array(raw.payload, '$.data.stations')) as station
