"""
Example DAG demonstrating the usage of the FileMaker provider in Apache Airflow.
This DAG shows how to extract data from a FileMaker database, process it, and store the results.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.decorators import task
from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator
from airflow.operators.python import PythonOperator

# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
with DAG(
    'filemaker_extract_example',
    default_args=default_args,
    description='Example DAG using FileMaker provider',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['example', 'filemaker'],
) as dag:
    
    # Define a FileMaker extraction task
    extract_data = FileMakerExtractOperator(
        task_id='extract_filemaker_data',
        conn_id='filemaker_default',
        layout='Customers',
        query={'Status': 'Active'},
        output_format='json',
    )
    
    # Define a processing task using the Python decorator
    @task(task_id="process_data")
    def process_data(**kwargs):
        """
        Process the FileMaker data extracted in the previous step.
        """
        import json
        from airflow.models import Variable
        
        # Get the data from the previous task
        ti = kwargs['ti']
        data = ti.xcom_pull(task_ids='extract_filemaker_data')
        
        # If we received data as a string, parse it
        if isinstance(data, str):
            data = json.loads(data)
        
        # Process the data
        processed_records = []
        if data and 'response' in data and 'data' in data['response']:
            records = data['response']['data']
            
            for record in records:
                # Extract relevant fields
                processed_record = {
                    'customer_id': record.get('fieldData', {}).get('CustomerID', ''),
                    'name': record.get('fieldData', {}).get('Name', ''),
                    'email': record.get('fieldData', {}).get('Email', ''),
                    'status': record.get('fieldData', {}).get('Status', ''),
                    'processed_date': datetime.now().strftime('%Y-%m-%d')
                }
                processed_records.append(processed_record)
        
        # Return the processed records
        return processed_records
    
    # Define a task to save the processed data
    @task(task_id="save_results")
    def save_results(**kwargs):
        """
        Save the processed data to a file.
        """
        import json
        import os
        
        # Get the processed data from the previous task
        ti = kwargs['ti']
        processed_data = ti.xcom_pull(task_ids='process_data')
        
        # Create the output directory if it doesn't exist
        output_dir = '/opt/airflow/data'
        os.makedirs(output_dir, exist_ok=True)
        
        # Save the data to a JSON file
        output_file = f"{output_dir}/processed_customers_{datetime.now().strftime('%Y%m%d')}.json"
        with open(output_file, 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        return f"Data saved to {output_file}"
    
    # Define the task dependencies
    process_task = process_data()
    save_task = save_results()
    
    extract_data >> process_task >> save_task 