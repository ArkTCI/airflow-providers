# FileMaker Cloud Provider for Apache Airflow

This is a custom provider package for Apache Airflow that enables integration with FileMaker Cloud's OData API.

## Features

- **FileMakerHook**: Handles authentication with FileMaker Cloud through AWS Cognito and provides methods to interact with the OData API.
- **FileMakerQueryOperator**: Executes OData queries against FileMaker Cloud.
- **FileMakerExtractOperator**: Extracts data from FileMaker Cloud and saves it in various formats.
- **FileMakerSchemaOperator**: Retrieves and parses the FileMaker Cloud OData metadata schema.
- **FileMakerDataSensor**: Sensor that monitors FileMaker tables for specific conditions.
- **FileMakerChangeSensor**: Sensor that detects changes in FileMaker tables since a timestamp.
- **FileMakerCustomSensor**: Customizable sensor that allows for complex monitoring logic.

## Installation

### Installation from PyPI (Recommended)

```bash
pip install arktci-airflow-provider-filemaker
```

### Manual Installation

1. Copy the `providers/filemaker` directory to your Airflow project's `providers` directory.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package:
   ```
   pip install -e .
   ```

4. Create a FileMaker connection in Airflow:
   - Connection ID: `filemaker_default` (or any ID you prefer)
   - Connection Type: `filemaker`
   - Host: Your FileMaker Cloud host (e.g., `my-fmcloud.filemaker-cloud.com`)
   - Schema: Your FileMaker database name
   - Login: Your FileMaker Cloud username (Claris ID)
   - Password: Your FileMaker Cloud password
   - Extra: JSON containing Cognito details (if not using auto-discovery):
     ```json
     {
       "user_pool_id": "your-cognito-user-pool-id",
       "client_id": "your-cognito-client-id",
       "region": "your-aws-region"
     }
     ```

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/airflow-provider-filemaker.git
   cd airflow-provider-filemaker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Run the development setup script:
   ```bash
   ./setup_dev_env.sh
   ```
   
   This script will:
   - Install all dependencies from `requirements.txt` and `requirements-dev.txt`
   - Install the package in development mode
   - Set up pre-commit hooks
   - Verify the installation

### Running Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest test_filemaker.py

# Run tests with coverage
pytest --cov=filemaker tests/
```

### Building the Package

```bash
python -m build
```

This will create both source distribution (`.tar.gz`) and wheel (`.whl`) files in the `dist/` directory.

## Usage

### Basic Query Example

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.filemaker.operators.filemaker import FileMakerQueryOperator

dag = DAG(
    'filemaker_query_example',
    start_date=days_ago(1),
    schedule_interval=None
)

query_task = FileMakerQueryOperator(
    task_id='query_filemaker',
    filemaker_conn_id='filemaker_default',
    endpoint='MyTableName',
    dag=dag
)
```

### Data Extraction Example

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.filemaker.operators.filemaker import FileMakerExtractOperator

dag = DAG(
    'filemaker_extract_example',
    start_date=days_ago(1),
    schedule_interval=None
)

extract_task = FileMakerExtractOperator(
    task_id='extract_filemaker_data',
    filemaker_conn_id='filemaker_default',
    endpoint='MyTableName',
    output_path='/tmp/extracted_data.json',
    format='json',
    dag=dag
)
```

### Schema Retrieval Example

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.filemaker.operators.filemaker import FileMakerSchemaOperator

dag = DAG(
    'filemaker_schema_example',
    start_date=days_ago(1),
    schedule_interval=None
)

schema_task = FileMakerSchemaOperator(
    task_id='get_filemaker_schema',
    filemaker_conn_id='filemaker_default',
    output_path='/tmp/filemaker_schema.json',
    dag=dag
)
```

### Data Sensor Example

```python
from airflow import DAG
from airflow.utils.dates import days_ago
from airflow.providers.filemaker.sensors.filemaker import FileMakerDataSensor

dag = DAG(
    'filemaker_sensor_example',
    start_date=days_ago(1),
    schedule_interval=None
)

sensor_task = FileMakerDataSensor(
    task_id='wait_for_filemaker_data',
    filemaker_conn_id='filemaker_default',
    table='MyTableName',
    condition="CreatedDate gt 2023-01-01T00:00:00Z",
    expected_count=5,
    comparison_operator='>',
    mode='poke',
    poke_interval=300,  # 5 minutes
    dag=dag
)
```

## Authentication

The FileMaker provider supports multiple authentication methods for FileMaker Cloud:

1. **Auto-discovery**: If no Cognito details are provided, the provider will attempt to discover them from the Claris endpoint.
2. **Explicit configuration**: You can provide `user_pool_id`, `client_id`, and `region` in the connection extras.
3. **Fallback methods**: The provider includes multiple authentication methods and will try different approaches if the primary method fails.

## OData Support

The provider supports FileMaker Cloud's OData v4 API, including:

- Basic CRUD operations
- Query filtering with `$filter`
- Sorting with `$orderby`
- Pagination with `$top` and `$skip`
- Selecting specific fields with `$select`
- Expanding relationships with `$expand`
- Count operations with `$count`

## Troubleshooting

- **Authentication Issues**: Ensure your credentials are correct and that you have the correct permissions in FileMaker Cloud.
- **Connection Errors**: Check your network connectivity and that the FileMaker Cloud host is accessible.
- **API Errors**: Check the Airflow logs for detailed error messages from the FileMaker Cloud API.
- **Import Errors**: Make sure the provider package is correctly installed and discoverable by Airflow.

## License

This provider is licensed under the same license as Apache Airflow. 