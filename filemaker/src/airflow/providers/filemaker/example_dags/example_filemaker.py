"""
Example DAG demonstrating the usage of FileMaker operators and hooks.

This DAG shows how to use the FileMaker provider to query data from FileMaker Cloud,
retrieve metadata schema, and monitor for changes.
"""

from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator

from airflow import DAG
from airflow.providers.filemaker.hooks.filemaker import FileMakerHook
from airflow.providers.filemaker.operators.filemaker import (
    FileMakerExtractOperator,
    FileMakerQueryOperator,
    FileMakerSchemaOperator,
)
from airflow.providers.filemaker.sensors.filemaker import (
    FileMakerChangeSensor,
    FileMakerDataSensor,
)

# Default arguments for the DAG
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

# Define the DAG
with DAG(
    "example_filemaker",
    default_args=default_args,
    description="Example DAG demonstrating FileMaker Cloud integration",
    schedule_interval=timedelta(days=1),
    catchup=False,
    tags=["example", "filemaker"],
) as dag:

    # Task 1: Retrieve the OData metadata schema
    get_metadata = FileMakerSchemaOperator(
        task_id="get_metadata_schema",
        filemaker_conn_id="filemaker_default",
    )

    # Task 2: Query records from a table with filtering
    query_records = FileMakerQueryOperator(
        task_id="query_students",
        filemaker_conn_id="filemaker_default",
        endpoint="Students",
        filter_query="GradeLevel eq '12'",
        top=100,
    )

    # Task 3: Extract data and save to a CSV file
    extract_data = FileMakerExtractOperator(
        task_id="extract_students_data",
        filemaker_conn_id="filemaker_default",
        endpoint="Students",
        output_path="/tmp/students_data.csv",
        output_format="csv",
    )

    # Task 4: Use a FileMaker sensor to wait for a condition
    wait_for_data = FileMakerDataSensor(
        task_id="wait_for_new_students",
        filemaker_conn_id="filemaker_default",
        endpoint="Students",
        filter_query="CreatedDate gt 2023-01-01",
        mode="poke",
        poke_interval=300,
        timeout=60 * 60 * 2,  # 2 hours
    )

    # Task 5: Use a Python function with FileMakerHook
    def process_filemaker_data(**context):
        """Process data from FileMaker using the hook directly."""
        hook = FileMakerHook(filemaker_conn_id="filemaker_default")
        # Get connection
        # conn = hook.get_conn()  # Unused connection object

        # Example 1: Get data with basic filtering and limit
        print("Example 1: Basic filtering with top")
        data = hook.get_records(table="Students", filter_query="GradeLevel eq '12'", top=10)
        # Log the results
        for record in data.get("value", []):
            print(f"Student: {record.get('Name')}, Grade: {record.get('GradeLevel')}")

        # Example 2: Get count of records
        print("\nExample 2: Getting count of records")
        count_data = hook.get_records(table="Students", filter_query="GradeLevel eq '12'", count=True)
        print(f"Total 12th grade students: {count_data.get('@odata.count', 0)}")

        # Example 3: Use apply for aggregations
        print("\nExample 3: Using apply for aggregations")
        aggregated_data = hook.get_records(
            table="Grades", apply="groupby((Subject), aggregate(Score with average as AverageScore))"
        )
        # Log the aggregated results
        for record in aggregated_data.get("value", []):
            print(f"Subject: {record.get('Subject')}, Average Score: {record.get('AverageScore')}")

        return data

    process_data = PythonOperator(
        task_id="process_filemaker_data",
        python_callable=process_filemaker_data,
    )

    # Task 6: Monitor for changes in a table
    monitor_changes = FileMakerChangeSensor(
        task_id="monitor_table_changes",
        filemaker_conn_id="filemaker_default",
        endpoint="Students",
        last_modified_field="ModificationTimestamp",
        reference_timestamp="{{ execution_date }}",
        mode="poke",
        poke_interval=300,
        timeout=60 * 60 * 2,  # 2 hours
    )

    # Define the task dependencies
    get_metadata >> query_records >> extract_data
    extract_data >> wait_for_data >> process_data
    process_data >> monitor_changes
