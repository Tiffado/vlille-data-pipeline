-- Daily saturation of each station (Paris time), read by the dashboard.
-- Shares are computed on the number of reports, an approximation of the share of time.

with reports as (
    select
        status.station_id,
        status.last_reported_at,
        status.num_bikes_available,
        status.num_docks_available,
        station.station_name,
        station.capacity,
        station.latitude,
        station.longitude
    from {{ ref('fct_station_status') }} as status
    -- Station version valid at report time (SCD2 range join).
    inner join {{ ref('dim_station') }} as station
        on status.station_id = station.station_id
        and status.last_reported_at >= station.valid_from
        and status.last_reported_at < station.valid_to
    where status.is_installed
        -- Out-of-service stations can publish very old reports.
        and date(status.last_reported_at) >= '{{ var("start_date") }}'
),

daily as (
    select
        date(last_reported_at, 'Europe/Paris') as report_date,
        station_id,
        any_value(station_name) as station_name,
        max(capacity) as capacity,
        any_value(latitude) as latitude,
        any_value(longitude) as longitude,
        count(*) as nb_reports,
        round(countif(num_bikes_available = 0) / count(*), 3) as share_empty,
        round(countif(num_docks_available = 0) / count(*), 3) as share_full,
        round(avg(num_bikes_available), 1) as avg_bikes_available
    from reports
    group by report_date, station_id
)

select
    *,
    -- "lat,lon" text, recognised as a geo field by Data Studio.
    concat(cast(latitude as string), ',', cast(longitude as string)) as location,
    case
        when share_empty >= {{ var('rebalancing_threshold') }} then 'apporter des vélos'
        when share_full >= {{ var('rebalancing_threshold') }} then 'retirer des vélos'
        else 'aucun'
    end as rebalancing_need
from daily
