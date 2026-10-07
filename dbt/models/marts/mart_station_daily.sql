-- Saturation quotidienne de chaque station (jour à l'heure de Paris).
-- Les parts sont calculées sur le nombre de remontées, approximation de la part du temps.

with reports as (
    select
        status.station_id,
        status.last_reported_at,
        status.num_bikes_available,
        status.num_docks_available,
        station.station_name,
        station.capacity
    from {{ ref('fct_station_status') }} as status
    -- Version de la station valable au moment de la remontée (jointure SCD2).
    inner join {{ ref('dim_station') }} as station
        on status.station_id = station.station_id
        and status.last_reported_at >= station.valid_from
        and status.last_reported_at < station.valid_to
    where status.is_installed
),

daily as (
    select
        date(last_reported_at, 'Europe/Paris') as report_date,
        station_id,
        any_value(station_name) as station_name,
        max(capacity) as capacity,
        count(*) as nb_reports,
        round(countif(num_bikes_available = 0) / count(*), 3) as share_empty,
        round(countif(num_docks_available = 0) / count(*), 3) as share_full,
        round(avg(num_bikes_available), 1) as avg_bikes_available
    from reports
    group by report_date, station_id
)

select
    *,
    case
        when share_empty >= {{ var('rebalancing_threshold') }} then 'apporter des vélos'
        when share_full >= {{ var('rebalancing_threshold') }} then 'retirer des vélos'
    end as rebalancing_need
from daily
