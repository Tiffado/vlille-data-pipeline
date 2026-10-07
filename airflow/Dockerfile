FROM apache/airflow:3.3.2-python3.12

# uv, à version fixe, copié depuis son image officielle.
COPY --from=ghcr.io/astral-sh/uv:0.12.23 /uv /usr/local/bin/uv

# Le projet est installé dans son propre environnement virtuel : ses dépendances (dbt,
# bibliothèques Google) restent séparées de celles d'Airflow.
WORKDIR /opt/vlille
ENV UV_PROJECT_ENVIRONMENT=/opt/vlille/.venv \
    UV_PYTHON_DOWNLOADS=never \
    UV_LINK_MODE=copy

COPY --chown=airflow:root pyproject.toml uv.lock .python-version README.md ./
COPY --chown=airflow:root src ./src
COPY --chown=airflow:root dbt ./dbt
RUN uv sync --locked --no-dev

WORKDIR /opt/airflow
