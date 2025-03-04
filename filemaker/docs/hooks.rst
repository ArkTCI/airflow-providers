Hooks
=====

The FileMaker Provider includes hooks for interacting with FileMaker Cloud using the OData API.

.. contents::
  :depth: 1
  :local:

FileMakerHook
-------------

Use the :class:`~airflow.providers.filemaker.hooks.filemaker.FileMakerHook` to interact with FileMaker Cloud.

.. code-block:: python

    from airflow.providers.filemaker.hooks.filemaker import FileMakerHook

    # Initialize the hook
    hook = FileMakerHook(filemaker_conn_id='filemaker_default')

    # Get records using the hook
    records = hook.get_records(
        table='Students',
        filter_query="GradeLevel eq '12'"
    )

Core Request Data Methods
------------------------

The FileMaker hook provides several methods for requesting data according to the FileMaker OData API specification:

Get Multiple Records
~~~~~~~~~~~~~~~~~~~

Use ``get_records`` to fetch multiple records from a table:

.. code-block:: python

    # Get all records from a table
    records = hook.get_records(table='Students')
    
    # Get filtered records
    records = hook.get_records(
        table='Students',
        filter_query="GradeLevel eq '12'"
    )

Get Record by ID
~~~~~~~~~~~~~~~

Use ``get_record_by_id`` to fetch a specific record by its ID:

.. code-block:: python

    # Get a specific record
    record = hook.get_record_by_id(
        table='Students',
        record_id='123'
    )
    
    # With expanded related data
    record = hook.get_record_by_id(
        table='Students',
        record_id='123',
        expand='Grades,Enrollments'
    )

Get Field Value
~~~~~~~~~~~~~~

Use ``get_field_value`` to get a specific field value from a record:

.. code-block:: python

    # Get a specific field value
    name = hook.get_field_value(
        table='Students',
        record_id='123',
        field_name='FirstName'
    )

Get Binary Field Value
~~~~~~~~~~~~~~~~~~~~~

Use ``get_binary_field_value`` to retrieve binary data (images, attachments, etc.):

.. code-block:: python

    # Get a binary field value (e.g., image or document)
    image_data = hook.get_binary_field_value(
        table='Students',
        record_id='123',
        field_name='Photo',
        accept_format='image/jpeg'
    )
    
    # Save to file
    with open('student_photo.jpg', 'wb') as f:
        f.write(image_data)

Cross Join Tables
~~~~~~~~~~~~~~~~

Use ``get_cross_join`` to create a cross join between unrelated tables:

.. code-block:: python

    # Cross join two tables
    results = hook.get_cross_join(
        tables=['Students', 'Courses'],
        select='Students/Id,Students/Name,Courses/Code,Courses/Title',
        filter_query="Students/GradeLevel eq '12'"
    )

Supported OData Query Options
-----------------------------

The FileMaker hook supports all standard OData query options through the ``get_records`` method:

.. code-block:: python

    records = hook.get_records(
        table='Students',
        select='FirstName,LastName,Email',        # $select - specific fields
        filter_query="GradeLevel eq '12'",        # $filter - filtering conditions
        top=20,                                   # $top - limit results
        skip=10,                                  # $skip - pagination
        orderby='LastName asc',                   # $orderby - sorting
        expand='Grades,Enrollments',              # $expand - related entities
        count=True,                               # $count - include total count
        apply='groupby((Subject),aggregate(Score with average as AverageScore))'  # $apply - aggregations
    )

Query Option Details
-------------------

$select
~~~~~~~

Specifies which fields to include in the response.

.. code-block:: python

    # Only return specific fields
    records = hook.get_records(
        table='Students',
        select='FirstName,LastName,Email'
    )

$filter
~~~~~~~

Filters records based on a condition.

.. code-block:: python

    # Filter records
    records = hook.get_records(
        table='Students',
        filter_query="GradeLevel eq '12' and Active eq true"
    )

$top and $skip
~~~~~~~~~~~~~

Used for pagination of results.

.. code-block:: python

    # Get results 11-20
    records = hook.get_records(
        table='Students',
        top=10,
        skip=10
    )

$orderby
~~~~~~~~

Sorts the results by one or more fields.

.. code-block:: python

    # Sort by last name, then first name
    records = hook.get_records(
        table='Students',
        orderby='LastName asc,FirstName asc'
    )

$expand
~~~~~~~

Expands related entities in the response.

.. code-block:: python

    # Include related tables
    records = hook.get_records(
        table='Students',
        expand='Grades,Enrollments'
    )

$count
~~~~~~

Includes the total count of entities that match the filter.

.. code-block:: python

    # Get records with count
    records = hook.get_records(
        table='Students',
        filter_query="GradeLevel eq '12'",
        count=True
    )
    
    # Access the count
    total_count = records.get('@odata.count', 0)

$apply
~~~~~~

Applies aggregation transformations to entities.

.. code-block:: python

    # Get average score by subject
    records = hook.get_records(
        table='Grades',
        apply='groupby((Subject),aggregate(Score with average as AverageScore))'
    )

Reference
---------

For more information on:

* FileMaker OData API: `Claris FileMaker OData API Guide <https://help.claris.com/en/odata-guide/>`_
* OData Query Options: `OData Query Options <https://help.claris.com/en/odata-guide/content/query-options.html>`_
* Request Data Methods: `OData Request Data <https://help.claris.com/en/odata-guide/content/request-data.html>`_ 