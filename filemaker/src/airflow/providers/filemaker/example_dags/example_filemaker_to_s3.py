"""
Example DAG demonstrating FileMaker to S3 data transfer.

This DAG shows how to extract data from FileMaker Cloud and upload it to Amazon S3.
"""

from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook

from airflow import DAG
from airflow.providers.filemaker.hooks.filemaker import FileMakerHook

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
    "example_filemaker_to_s3",
    default_args=default_args,
    description="Example DAG demonstrating FileMaker to S3 data transfer",
    schedule_interval="@daily",
    catchup=False,
    tags=["example", "filemaker", "s3", "transfer"],
) as dag:

    # Function to extract data from FileMaker and upload to S3
    def extract_filemaker_to_s3(**context):
        """
        Extract data from FileMaker and upload to S3.

        This function uses FileMakerHook to query data and S3Hook to upload it.
        """
        # Task instance
        # ti = context["ti"]  # Unused task instance variable

        # Extract execution date as string for partitioning
        execution_date = context["ds_nodash"]

        # Initialize hooks
        filemaker_hook = FileMakerHook(filemaker_conn_id="filemaker_default")
        s3_hook = S3Hook(aws_conn_id="aws_default")

        # Define S3 path
        s3_bucket = "my-data-lake"
        s3_key = f"filemaker_exports/students/{execution_date}/students_export.json"

        # Query FileMaker data
        students_data = filemaker_hook.get_records(
            table="Students",
            filter_query="Active eq true",
            expand="Enrollments,Grades",
            count=True,  # Get total count of records that match the filter
        )

        # Log the total count of records
        total_count = students_data.get("@odata.count", 0)
        print(f"Total active students: {total_count}")

        # Convert to JSON string
        import json

        json_data = json.dumps(students_data)

        # Upload to S3
        s3_hook.load_string(string_data=json_data, key=s3_key, bucket_name=s3_bucket, replace=True)

        # Log the results
        record_count = len(students_data.get("value", []))
        print(f"Extracted {record_count} records from FileMaker")
        print(f"Uploaded data to s3://{s3_bucket}/{s3_key}")

        # Return metadata for downstream tasks
        return {"record_count": record_count, "s3_uri": f"s3://{s3_bucket}/{s3_key}"}

    # Task to extract data from FileMaker and upload to S3
    extract_and_upload = PythonOperator(
        task_id="extract_filemaker_to_s3",
        python_callable=extract_filemaker_to_s3,
    )

    # Function to process the data in S3
    def process_s3_data(**context):
        """
        Process the data that was uploaded to S3.

        This is a placeholder for downstream processing.
        """
        # Get the metadata from the upstream task
        ti = context["ti"]
        metadata = ti.xcom_pull(task_ids="extract_filemaker_to_s3")

        if metadata:
            record_count = metadata.get("record_count", 0)
            s3_uri = metadata.get("s3_uri", "")

            print(f"Processing {record_count} records from {s3_uri}")
            # Add your processing logic here

            return f"Processed {record_count} records successfully"
        else:
            print("No metadata available from upstream task")
            return "No data processed"

    # Task to process the uploaded data
    process_data = PythonOperator(
        task_id="process_s3_data",
        python_callable=process_s3_data,
    )

    # Define the task dependencies
    extract_and_upload >> process_data
