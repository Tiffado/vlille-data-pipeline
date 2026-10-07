-- La table de faits ne doit contenir qu'une ligne par remontée de station.

select
    station_id,
    last_reported_at,
    count(*) as occurrences
from {{ ref('fct_station_status') }}
group by station_id, last_reported_at
having count(*) > 1
