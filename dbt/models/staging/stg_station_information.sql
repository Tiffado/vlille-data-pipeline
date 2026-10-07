-- One row per station and per station_information feed.

with raw as (
    select
        last_updated,
        payload
    from {{ source('vlille_raw', 'raw_station_information') }}
    where date(last_updated) >= '{{ var("start_date") }}'
)

select
    string(station.station_id) as station_id,
    string(station.name) as station_name,
    int64(station.capacity) as capacity,
    float64(station.lat) as latitude,
    float64(station.lon) as longitude,
    string(station.post_code) as post_code,
    raw.last_updated as feed_updated_at
from raw
cross join unnest(json_query_array(raw.payload, '$.data.stations')) as station
