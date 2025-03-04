"""
Example DAG demonstrating the FileMaker OData request data methods.

This DAG shows how to use the FileMaker hook to request data in various ways
according to the FileMaker OData API specification.
"""

from datetime import datetime, timedelta

from airflow.operators.python import PythonOperator

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

# Create the DAG
with DAG(
    "example_filemaker_request_data",
    default_args=default_args,
    description="Example DAG demonstrating FileMaker OData request data methods",
    schedule_interval=None,  # Set to None for manual triggering
    catchup=False,
) as dag:

    def demonstrate_request_data(**context):
        """Demonstrate various ways to request data from FileMaker."""
        hook = FileMakerHook(filemaker_conn_id="filemaker_default")
        results = {}

        # Example 1: Get multiple records with filtering
        print("\n--- Example 1: Get multiple records ---")
        try:
            records = hook.get_records(
                table="Students", filter_query="GradeLevel eq '12'", top=5, orderby="LastName asc", count=True
            )
            results["records_count"] = records.get("@odata.count", 0)
            print(f"Found {results['records_count']} records")

            # Print the first 5 records
            for i, record in enumerate(records.get("value", [])[:5]):
                print(f"Record {i + 1}: {record.get('FirstName')} {record.get('LastName')}")
        except Exception as e:
            print(f"Error fetching records: {str(e)}")

        # Example 2: Get a specific record by ID
        print("\n--- Example 2: Get record by ID ---")
        try:
            # Use the first record ID from the previous query if available
            record_id = records.get("value", [{}])[0].get("id", "1")
            record = hook.get_record_by_id(
                table="Students", record_id=record_id, expand="Grades"  # Expand related grades
            )
            print(f"Record details: {record}")

            # Show expanded grades if available
            if "Grades" in record:
                for grade in record["Grades"].get("value", []):
                    print(f"  Grade: {grade.get('Subject')} - {grade.get('Score')}")
        except Exception as e:
            print(f"Error fetching record by ID: {str(e)}")

        # Example 3: Get a specific field value
        print("\n--- Example 3: Get field value ---")
        try:
            name = hook.get_field_value(table="Students", record_id=record_id, field_name="FirstName")
            print(f"First name: {name}")
        except Exception as e:
            print(f"Error fetching field value: {str(e)}")

        # Example 4: Get binary field (if available)
        print("\n--- Example 4: Get binary field ---")
        try:
            binary_data = hook.get_binary_field_value(table="Students", record_id=record_id, field_name="Photo")
            print(f"Binary data size: {len(binary_data)} bytes")
        except Exception as e:
            print(f"Note: Binary field retrieval skipped or failed: {str(e)}")

        # Example 5: Cross join two tables
        print("\n--- Example 5: Cross join tables ---")
        try:
            joined_data = hook.get_cross_join(
                tables=["Students", "Courses"],
                select="Students/Id,Students/LastName,Courses/Code",
                filter_query="Students/GradeLevel eq '12'",
                top=5,
            )
            print(f"Cross join results: {len(joined_data.get('value', []))} records")

            # Print sample of joined data
            for i, item in enumerate(joined_data.get("value", [])[:3]):
                print(f"Join {i + 1}: Student={item.get('Students/LastName')}, Course={item.get('Courses/Code')}")
        except Exception as e:
            print(f"Error performing cross join: {str(e)}")

        return results

    # Create the task
    request_data_task = PythonOperator(
        task_id="request_filemaker_data",
        python_callable=demonstrate_request_data,
        provide_context=True,
    )

    # Define the task dependencies (none in this case as we have a single task)
