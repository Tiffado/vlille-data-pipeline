-- Station versions from the SCD2 snapshot, with a validity period for range joins.
-- The first version is valid from 1970: the snapshot started after the first reports.

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
