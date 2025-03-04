FileMaker Sensors
==============

This document describes the sensors provided by the FileMaker provider for Apache Airflow.

FileMakerDataSensor
----------------

The ``FileMakerDataSensor`` monitors a FileMaker table for records matching a specific condition.

.. code-block:: python

    from airflow.providers.filemaker.sensors.filemaker import FileMakerDataSensor
    
    wait_for_new_students = FileMakerDataSensor(
        task_id='wait_for_new_students',
        filemaker_conn_id='filemaker_default',
        endpoint='Students',
        filter_query="CreatedDate gt 2023-01-01",
        mode='poke',
        poke_interval=300,
        timeout=60 * 60 * 2,  # 2 hours
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``endpoint``: The OData endpoint to monitor
* ``filter_query``: OData filter query expression
* ``select``: Comma-separated list of fields to return (optional)
* ``mode``: Sensor mode (``poke`` or ``reschedule``, default: ``poke``)
* ``poke_interval``: Time in seconds between pokes (default: 60)
* ``timeout``: Time in seconds to wait before timing out (default: 60 * 60 * 24 - 24 hours)
* ``soft_fail``: Whether to mark the task as SKIPPED on failure (default: False)
* ``exponential_backoff``: Whether to wait exponentially longer between pokes (default: False)

FileMakerChangeSensor
------------------

The ``FileMakerChangeSensor`` detects changes in a FileMaker table since a specified timestamp.

.. code-block:: python

    from airflow.providers.filemaker.sensors.filemaker import FileMakerChangeSensor
    
    monitor_changes = FileMakerChangeSensor(
        task_id='monitor_table_changes',
        filemaker_conn_id='filemaker_default',
        endpoint='Students',
        last_modified_field='ModificationTimestamp',
        reference_timestamp="{{ execution_date }}",
        mode='poke',
        poke_interval=300,
        timeout=60 * 60 * 2,  # 2 hours
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``endpoint``: The OData endpoint to monitor
* ``last_modified_field``: The timestamp field to check for changes
* ``reference_timestamp``: The reference timestamp to compare against
* ``mode``: Sensor mode (``poke`` or ``reschedule``, default: ``poke``)
* ``poke_interval``: Time in seconds between pokes (default: 60)
* ``timeout``: Time in seconds to wait before timing out (default: 60 * 60 * 24 - 24 hours)
* ``soft_fail``: Whether to mark the task as SKIPPED on failure (default: False)
* ``exponential_backoff``: Whether to wait exponentially longer between pokes (default: False)

FileMakerCustomSensor
------------------

The ``FileMakerCustomSensor`` allows for custom monitoring logic with a callable function.

.. code-block:: python

    from airflow.providers.filemaker.sensors.filemaker import FileMakerCustomSensor
    
    def check_data_quality(hook, **kwargs):
        """Custom function to check data quality in FileMaker."""
        response = hook.get_records(
            table='Students', 
            filter_query="GradeLevel eq null"
        )
        # Return True if no students have null grade levels (good quality)
        return len(response.get('value', [])) == 0
    
    data_quality_sensor = FileMakerCustomSensor(
        task_id='check_data_quality',
        filemaker_conn_id='filemaker_default',
        callable_fn=check_data_quality,
        mode='poke',
        poke_interval=3600,  # Check hourly
    )

**Parameters**:

* ``filemaker_conn_id``: The Airflow connection ID for FileMaker Cloud (default: ``filemaker_default``)
* ``callable_fn``: A callable function that takes a FileMakerHook and returns a boolean
* ``op_kwargs``: Additional keyword arguments to pass to the callable function (optional)
* ``mode``: Sensor mode (``poke`` or ``reschedule``, default: ``poke``)
* ``poke_interval``: Time in seconds between pokes (default: 60)
* ``timeout``: Time in seconds to wait before timing out (default: 60 * 60 * 24 - 24 hours)
* ``soft_fail``: Whether to mark the task as SKIPPED on failure (default: False)
* ``exponential_backoff``: Whether to wait exponentially longer between pokes (default: False)

Using Sensors in DAGs
------------------

Here's an example DAG that demonstrates using FileMaker sensors:

.. code-block:: python

    from datetime import datetime, timedelta
    from airflow import DAG
    from airflow.operators.dummy import DummyOperator
    from airflow.providers.filemaker.sensors.filemaker import (
        FileMakerDataSensor,
        FileMakerChangeSensor,
        FileMakerCustomSensor
    )
    
    def check_student_data_quality(hook, **kwargs):
        """Check that all required fields are present."""
        students = hook.get_records(
            table='Students', 
            filter_query="Name eq null or Email eq null"
        )
        # Return True if all students have required fields (good quality)
        return len(students.get('value', [])) == 0
    
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
        'filemaker_sensors_example',
        default_args=default_args,
        schedule_interval='@daily',
        catchup=False,
    ) as dag:
        
        start = DummyOperator(task_id='start')
        
        # Wait for new students added today
        wait_for_new_students = FileMakerDataSensor(
            task_id='wait_for_new_students',
            filemaker_conn_id='filemaker_default',
            endpoint='Students',
            filter_query="CreatedDate gt {{ ds }}",
            mode='poke',
            poke_interval=300,
            timeout=60 * 60 * 6,  # 6 hours
        )
        
        # Monitor for changes since the execution date
        monitor_changes = FileMakerChangeSensor(
            task_id='monitor_student_changes',
            filemaker_conn_id='filemaker_default',
            endpoint='Students',
            last_modified_field='ModificationTimestamp',
            reference_timestamp="{{ execution_date }}",
            mode='poke',
            poke_interval=300,
        )
        
        # Check data quality
        check_quality = FileMakerCustomSensor(
            task_id='check_student_data_quality',
            filemaker_conn_id='filemaker_default',
            callable_fn=check_student_data_quality,
            mode='poke',
            poke_interval=1800,  # Every 30 minutes
            timeout=60 * 60 * 4,  # 4 hours
        )
        
        end = DummyOperator(task_id='end')
        
        # Set task dependencies
        start >> wait_for_new_students >> monitor_changes >> check_quality >> end 