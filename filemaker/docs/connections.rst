FileMaker Connection Setup
=======================

This document provides instructions for setting up a FileMaker Cloud connection in Apache Airflow.

Prerequisites
------------

- Apache Airflow with the FileMaker provider installed
- FileMaker Cloud account credentials
- Access to the Airflow UI

Connection Configuration
----------------------

Follow these steps to set up a FileMaker Cloud connection in Airflow:

1. Navigate to the Airflow UI and go to **Admin** > **Connections**.
2. Click the **+** button to add a new connection.
3. Fill in the following fields:
   
   - **Connection Id**: A unique identifier for your connection (e.g., ``filemaker_default``)
   - **Connection Type**: Select ``FileMaker Cloud`` from the dropdown
   - **FileMaker Host**: Your FileMaker Cloud host URL (e.g., ``cloud.filemaker.com`` or with subdomain if applicable)
   - **FileMaker Database**: The name of your FileMaker database
   - **Username**: Your FileMaker Cloud username
   - **Password**: Your FileMaker Cloud password

4. Click the **Test** button to verify your connection works properly.
5. If the test is successful, click **Save** to store your connection.

Connection Testing
----------------

When you click the **Test** button, the provider will:

1. Attempt to authenticate with your provided credentials
2. Verify that it can retrieve an authentication token
3. Return a success or failure message

Common error messages include:

- **Missing FileMaker host/database/username/password**: Ensure all required fields are filled in
- **Failed to retrieve authentication token**: Check if your credentials are correct
- **Connection failed**: There might be network issues or the FileMaker server may be unreachable

Using the Connection in DAGs
--------------------------

Once your connection is set up, you can use it in your DAGs with the FileMakerHook:

.. code-block:: python

    from airflow.providers.filemaker.hooks.filemaker import FileMakerHook
    
    def my_task_function(**context):
        # Create a hook using the connection
        hook = FileMakerHook(filemaker_conn_id="filemaker_default")
        
        # Use the hook to interact with FileMaker
        result = hook.get_records(table="MyTable")
        print(f"Retrieved {len(result.get('value', []))} records")

Troubleshooting
-------------

If you encounter issues with your FileMaker connection:

1. Verify that your FileMaker Cloud credentials are correct
2. Ensure the FileMaker database name is correctly specified
3. Check if your FileMaker Cloud server is accessible from your Airflow environment
4. Verify that you have the necessary permissions to access the specified database
5. Check the Airflow logs for more detailed error information 