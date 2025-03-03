"""
Operators for FileMaker Cloud integration.

This module contains operators for executing tasks against FileMaker Cloud's OData API.
"""

from typing import Any, Dict, Optional

from airflow.models import BaseOperator
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
        filemaker_conn_id: str = "filemaker_default",
        accept_format: str = "application/json",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.filemaker_conn_id = filemaker_conn_id
        self.accept_format = accept_format

    def execute(self, context) -> Dict[str, Any]:
        """
        Execute the OData query.

        :param context: The task context
        :return: The query result data
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Executing OData query on endpoint: {self.endpoint}")

        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        base_url = hook.get_base_url()

        # Build full URL - handling whether endpoint already starts with '/'
        if self.endpoint.startswith("/"):
            full_url = f"{base_url}{self.endpoint}"
        else:
            full_url = f"{base_url}/{self.endpoint}"

        self.log.info(f"Full URL: {full_url}")

        # Execute query
        result = hook.get_odata_response(endpoint=full_url, accept_format=self.accept_format)

        return result


class FileMakerExtractOperator(BaseOperator):
    """
    Extracts data from FileMaker Cloud and optionally saves it to a destination.

    This operator extends the basic query functionality to handle common extraction
    patterns and save the results to a destination format/location.

    :param endpoint: The OData endpoint to query
    :type endpoint: str
    :param filemaker_conn_id: The Airflow connection ID for FileMaker Cloud
    :type filemaker_conn_id: str
    :param output_path: Optional path to save the output
    :type output_path: Optional[str]
    :param format: Output format ('json', 'csv', etc.)
    :type format: str
    :param accept_format: The accept header format for the OData API
    :type accept_format: str
    """

    template_fields = ("endpoint", "output_path")
    template_ext = ()
    ui_color = "#e8c1f0"  # Lighter purple than query operator

    @apply_defaults
    def __init__(
        self,
        *,
        endpoint: str,
        filemaker_conn_id: str = "filemaker_default",
        output_path: Optional[str] = None,
        format: str = "json",
        accept_format: str = "application/json",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.filemaker_conn_id = filemaker_conn_id
        self.output_path = output_path
        self.format = format
        self.accept_format = accept_format

    def execute(self, context) -> Dict[str, Any]:
        """
        Execute the OData extraction.

        :param context: The task context
        :return: The extraction result data
        :rtype: Dict[str, Any]
        """
        self.log.info(f"Extracting data from FileMaker Cloud endpoint: {self.endpoint}")

        # Use the query operator to fetch data
        query_op = FileMakerQueryOperator(
            task_id=f"{self.task_id}_query",
            endpoint=self.endpoint,
            filemaker_conn_id=self.filemaker_conn_id,
            accept_format=self.accept_format,
        )

        result = query_op.execute(context)

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

        # Create directory if it doesn't exist
        if self.output_path:
            os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

        self.log.info(f"Saving data to {self.output_path} in {self.format} format")

        if self.output_path:
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
        else:
            self.log.warning("No output path specified, skipping file write operation")


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
