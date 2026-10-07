"""DAG vlille_pipeline : collecte V'Lille, chargement dans BigQuery, puis modèles dbt.

Toutes les 30 minutes. Les commandes du projet sont installées dans l'image Airflow, dans un
environnement Python séparé (/opt/vlille/.venv).
"""

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

VENV_BIN = "/opt/vlille/.venv/bin"
DBT_DIR = "/opt/vlille/dbt"

with DAG(
    dag_id="vlille_pipeline",
    description="Collecte V'Lille → zone brute GCS → BigQuery → dbt build",
    schedule=timedelta(minutes=30),
    start_date=datetime(2026, 10, 7),
    # La collecte lit l'état actuel de l'API : rejouer des créneaux passés n'a pas de sens.
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["vlille"],
) as dag:
    collect = BashOperator(
        task_id="collect",
        bash_command=f"{VENV_BIN}/vlille-collect",
    )

    # Hier et aujourd'hui (UTC, à l'heure d'exécution) : le dernier fichier collecté avant minuit
    # est aussi chargé. La date d'exécution suffit puisque les créneaux passés ne sont pas rejoués.
    load = BashOperator(
        task_id="load",
        bash_command=(f"{VENV_BIN}/vlille-load --date $(date -u -d yesterday +%F) $(date -u +%F)"),
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=f"{VENV_BIN}/dbt build --project-dir {DBT_DIR} --profiles-dir {DBT_DIR}",
    )

    collect >> load >> dbt_build
