-- Le mart ne doit contenir qu'une ligne par station et par jour.

select
    report_date,
    station_id,
    count(*) as occurrences
from {{ ref('mart_station_daily') }}
group by report_date, station_id
having count(*) > 1
