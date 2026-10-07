-- Latest known state of each station (one row per station).

select
    station_id,
    station_name,
    capacity,
    latitude,
    longitude,
    post_code,
    feed_updated_at
from {{ ref('stg_station_information') }}
qualify row_number() over (partition by station_id order by feed_updated_at desc) = 1
