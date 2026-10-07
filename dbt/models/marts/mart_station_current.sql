-- État de chaque station à sa dernière remontée chargée dans BigQuery (rafraîchi toutes les 3 heures).
-- Table lue par la carte « état actuel » du tableau de bord.

with last_report as (
    select *
    from {{ ref('fct_station_status') }}
    qualify row_number() over (partition by station_id order by last_reported_at desc) = 1
)

select
    last_report.station_id,
    station.station_name,
    station.capacity,
    last_report.num_bikes_available,
    last_report.num_docks_available,
    last_report.is_installed,
    last_report.is_renting,
    last_report.last_reported_at,
    -- Heure de Paris, lisible dans l'info-bulle de la carte.
    format_timestamp('%d/%m %H:%M', last_report.last_reported_at, 'Europe/Paris') as last_report_label,
    -- Libellé de l'info-bulle : la carte n'affiche qu'une dimension.
    concat(
        station.station_name,
        ' (remontée du ',
        format_timestamp('%d/%m à %H:%M', last_report.last_reported_at, 'Europe/Paris'),
        ')'
    ) as station_label,
    concat(cast(station.latitude as string), ',', cast(station.longitude as string)) as location
from last_report
inner join {{ ref('dim_station') }} as station
    on last_report.station_id = station.station_id
    and station.is_current
