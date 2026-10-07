-- Une station ne doit apparaître qu'une fois par relevé. Le test échoue s'il renvoie des lignes.

select
    station_id,
    feed_updated_at,
    count(*) as occurrences
from {{ ref('stg_station_status') }}
group by station_id, feed_updated_at
having count(*) > 1
