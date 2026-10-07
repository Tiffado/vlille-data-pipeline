-- One fact row per station report.

select
    station_id,
    last_reported_at,
    count(*) as occurrences
from {{ ref('fct_station_status') }}
group by station_id, last_reported_at
having count(*) > 1
