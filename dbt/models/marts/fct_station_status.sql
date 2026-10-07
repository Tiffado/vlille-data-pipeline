-- One row per station report (station_id, last_reported_at); Kafka duplicates are removed.

{{
    config(
        materialized='incremental',
        incremental_strategy='merge',
        unique_key=['station_id', 'last_reported_at'],
        partition_by={'field': 'last_reported_at', 'data_type': 'timestamp', 'granularity': 'day'}
    )
}}

with status as (
    select *
    from {{ ref('stg_station_status') }}
    {% if is_incremental() %}
    -- Re-read the last two days of partitions to catch late loads; the merge key avoids duplicates.
    where ingestion_date >= date_sub(current_date(), interval 2 day)
    {% endif %}
)

select
    station_id,
    last_reported_at,
    num_bikes_available,
    num_docks_available,
    is_installed,
    is_renting,
    is_returning
from status
qualify row_number() over (
    partition by station_id, last_reported_at order by feed_updated_at
) = 1
