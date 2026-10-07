-- One mart row per station and day.

select
    report_date,
    station_id,
    count(*) as occurrences
from {{ ref('mart_station_daily') }}
group by report_date, station_id
having count(*) > 1
