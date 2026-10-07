"""vlille_pipeline: station reference data, load into BigQuery, then dbt, every 3 hours.

Station availability arrives continuously through Kafka (producer and consumer containers). The
project commands are installed in the Airflow image, in a separate virtualenv (/opt/vlille/.venv).
"""

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

VENV_BIN = "/opt/vlille/.venv/bin"
DBT_DIR = "/opt/vlille/dbt"

with DAG(
    dag_id="vlille_pipeline",
    description="Référentiel V'Lille + événements Kafka → BigQuery → dbt build",
    # Every 3 hours keeps dbt within the BigQuery free tier; the marts are daily anyway.
    schedule=timedelta(hours=3),
    start_date=datetime(2026, 10, 7),
    # The collection reads the current API state: replaying past slots makes no sense.
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["vlille"],
) as dag:
    collect = BashOperator(
        task_id="collect",
        bash_command=f"{VENV_BIN}/vlille-collect",
    )

    # Yesterday and today (UTC), so files written just before midnight are loaded too.
    load = BashOperator(
        task_id="load",
        bash_command=(f"{VENV_BIN}/vlille-load --date $(date -u -d yesterday +%F) $(date -u +%F)"),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{VENV_BIN}/dbt build --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )

    collect >> load >> dbt_build
