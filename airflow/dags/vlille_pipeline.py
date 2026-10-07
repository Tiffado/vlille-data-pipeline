"""DAG vlille_pipeline : référentiel des stations, chargement dans BigQuery, puis modèles dbt.

Toutes les 3 heures. Les disponibilités arrivent en continu par Kafka (conteneurs producer et
consumer) dans la zone brute ; ce DAG collecte le référentiel, charge les deux sources dans BigQuery
et reconstruit les modèles. Les commandes du projet sont installées dans l'image Airflow, dans un
environnement Python séparé (/opt/vlille/.venv).
"""

from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

VENV_BIN = "/opt/vlille/.venv/bin"
DBT_DIR = "/opt/vlille/dbt"

with DAG(
    dag_id="vlille_pipeline",
    description="Référentiel V'Lille + événements Kafka → BigQuery → dbt build",
    # Toutes les 3 heures : le mart est quotidien, et dbt (modèles et tests) reste ainsi dans le
    # quota gratuit de BigQuery malgré le volume des événements Kafka.
    schedule=timedelta(hours=3),
    start_date=datetime(2026, 10, 7),
    # La collecte lit l'état actuel de l'API : rejouer des créneaux passés n'a pas de sens.
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=2)},
    tags=["vlille"],
) as dag:
    # Référentiel des stations uniquement ; les disponibilités viennent de Kafka.
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
