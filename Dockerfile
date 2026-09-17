FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /dbt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dbt_project.yml .
COPY profiles.yml .
COPY models/ models/
COPY app.py .
ENV DBT_PROFILES_DIR=/dbt
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD dbt --version || exit 1
ENTRYPOINT ["dbt"]
CMD ["run"]
