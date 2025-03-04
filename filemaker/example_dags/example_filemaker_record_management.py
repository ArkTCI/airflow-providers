"""
Example DAG demonstrating FileMaker record management operators.

This DAG shows how to use the FileMaker operators to create, update, and delete records,
as well as perform bulk operations and execute FileMaker scripts.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.providers.filemaker.operators.filemaker import (
    FileMakerBulkCreateOperator,
    FileMakerCreateRecordOperator,
    FileMakerDeleteRecordOperator,
    FileMakerExecuteFunctionOperator,
    FileMakerQueryOperator,
    FileMakerUpdateRecordOperator,
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "example_filemaker_record_management",
    default_args=default_args,
    description="Example DAG demonstrating FileMaker record management operations",
    schedule_interval=None,
    start_date=datetime(2022, 1, 1),
    catchup=False,
    tags=["example", "filemaker"],
) as dag:

    # Create a new record
    create_record = FileMakerCreateRecordOperator(
        task_id="create_record",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        record_data={
            "FirstName": "John",
            "LastName": "Doe",
            "Email": "john.doe@example.com",
            "Grade": "A",
        },
    )

    # Query to verify the record was created
    query_record = FileMakerQueryOperator(
        task_id="query_record",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        query={"Email": "john.doe@example.com"},
    )

    # Update the record
    update_record = FileMakerUpdateRecordOperator(
        task_id="update_record",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        record_id="{{ ti.xcom_pull(task_ids='create_record')['recordId'] }}",
        record_data={
            "Grade": "A+",
            "Notes": "Updated via Airflow",
        },
    )

    # Create multiple records in bulk
    bulk_create = FileMakerBulkCreateOperator(
        task_id="bulk_create",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        records_data=[
            {
                "FirstName": "Jane",
                "LastName": "Smith",
                "Email": "jane.smith@example.com",
                "Grade": "B+",
            },
            {
                "FirstName": "Bob",
                "LastName": "Johnson",
                "Email": "bob.johnson@example.com",
                "Grade": "C",
            },
        ],
    )

    # Execute a FileMaker script
    execute_script = FileMakerExecuteFunctionOperator(
        task_id="execute_script",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        script_name="UpdateGrades",
        script_params={
            "gradeThreshold": "C",
            "newGrade": "C+",
        },
    )

    # Delete the record
    delete_record = FileMakerDeleteRecordOperator(
        task_id="delete_record",
        filemaker_conn_id="filemaker_default",
        database="students",
        layout="students",
        record_id="{{ ti.xcom_pull(task_ids='create_record')['recordId'] }}",
    )

    # Set task dependencies
    create_record >> query_record >> update_record >> bulk_create >> execute_script >> delete_record
