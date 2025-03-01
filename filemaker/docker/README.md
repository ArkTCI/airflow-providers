# Airflow with FileMaker Provider Docker Image

This Docker image is based on the official Apache Airflow image and includes the FileMaker provider pre-installed.

## Image Information

- Base Image: `apache/airflow:2.8.2-python3.9`
- FileMaker Provider: Included and ready to use
- Additional Python dependencies: All dependencies required by the FileMaker provider

## Usage

### Quick Start

```bash
docker pull ghcr.io/arktci/airflow-filemaker:latest
```

### Run with Docker Compose

Create a `docker-compose.yml` file:

```yaml
version: '3'
services:
  postgres:
    image: postgres:13
    environment:
      - POSTGRES_USER=airflow
      - POSTGRES_PASSWORD=airflow
      - POSTGRES_DB=airflow
    ports:
      - "5432:5432"
    volumes:
      - postgres-db-volume:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "airflow"]
      interval: 5s
      retries: 5

  airflow-webserver:
    image: ghcr.io/arktci/airflow-filemaker:latest
    depends_on:
      - postgres
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    ports:
      - "8080:8080"
    command: webserver
    healthcheck:
      test: ["CMD", "curl", "--fail", "http://localhost:8080/health"]
      interval: 10s
      timeout: 10s
      retries: 5

  airflow-scheduler:
    image: ghcr.io/arktci/airflow-filemaker:latest
    depends_on:
      - postgres
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
      - AIRFLOW__DATABASE__SQL_ALCHEMY_CONN=postgresql+psycopg2://airflow:airflow@postgres/airflow
      - AIRFLOW__WEBSERVER__SECRET_KEY=your_secret_key
    volumes:
      - ./dags:/opt/airflow/dags
      - ./logs:/opt/airflow/logs
      - ./plugins:/opt/airflow/plugins
    command: scheduler

volumes:
  postgres-db-volume:
```

### Run the image

```bash
docker-compose up -d
```

## FileMaker Provider Configuration

To use the FileMaker provider, you need to set up a connection in Airflow:

1. Navigate to the Airflow UI (default: http://localhost:8080)
2. Go to Admin > Connections
3. Add a new connection:
   - Connection Id: `filemaker_default` (or your custom ID)
   - Connection Type: `FileMaker`
   - Host: Your FileMaker Cloud/Server host
   - Login: Your username
   - Password: Your password
   - Schema: Your database name

## Example DAG

Here's a simple example DAG using the FileMaker provider:

```python
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'filemaker_extract_example',
    default_args=default_args,
    description='Example DAG using FileMaker provider',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
)

extract_data = FileMakerExtractOperator(
    task_id='extract_filemaker_data',
    conn_id='filemaker_default',
    layout='YourLayout',
    query={'YourField': 'YourValue'},
    output_format='json',
    dag=dag,
)
```

## Building the Image Locally

If you want to build the image yourself:

```bash
cd /path/to/airflow-providers/filemaker
docker build -t airflow-filemaker:local .
```

## Versioning

The Docker image follows the same version numbering as the FileMaker provider package. 