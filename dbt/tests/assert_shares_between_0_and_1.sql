-- Les parts vide et pleine sont des proportions.

select *
from {{ ref('mart_station_daily') }}
where share_empty not between 0 and 1
    or share_full not between 0 and 1
