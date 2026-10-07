-- Dimension des stations issue du snapshot SCD2, prête pour une jointure par période.
-- La première version d'une station est considérée valable depuis toujours : le snapshot a démarré
-- après les premières remontées, et c'est le plus ancien état connu.

select
    station_id,
    station_name,
    capacity,
    latitude,
    longitude,
    post_code,
    case
        when row_number() over (partition by station_id order by dbt_valid_from) = 1
            then timestamp('1970-01-01')
        else dbt_valid_from
    end as valid_from,
    coalesce(dbt_valid_to, timestamp('9999-12-31')) as valid_to,
    dbt_valid_to is null as is_current
from {{ ref('snap_station') }}
