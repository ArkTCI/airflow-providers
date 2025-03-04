FileMaker Cloud Provider for Apache Airflow
==========================================

.. image:: https://img.shields.io/pypi/v/arktci-airflow-provider-filemaker.svg
    :target: https://pypi.org/project/arktci-airflow-provider-filemaker/
    :alt: PyPI Version

.. image:: https://img.shields.io/badge/License-Apache%202.0-blue.svg
    :target: https://opensource.org/licenses/Apache-2.0
    :alt: License

.. image:: https://arkapps-assessts.s3.us-east-1.amazonaws.com/ark-logo.png
    :target: https://www.arktci.com
    :alt: ArkTCI Logo
    :width: 200px

A comprehensive Apache Airflow provider for FileMaker Cloud that enables seamless integration with FileMaker's OData API.

Developed and maintained by `ArkTCI <https://www.arktci.com>`_.

Features
--------

- **Authentication**: Secure connection to FileMaker Cloud using AWS Cognito
- **OData Support**: Full implementation of FileMaker's OData API specification
- **Data Operations**: Query, create, update, and delete records
- **Monitoring**: Sensors to detect changes or conditions in FileMaker databases
- **Data Transfer**: Extract data from FileMaker and save it to various formats or destinations

Documentation
-------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   connections
   hooks
   operators
   sensors

Getting Started
--------------

Installation
~~~~~~~~~~~

.. code-block:: bash

    pip install arktci-airflow-provider-filemaker

Basic Usage
~~~~~~~~~~

1. **Create a FileMaker Connection**

   In the Airflow UI, create a new connection with:
   
   - Connection ID: ``filemaker_default`` (or any ID you choose)
   - Connection Type: ``filemaker``
   - Host: Your FileMaker Cloud host (e.g., ``my-fmcloud.filemaker-cloud.com``)
   - Schema: Your FileMaker database name
   - Login: Your FileMaker Cloud username
   - Password: Your FileMaker Cloud password

2. **Query Data from FileMaker**

   .. code-block:: python

       from airflow.providers.filemaker.operators.filemaker import FileMakerQueryOperator

       query_task = FileMakerQueryOperator(
           task_id="query_filemaker",
           filemaker_conn_id="filemaker_default",
           database="students",
           layout="students",
           query={"Grade": "A"},
       )

3. **Monitor Changes in FileMaker**

   .. code-block:: python

       from airflow.providers.filemaker.sensors.filemaker import FileMakerChangeSensor

       change_sensor = FileMakerChangeSensor(
           task_id="detect_changes",
           filemaker_conn_id="filemaker_default",
           database="students",
           layout="students",
           last_timestamp="{{ prev_execution_date_success }}",
           mode="poke",
       )

Example DAGs
-----------

The provider includes several example DAGs that demonstrate common usage patterns:

- **Basic Query**: Query data from FileMaker Cloud
- **Data Extraction**: Extract data to various formats
- **Record Management**: Create, update, and delete records
- **Data Transfer**: Move data from FileMaker to other systems

Advanced Topics
--------------

- **Authentication Mechanisms**: Learn about the authentication workflow
- **OData Query Options**: Explore advanced filtering and query capabilities
- **Error Handling**: Best practices for handling connection and query errors
- **Performance Optimization**: Tips for working with large datasets

Troubleshooting
--------------

Common Issues
~~~~~~~~~~~

- **Connection Failed**: Verify credentials and network connectivity
- **Authentication Errors**: Check token generation and authentication headers
- **Query Timeouts**: Optimize queries for large datasets
- **Missing Data**: Ensure correct database, layout, and field names

Getting Help
~~~~~~~~~~~

If you encounter issues not covered in this documentation:

1. Search existing issues on GitHub
2. Check the FileMaker OData documentation
3. File a new issue on the GitHub repository
4. Contact support at `josh@arktci.com <mailto:josh@arktci.com>`_

Contributing
-----------

We welcome contributions to the FileMaker provider! See the GitHub repository for:

- Issue reporting
- Feature requests
- Pull request guidelines
- Development setup

Company Information
-----------------

.. image:: https://arkapps-assessts.s3.us-east-1.amazonaws.com/ark-logo.png
    :target: https://www.arktci.com
    :alt: ArkTCI Logo
    :width: 150px

This provider is developed and maintained by `ArkTCI <https://www.arktci.com>`_, specialists in data integration and automation solutions.

- Website: `https://www.arktci.com <https://www.arktci.com>`_
- Contact: `info@arktci.com <mailto:info@arktci.com>`_
- Contact: `josh@arktci.com <mailto:josh@arktci.com>`_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 