FileMaker Operators
=================

This document describes the operators provided by the FileMaker provider for Apache Airflow.

FileMakerQueryOperator
--------------------

The ``FileMakerQueryOperator`` allows you to execute OData queries against FileMaker Cloud.

.. code-block:: python

    from airflow.providers.filemaker.operators.filemaker import FileMakerQueryOperator
    
    query_students = FileMakerQueryOperator(
        task_id='query_students',
        filemaker_conn_id='filemaker_default',
        endpoint='Students',
        filter_query="GradeLevel eq '12'",
        top=100,
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``endpoint``: The OData endpoint to query, will be appended to the base URL
* ``filter_query``: OData filter query expression (optional)
* ``select``: Comma-separated list of fields to return (optional)
* ``expand``: Related entities to expand (optional)
* ``orderby``: Fields to order results by (optional)
* ``top``: Maximum number of records to return (optional)
* ``skip``: Number of records to skip (optional)
* ``count``: Whether to include total count in response (optional)
* ``format_options``: Additional format options (optional)

FileMakerExtractOperator
----------------------

The ``FileMakerExtractOperator`` extracts data from FileMaker Cloud and saves it in various formats.

.. code-block:: python

    from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator
    
    extract_data = FileMakerExtractOperator(
        task_id='extract_students_data',
        filemaker_conn_id='filemaker_default',
        endpoint='Students',
        output_path='/tmp/students_data.csv',
        output_format='csv',
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``endpoint``: The OData endpoint to extract data from
* ``filter_query``: OData filter query expression (optional)
* ``select``: Comma-separated list of fields to extract (optional)
* ``expand``: Related entities to expand (optional)
* ``orderby``: Fields to order results by (optional)
* ``output_path``: Path where the extracted data will be saved
* ``output_format``: Format to save the data (``csv``, ``json``, ``parquet``, ``excel``)
* ``top``: Maximum number of records to extract (optional)
* ``skip``: Number of records to skip (optional)
* ``batch_size``: Number of records to fetch in each batch (default: 1000)

FileMakerSchemaOperator
---------------------

The ``FileMakerSchemaOperator`` retrieves and parses the FileMaker Cloud OData metadata schema.

.. code-block:: python

    from airflow.providers.filemaker.operators.filemaker import FileMakerSchemaOperator
    
    get_schema = FileMakerSchemaOperator(
        task_id='get_metadata_schema',
        filemaker_conn_id='filemaker_default',
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``output_path``: Path to save the schema (optional)
* ``output_format``: Format to save the schema (``json``, ``xml``) (optional, default: ``json``)

FileMakeToS3Operator
-----------------

The ``FileMakerToS3Operator`` extracts data from FileMaker Cloud and uploads it to Amazon S3.

.. code-block:: python

    from airflow.providers.filemaker.operators.filemaker import FileMakerToS3Operator
    
    extract_to_s3 = FileMakerToS3Operator(
        task_id='extract_to_s3',
        filemaker_conn_id='filemaker_default',
        aws_conn_id='aws_default',
        endpoint='Students',
        s3_bucket='my-data-lake',
        s3_key='filemaker-data/students/{{ ds }}/data.json',
        file_format='json',
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``aws_conn_id``: The Airflow connection ID for AWS (default: ``aws_default``)
* ``endpoint``: The OData endpoint to extract data from
* ``filter_query``: OData filter query expression (optional)
* ``select``: Comma-separated list of fields to extract (optional)
* ``expand``: Related entities to expand (optional)
* ``s3_bucket``: The S3 bucket to upload data to
* ``s3_key``: The S3 key to upload data to
* ``file_format``: Format to save the data (``csv``, ``json``, ``parquet``)
* ``replace``: Whether to replace existing S3 file (default: ``True``)
* ``top``: Maximum number of records to extract (optional)
* ``batch_size``: Number of records to fetch in each batch (default: 1000)

Using Operators in DAGs
---------------------

Here's an example DAG that combines these operators:

.. code-block:: python

    from datetime import datetime, timedelta
    from airflow import DAG
    from airflow.providers.filemaker.operators.filemaker import (
        FileMakerQueryOperator,
        FileMakerExtractOperator,
        FileMakerSchemaOperator,
        FileMakerToS3Operator,
    )
    
    default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2023, 1, 1),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }
    
    with DAG(
        'filemaker_etl_example',
        default_args=default_args,
        schedule_interval='@daily',
        catchup=False,
    ) as dag:
        
        # Get schema metadata
        get_schema = FileMakerSchemaOperator(
            task_id='get_schema',
            filemaker_conn_id='filemaker_default',
        )
        
        # Query active students
        query_students = FileMakerQueryOperator(
            task_id='query_students',
            filemaker_conn_id='filemaker_default',
            endpoint='Students',
            filter_query="Active eq true",
            top=100,
        )
        
        # Extract student data to CSV
        extract_to_csv = FileMakerExtractOperator(
            task_id='extract_to_csv',
            filemaker_conn_id='filemaker_default',
            endpoint='Students',
            filter_query="Active eq true",
            output_path='/tmp/students_{{ ds }}.csv',
            output_format='csv',
        )
        
        # Upload to S3
        upload_to_s3 = FileMakerToS3Operator(
            task_id='upload_to_s3',
            filemaker_conn_id='filemaker_default',
            aws_conn_id='aws_default',
            endpoint='Students',
            filter_query="Active eq true",
            s3_bucket='my-data-lake',
            s3_key='filemaker/students/{{ ds }}/data.json',
            file_format='json',
        )
        
        # Set task dependencies
        get_schema >> query_students >> extract_to_csv >> upload_to_s3 