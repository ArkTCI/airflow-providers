"""
Example DAG demonstrating the usage of the FileMaker Cloud provider.

This DAG shows how to use the FileMaker Cloud provider to extract data
from a FileMaker Cloud database and process it.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator
from airflow.providers.filemaker.sensors.filemaker import FileMakerDataSensor


# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# Function to process the data
def process_data(**context):
    """Process the data extracted from FileMaker Cloud."""
    data = context["ti"].xcom_pull(task_ids="extract_data")
    if not data or "value" not in data:
        return {"processed": False, "count": 0}

    records = data["value"]
    record_count = len(records)

    # Simple processing example
    processed_data = [{"id": record.get("id"), "processed": True} for record in records]

    return {"processed": True, "count": record_count, "data": processed_data}


# Create the DAG
with DAG(
    "example_filemaker",
    default_args=default_args,
    description="Example DAG demonstrating FileMaker Cloud provider",
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["example", "filemaker"],
) as dag:

    # Check if data is available
    check_data = FileMakerDataSensor(
        task_id="check_data",
        table="Customers",  # Replace with your actual table name
        condition="CreatedDate ge 2023-01-01",  # Replace with your condition
        expected_count=1,
        filemaker_conn_id="filemaker_default",
        poke_interval=300,  # Check every 5 minutes
        timeout=60 * 60 * 2,  # Timeout after 2 hours
        mode="reschedule",  # Release worker slot while waiting
    )

    # Extract data from FileMaker Cloud
    extract_data = FileMakerExtractOperator(
        task_id="extract_data",
        endpoint="Customers?$filter=CreatedDate ge 2023-01-01&$orderby=CreatedDate desc",  # Replace with your endpoint
        filemaker_conn_id="filemaker_default",
    )

    # Process the extracted data
    process_data_task = PythonOperator(
        task_id="process_data",
        python_callable=process_data,
        provide_context=True,
    )

    # Define task dependencies
    check_data >> extract_data >> process_data_task
