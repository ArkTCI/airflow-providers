"""
Operators for FileMaker Cloud integration.

This module contains operators for executing tasks against FileMaker Cloud's OData API.
"""

from typing import Any, Dict, List, Optional

from airflow.models import BaseOperator
from airflow.providers.amazon.aws.hooks.s3 import S3Hook
from airflow.utils.decorators import apply_defaults

from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


class FileMakerQueryOperator(BaseOperator):
    """
    Executes an OData query against FileMaker Cloud.

    :param endpoint: The OData endpoint to query, will be appended to the base URL
    :type endpoint: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    :param accept_format: The accept header format, defaults to 'application/json'
    :type accept_format: str
    """

    template_fields = ("endpoint",)
    template_ext = ()
    ui_color = "#edd1f0"  # Light purple

    @apply_defaults
    def __init__(
        self,
        *,
        endpoint: str,
        accept_format: str = "application/json",
        filemaker_conn_id: str = "filemaker_default",
        hook: Optional[FileMakerHook] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.filemaker_conn_id = filemaker_conn_id
        self.accept_format = accept_format
        self.hook = hook

    def execute(self, context) -> Dict[str, Any]:
        """
        Execute the OData query.

        :param context: The task context
        :return: The query result data
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Executing OData query on endpoint: {self.endpoint}")
        if self.hook is None and self.filemaker_conn_id is not None:
            self.hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Extract just the table name from the endpoint, removing any leading/trailing slashes
        table_name = self.endpoint.strip("/")

        # If it contains a path, take only the last part which should be the table name
        if "/" in table_name:
            table_name = table_name.split("/")[-1]

        self.log.info(f"Using table name: {table_name}")

        # Execute query with the proper table name parameter
        result = self.hook.get_records(
            table=table_name,
            page_size=100,  # Use a reasonable page size
            max_pages=30,  # Limit to one page to prevent endless loops
            accept_format=self.accept_format,
        )

        return result


class FileMakerExtractOperator(BaseOperator):
    """
    Extracts data from FileMaker Cloud and optionally saves it to a destination.

    This operator extends the basic query functionality to handle common extraction
    patterns and save the results to a destination format/location.

    :param table: The OData table to query
    :type table: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    :param output_path: Optional path to save the output
    :type output_path: Optional[str]
    :param format: Output format ('json', 'csv', etc.)
    :type format: str
    :param accept_format: The accept header format for the OData API
    :type accept_format: str
    :param hook: Optional FileMakerHook instance
    :type hook: Optional[FileMakerHook]
    """

    template_fields = ("table", "output_path")
    template_ext = ()
    ui_color = "#e8c1f0"  # Lighter purple than query operator

    @apply_defaults
    def __init__(
        self,
        *,
        table: str,
        filemaker_conn_id: str = "filemaker_default",
        output_path: Optional[str] = None,
        format: str = "json",
        accept_format: str = "application/json",
        hook: Optional[FileMakerHook] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.filemaker_conn_id = filemaker_conn_id
        self.output_path = output_path
        self.format = format
        self.accept_format = accept_format
        self.hook = hook

    def execute(self, context) -> Dict[str, Any]:
        """
        Execute the OData extraction.

        :param context: The task context
        :return: The extraction result data
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Extracting data from FileMaker Cloud endpoint: {self.table}")

        if self.hook is None and self.filemaker_conn_id is not None:
            self.hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Execute query with safe parameters
        # Execute query with safe parameters
        result = self.hook.get_records(
            table=self.table,
            page_size=100,  # Use a reasonable page size
            max_pages=200,  # Limit to one page initially
            accept_format=self.accept_format,
        )

        # Save output if path is specified
        if self.output_path:
            self._save_output(result)

        return result

    def _save_output(self, data: Dict[str, Any]) -> None:
        """
        Save the data to the specified output path in the specified format.

        :param data: The data to save
        :type data: Dict[str, Any]
        """
        import csv
        import json
        import os

        # Skip if output_path is None or empty
        if not self.output_path:
            self.log.warning("No output path specified, skipping file write operation")
            return

        # Check if the directory path is not empty (to avoid errors with os.makedirs(''))
        dir_path = os.path.dirname(self.output_path)
        if dir_path:  # Only create directory if there's an actual path
            os.makedirs(dir_path, exist_ok=True)

        self.log.info(f"Saving data to {self.output_path} in {self.format} format")

        with open(self.output_path, "w") as f:
            if self.format.lower() == "json":
                json.dump(data, f, indent=2)
            elif self.format.lower() == "csv":
                # Handle CSV output - assumes data is a list of dictionaries
                if "value" in data and isinstance(data["value"], list):
                    items = data["value"]
                    if items:
                        with open(self.output_path, "w", newline="") as f:
                            writer = csv.DictWriter(f, fieldnames=items[0].keys())
                            writer.writeheader()
                            writer.writerows(items)
                    else:
                        self.log.warning("No items found in 'value' key to write to CSV")
                else:
                    self.log.error("Data format not suitable for CSV output")
            else:
                self.log.error(f"Unsupported output format: {self.format}")


class FileMakerSchemaOperator(BaseOperator):
    """
    Retrieves and parses FileMaker Cloud's OData metadata schema.

    This operator fetches the OData API's metadata schema in XML format
    and parses it to extract entities, properties, and relationships.

    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ()
    template_ext = ()
    ui_color = "#d1c1f0"  # Different shade of purple

    @apply_defaults
    def __init__(
        self,
        *,
        filemaker_conn_id: str = "filemaker_default",
        output_path: Optional[str] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.filemaker_conn_id = filemaker_conn_id
        self.output_path = output_path

    def execute(self, context) -> Dict[str, Any]:
        """
        Execute the schema retrieval.

        :param context: The task context
        :return: The parsed schema data
        :rtype: Dict[str, Any]
        """
        self.log.info("Retrieving FileMaker Cloud OData schema")

        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        base_url = hook.get_base_url()

        # The OData metadata endpoint
        metadata_url = f"{base_url}/$metadata"
        self.log.info(f"Metadata URL: {metadata_url}")

        # Get the metadata XML
        xml_content = hook.get_odata_response(endpoint=metadata_url, accept_format="application/xml")

        # Parse the XML schema
        schema = self._parse_xml_schema(xml_content)

        # Save the schema if output path is provided
        if self.output_path:
            import json
            import os

            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
            with open(self.output_path, "w") as f:
                json.dump(schema, f, indent=2)
        else:
            self.log.warning("No output path specified, skipping file write operation")

        return schema

    def _parse_xml_schema(self, xml_content: str) -> Dict[str, Any]:
        """
        Parse XML schema content.

        Args:
            xml_content: The XML content to parse

        Returns:
            Dict[str, Any]: Parsed schema
        """
        import xml.etree.ElementTree as ET

        # XML namespaces used in OData metadata
        namespaces = {
            "edmx": "http://docs.oasis-open.org/odata/ns/edmx",
            "edm": "http://docs.oasis-open.org/odata/ns/edm",
        }

        try:
            root = ET.fromstring(xml_content)

            # Find all entity types
            schema_data: Dict[str, Any] = {"entities": {}, "entity_sets": {}, "relationships": []}

            # Parse entity types
            for entity_type in root.findall(".//edm:EntityType", namespaces):
                entity_name = entity_type.get("Name")
                if entity_name is None:
                    entity_name = ""  # Default to empty string if None
                properties = []

                # Fix Element handling for property elements
                for property_elem in entity_type.findall("./edm:Property", namespaces):
                    prop_name = property_elem.get("Name", "")  # Default to empty string if None
                    prop_type = property_elem.get("Type", "")  # Default to empty string if None

                    # Now prop_name and prop_type are guaranteed to be strings
                    if prop_name.startswith("@"):
                        # Handle special properties
                        pass

                    # Add property to the list
                    properties.append({"name": prop_name, "type": prop_type})

                # Find keys
                key_props = []
                key_element = entity_type.find("./edm:Key", namespaces)
                if key_element is not None:
                    for key_ref in key_element.findall("./edm:PropertyRef", namespaces):
                        key_props.append(key_ref.get("Name"))

                schema_data["entities"][entity_name] = {
                    "properties": properties,
                    "key_properties": key_props,
                }

            # Parse entity sets (tables)
            for entity_set in root.findall(".//edm:EntitySet", namespaces):
                set_name = entity_set.get("Name")
                entity_type = entity_set.get("EntityType")
                if entity_type:
                    # Extract the type name without namespace
                    type_name = entity_type.split(".")[-1]
                    schema_data["entity_sets"][set_name] = {"entity_type": type_name}

            # Parse navigation properties (relationships)
            for entity_type in root.findall(".//edm:EntityType", namespaces):
                source_entity = entity_type.get("Name")
                if source_entity is None:
                    source_entity = ""  # Default to empty string if None

                for nav_prop in entity_type.findall("./edm:NavigationProperty", namespaces):
                    target_type = nav_prop.get("Type")
                    # Handle both EntityType and Collection(EntityType)
                    if target_type is not None and target_type.startswith("Collection("):
                        # Extract entity type from Collection(Namespace.EntityType)
                        target_entity = target_type[11:-1]
                        if target_entity is not None and isinstance(target_entity, str):
                            parts = target_entity.split(".")
                            if parts and len(parts) > 0:
                                target_entity = parts[-1]
                    else:
                        # Handle direct entity type reference
                        if target_type is not None and isinstance(target_type, str):
                            parts = target_type.split(".")
                            if parts and len(parts) > 0:
                                target_entity = parts[-1]
                        else:
                            target_entity = ""

                    schema_data["relationships"].append(
                        {
                            "source_entity": source_entity,
                            "target_entity": target_entity,
                            "name": nav_prop.get("Name"),
                            "type": "one-to-one" if target_entity else "one-to-many",
                        }
                    )

            return schema_data

        except ET.ParseError as e:
            self.log.error(f"Error parsing XML: {str(e)}")
            raise ValueError(f"Failed to parse OData metadata XML: {str(e)}")
        except Exception as e:
            self.log.error(f"Error processing schema: {str(e)}")
            raise ValueError(f"Failed to process OData schema: {str(e)}")


class FileMakerCreateRecordOperator(BaseOperator):
    """
    Creates a new record in FileMaker Cloud using the OData API.

    :param table: The table name (OData entity set) to create a record in
    :type table: str
    :param data: Dictionary containing the field values for the new record
    :type data: Dict[str, Any]
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "data")
    template_ext = ()
    ui_color = "#c2e3f0"  # Light blue

    @apply_defaults
    def __init__(
        self,
        *,
        table: str,
        data: Dict[str, Any],
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.data = data
        self.filemaker_conn_id = filemaker_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Creates a new record in FileMaker Cloud and returns the created record.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: The created record response from FileMaker
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Creating record in FileMaker table '{self.table}'")

        # Initialize the FileMaker hook
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Create the record
        result = hook.create_record(table=self.table, data=self.data)

        # Log the result
        self.log.info(f"Successfully created record in table '{self.table}'")

        return result


class FileMakerUpdateRecordOperator(BaseOperator):
    """
    Updates an existing record in FileMaker Cloud using the OData API.

    :param table: The table name (OData entity set) to update a record in
    :type table: str
    :param record_id: The ID of the record to update
    :type record_id: str
    :param data: Dictionary containing the field values to update
    :type data: Dict[str, Any]
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "record_id", "data")
    template_ext = ()
    ui_color = "#e0f0c2"  # Light green

    @apply_defaults
    def __init__(
        self,
        *,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.record_id = record_id
        self.data = data
        self.filemaker_conn_id = filemaker_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Updates an existing record in FileMaker Cloud and returns the update response.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: The update response from FileMaker
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Updating record '{self.record_id}' in FileMaker table '{self.table}'")

        # Initialize the FileMaker hook
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Update the record
        result = hook.update_record(table=self.table, record_id=self.record_id, data=self.data)

        # Log the result
        self.log.info(f"Successfully updated record '{self.record_id}' in table '{self.table}'")

        return result


class FileMakerDeleteRecordOperator(BaseOperator):
    """
    Deletes a record from FileMaker Cloud using the OData API.

    :param table: The table name (OData entity set) to delete a record from
    :type table: str
    :param record_id: The ID of the record to delete
    :type record_id: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "record_id")
    template_ext = ()
    ui_color = "#f0c2e3"  # Light pink

    @apply_defaults
    def __init__(
        self,
        *,
        table: str,
        record_id: str,
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.record_id = record_id
        self.filemaker_conn_id = filemaker_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Deletes a record from FileMaker Cloud and returns the deletion response.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: The deletion response from FileMaker
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Deleting record '{self.record_id}' from FileMaker table '{self.table}'")

        # Initialize the FileMaker hook
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Delete the record
        result = hook.delete_record(table=self.table, record_id=self.record_id)

        # Log the result
        self.log.info(f"Successfully deleted record '{self.record_id}' from table '{self.table}'")

        return result


class FileMakerBulkCreateOperator(BaseOperator):
    """
    Creates multiple records in FileMaker Cloud in a batch operation.

    :param table: The table name (OData entity set) to create records in
    :type table: str
    :param records: List of dictionaries containing the field values for each new record
    :type records: List[Dict[str, Any]]
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "records")
    template_ext = ()
    ui_color = "#c2f0e3"  # Light cyan

    @apply_defaults
    def __init__(
        self,
        *,
        table: str,
        records: List[Dict[str, Any]],
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.records = records
        self.filemaker_conn_id = filemaker_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Creates multiple records in FileMaker Cloud and returns the batch creation response.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: The batch creation response from FileMaker
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Bulk creating {len(self.records)} records in FileMaker table '{self.table}'")

        # Initialize the FileMaker hook
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Create the records in bulk
        result = hook.bulk_create_records(table=self.table, records=self.records)

        # Log the result
        self.log.info(f"Successfully bulk created {len(self.records)} records in table '{self.table}'")

        return result


class FileMakerExecuteFunctionOperator(BaseOperator):
    """
    Executes a FileMaker script/function through the OData API.

    :param function_name: The name of the FileMaker script/function to execute
    :type function_name: str
    :param parameters: Dictionary of parameters to pass to the function (optional)
    :type parameters: Dict[str, Any]
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    """

    template_fields = ("function_name", "parameters")
    template_ext = ()
    ui_color = "#f0e3c2"  # Light orange

    @apply_defaults
    def __init__(
        self,
        *,
        function_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.function_name = function_name
        self.parameters = parameters
        self.filemaker_conn_id = filemaker_conn_id

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Executes a FileMaker script/function and returns the execution response.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: The function execution response from FileMaker
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Executing FileMaker function '{self.function_name}'")

        # Initialize the FileMaker hook
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Execute the function
        result = hook.execute_function(function_name=self.function_name, parameters=self.parameters)

        # Log the result
        self.log.info(f"Successfully executed FileMaker function '{self.function_name}'")

        return result


class FileMakerToS3Operator(BaseOperator):
    """
    Extracts data from FileMaker Cloud and uploads it to Amazon S3.

    :param endpoint: The OData endpoint to extract data from
    :type endpoint: str
    :param s3_bucket: The S3 bucket to upload data to
    :type s3_bucket: str
    :param s3_key: The S3 key to upload data to
    :type s3_key: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    :param aws_conn_id: The Airflow connection ID for AWS
    :type aws_conn_id: str
    :param filter_query: OData filter query expression (optional)
    :type filter_query: str
    :param select: Comma-separated list of fields to extract (optional)
    :type select: str
    :param expand: Related entities to expand (optional)
    :type expand: str
    :param file_format: Format to save the data (json, csv, parquet) (default: json)
    :type file_format: str
    :param replace: Whether to replace existing S3 file (default: True)
    :type replace: bool
    :param top: Maximum number of records to extract (optional)
    :type top: int
    :param batch_size: Number of records to fetch in each batch (default: 1000)
    :type batch_size: int
    """

    template_fields = ("endpoint", "s3_bucket", "s3_key", "filter_query")
    template_ext = ()
    ui_color = "#80cbc4"  # Teal

    @apply_defaults
    def __init__(
        self,
        *,
        endpoint: str,
        s3_bucket: str,
        s3_key: str,
        filemaker_conn_id: str = "filemaker_default",
        aws_conn_id: str = "aws_default",
        filter_query: Optional[str] = None,
        select: Optional[str] = None,
        expand: Optional[str] = None,
        file_format: str = "json",
        replace: bool = True,
        top: Optional[int] = None,
        batch_size: int = 1000,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.s3_bucket = s3_bucket
        self.s3_key = s3_key
        self.filemaker_conn_id = filemaker_conn_id
        self.aws_conn_id = aws_conn_id
        self.filter_query = filter_query
        self.select = select
        self.expand = expand
        self.file_format = file_format.lower()
        self.replace = replace
        self.top = top
        self.batch_size = batch_size

    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the operator.

        Extracts data from FileMaker Cloud and uploads it to Amazon S3.

        :param context: The task context
        :type context: Dict[str, Any]
        :return: Dictionary with upload details
        :rtype: Dict[str, Any]
        """
        import tempfile

        # Extract just the table name from the endpoint, removing any leading/trailing slashes
        table_name = self.endpoint.strip("/")

        # If it contains a path, take only the last part which should be the table name
        if "/" in table_name:
            table_name = table_name.split("/")[-1]

        self.log.info(
            f"Extracting data from FileMaker table '{table_name}' "
            f"and uploading to S3: s3://{self.s3_bucket}/{self.s3_key}"
        )

        # Initialize hooks
        filemaker_hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        s3_hook = S3Hook(aws_conn_id=self.aws_conn_id)

        # Create parameters for the query
        query_params = {}
        if self.filter_query:
            query_params["filter_query"] = self.filter_query
        if self.select:
            query_params["select"] = self.select
        if self.expand:
            query_params["expand"] = self.expand
        if self.top:
            query_params["top"] = self.top

        # Additional parameters for safety and efficiency
        query_params["page_size"] = min(self.batch_size, 1000)  # Limit to reasonable page size
        query_params["max_pages"] = 10  # Set a reasonable limit on pages

        # Get data from FileMaker with proper parameters
        data = filemaker_hook.get_records(table=table_name, **query_params)

        # Convert data to the requested format
        with tempfile.NamedTemporaryFile(mode="w+", suffix=f".{self.file_format}") as tmp:
            if self.file_format == "json":
                import json

                json.dump(data, tmp)
            elif self.file_format == "csv":
                import csv

                import pandas as pd

                # Convert to DataFrame
                records = data.get("value", [])
                df = pd.DataFrame(records)

                # Write to CSV
                df.to_csv(tmp.name, index=False, quoting=csv.QUOTE_NONNUMERIC)
            elif self.file_format == "parquet":
                import pandas as pd

                # Convert to DataFrame
                records = data.get("value", [])
                df = pd.DataFrame(records)

                # Write to parquet
                df.to_parquet(tmp.name, index=False)
            else:
                raise ValueError(f"Unsupported file format: {self.file_format}")

            # Flush to make sure all data is written
            tmp.flush()

            # Upload to S3
            tmp.seek(0)
            s3_hook.load_file(filename=tmp.name, key=self.s3_key, bucket_name=self.s3_bucket, replace=self.replace)

        # Log the result
        num_records = len(data.get("value", []))
        self.log.info(f"Successfully uploaded {num_records} records to s3://{self.s3_bucket}/{self.s3_key}")

        return {
            "records": num_records,
            "s3_bucket": self.s3_bucket,
            "s3_key": self.s3_key,
            "format": self.file_format,
            "source": self.endpoint,
        }


class FileMakerRawOperator(BaseOperator):
    """
    Executes a raw request to the specified endpoint with the given parameters.

    :param endpoint: The endpoint to execute the request to
    :type endpoint: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    :param accept_format: The accept header format for the OData API
    :type accept_format: str
    :param params: Dictionary of parameters to pass to the endpoint
    :type params: Dict[str, Any]
    """

    template_fields = ("endpoint", "params")
    template_ext = ()
    ui_color = "#f0e3c2"  # Light orange

    @apply_defaults
    def __init__(
        self,
        *,
        endpoint: str,
        filemaker_conn_id: str = "filemaker_default",
        accept_format: str = "application/json",
        params: Dict[str, Any] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.filemaker_conn_id = filemaker_conn_id
        self.accept_format = accept_format
        self.params = params

    def execute(self, context) -> Any:
        """
        Execute a request to the specified endpoint with the given parameters.

        :param context: The task context
        :return: The raw API response
        :rtype: Any
        """
        self.log.info(f"Executing raw request to endpoint: {self.endpoint}")

        # Initialize hook if not already initialized
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)

        # Ensure we have the base URL
        base_url = hook.get_base_url()

        # Build full URL - handling whether endpoint already has proper structure
        if self.endpoint.startswith("http"):
            # Endpoint is already a full URL
            full_url = self.endpoint
        elif self.endpoint.startswith("/"):
            # Endpoint starts with '/' - avoid double slash
            full_url = f"{base_url}{self.endpoint}"
        else:
            # Standard case - append to base URL with a slash
            full_url = f"{base_url}/{self.endpoint}"

        self.log.info(f"Full URL: {full_url}")

        # Get response with validation
        response = hook.get_odata_response(endpoint=full_url, params=self.params, accept_format=self.accept_format)

        return response
