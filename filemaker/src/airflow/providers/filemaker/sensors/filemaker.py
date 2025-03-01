"""
Sensors for FileMaker Cloud integration.

This module contains sensors to detect conditions in FileMaker Cloud tables.
"""

from typing import Any, Callable, Dict, Optional

# Simplify to use the most common location in modern Airflow
from airflow.sensors.base import BaseSensorOperator

from airflow.providers.filemaker.hooks.filemaker import FileMakerHook


class FileMakerDataSensor(BaseSensorOperator):
    """
    Sensor that detects if new data is available in a FileMaker table
    based on specified conditions.

    :param table: The table name to monitor
    :type table: str
    :param condition: OData $filter expression to apply as a condition
    :type condition: str
    :param expected_count: The expected count to satisfy the condition
    :type expected_count: int
    :param comparison_operator: The operator to use for comparison ('>=', '==', '>', '<', '<=')
    :type comparison_operator: str
    :param filemaker_conn_id: The connection ID to use for FileMaker
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "condition")

    def __init__(
        self,
        *,
        table: str,
        condition: Optional[str] = None,
        expected_count: int = 1,
        comparison_operator: str = ">=",
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.condition = condition
        self.expected_count = expected_count
        self.comparison_operator = comparison_operator
        self.filemaker_conn_id = filemaker_conn_id

        # Validate comparison operator
        if self.comparison_operator not in (">=", "==", ">", "<", "<="):
            raise ValueError(
                f"Invalid comparison operator: {self.comparison_operator}. " "Must be one of '>=', '==', '>', '<', '<='"
            )

    def poke(self, context) -> bool:
        """
        Determine if the sensor criteria are met.

        :param context: The task context
        :return: True if criteria are met, False otherwise
        :rtype: bool
        """
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        base_url = hook.get_base_url()

        # Build endpoint with OData query
        endpoint = f"{base_url}/{self.table}/$count"
        if self.condition:
            endpoint = f"{endpoint}?$filter={self.condition}"

        self.log.info(f"Checking data presence with endpoint: {endpoint}")

        # Get the count of records matching the condition
        try:
            count = int(hook.get_odata_response(endpoint=endpoint, accept_format="text/plain"))

            self.log.info(f"Found {count} records (expected {self.comparison_operator} {self.expected_count})")

            # Evaluate the condition using the specified comparison operator
            result = self._evaluate_condition(count, self.expected_count, self.comparison_operator)
            return result

        except Exception as e:
            self.log.error(f"Error checking FileMaker data: {str(e)}")
            return False

    def _evaluate_condition(self, actual: int, expected: int, operator: str) -> bool:
        """
        Evaluates if the condition is met using the specified comparison operator.

        :param actual: The actual count
        :type actual: int
        :param expected: The expected count
        :type expected: int
        :param operator: The comparison operator
        :type operator: str
        :return: True if condition is met, False otherwise
        :rtype: bool
        """
        if operator == ">=":
            return actual >= expected
        elif operator == "==":
            return actual == expected
        elif operator == ">":
            return actual > expected
        elif operator == "<":
            return actual < expected
        elif operator == "<=":
            return actual <= expected
        else:
            # Should never reach here as we validate in __init__
            raise ValueError(f"Invalid comparison operator: {operator}")


class FileMakerChangeSensor(BaseSensorOperator):
    """
    Sensor that detects if data has changed in a FileMaker table
    since a previous execution or timestamp.

    :param table: The table name to monitor
    :type table: str
    :param modified_field: The name of the field containing modification timestamps
    :type modified_field: str
    :param last_modified_ts: The timestamp to compare against (can be a template)
    :type last_modified_ts: str
    :param filemaker_conn_id: The connection ID to use for FileMaker
    :type filemaker_conn_id: str
    """

    template_fields = ("table", "last_modified_ts")

    def __init__(
        self,
        *,
        table: str,
        modified_field: str,
        last_modified_ts: Optional[str] = None,
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.table = table
        self.modified_field = modified_field
        self.last_modified_ts = last_modified_ts
        self.filemaker_conn_id = filemaker_conn_id

    def poke(self, context) -> bool:
        """
        Determine if data has changed since the last check.

        :param context: The task context
        :return: True if data has changed, False otherwise
        :rtype: bool
        """
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        base_url = hook.get_base_url()

        # If no timestamp provided, get the current max timestamp and return False
        # This allows the sensor to establish a baseline on first run
        if not self.last_modified_ts:
            self._set_baseline_timestamp(hook, base_url)
            return False

        # Build query to check for records modified after last_modified_ts
        condition = f"{self.modified_field} gt {self.last_modified_ts}"
        endpoint = f"{base_url}/{self.table}/$count?$filter={condition}"

        self.log.info(f"Checking for changes since {self.last_modified_ts} with endpoint: {endpoint}")

        try:
            count = int(hook.get_odata_response(endpoint=endpoint, accept_format="text/plain"))

            self.log.info(f"Found {count} modified records since {self.last_modified_ts}")

            # If we have new records, update the timestamp before returning
            if count > 0:
                self._update_timestamp(hook, base_url)
                return True

            return False

        except Exception as e:
            self.log.error(f"Error checking for FileMaker changes: {str(e)}")
            return False

    def _set_baseline_timestamp(self, hook: FileMakerHook, base_url: str) -> None:
        """
        Sets the baseline timestamp for change detection.

        :param hook: The FileMaker hook
        :type hook: FileMakerHook
        :param base_url: The base URL for OData API
        :type base_url: str
        """
        # Query to get the most recent modification timestamp
        endpoint = f"{base_url}/{self.table}?$orderby={self.modified_field} desc&$top=1&$select={self.modified_field}"

        try:
            result = hook.get_odata_response(endpoint=endpoint)

            if "value" in result and len(result["value"]) > 0:
                latest_ts = result["value"][0][self.modified_field]
                self.log.info(f"Setting baseline timestamp to: {latest_ts}")

                # Store the timestamp in XCom for future runs
                self.xcom_push(context=None, key="last_modified_ts", value=latest_ts)
                self.last_modified_ts = latest_ts
            else:
                self.log.warning(f"No records found in {self.table} to establish baseline timestamp")

        except Exception as e:
            self.log.error(f"Error setting baseline timestamp: {str(e)}")

    def _update_timestamp(self, hook: FileMakerHook, base_url: str) -> None:
        """
        Updates the timestamp after changes are detected.

        :param hook: The FileMaker hook
        :type hook: FileMakerHook
        :param base_url: The base URL for OData API
        :type base_url: str
        """
        # Query to get the most recent modification timestamp
        endpoint = f"{base_url}/{self.table}?$orderby={self.modified_field} desc&$top=1&$select={self.modified_field}"

        try:
            result = hook.get_odata_response(endpoint=endpoint)

            if "value" in result and len(result["value"]) > 0:
                latest_ts = result["value"][0][self.modified_field]
                self.log.info(f"Updating timestamp to: {latest_ts}")

                # Store the timestamp in XCom for future runs
                self.xcom_push(context=None, key="last_modified_ts", value=latest_ts)
                self.last_modified_ts = latest_ts

        except Exception as e:
            self.log.error(f"Error updating timestamp: {str(e)}")


class FileMakerCustomSensor(BaseSensorOperator):
    """
    Allows for custom sensor logic with a FileMaker Cloud OData query.

    :param endpoint: The OData endpoint to query
    :type endpoint: str
    :param success_fn: A callable that takes the response data and returns a boolean
    :type success_fn: Callable[[Dict[str, Any]], bool]
    :param filemaker_conn_id: The connection ID to use for FileMaker
    :type filemaker_conn_id: str
    """

    template_fields = ("endpoint",)

    def __init__(
        self,
        *,
        endpoint: str,
        success_fn: Callable[[Dict[str, Any]], bool],
        filemaker_conn_id: str = "filemaker_default",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.endpoint = endpoint
        self.success_fn = success_fn
        self.filemaker_conn_id = filemaker_conn_id

    def poke(self, context) -> bool:
        """
        Execute the custom sensor logic.

        :param context: The task context
        :return: True if the custom condition is met, False otherwise
        :rtype: bool
        """
        hook = FileMakerHook(filemaker_conn_id=self.filemaker_conn_id)
        base_url = hook.get_base_url()

        # Build full URL
        if self.endpoint.startswith("/"):
            full_url = f"{base_url}{self.endpoint}"
        else:
            full_url = f"{base_url}/{self.endpoint}"

        self.log.info(f"Running custom sensor with endpoint: {full_url}")

        try:
            # Get the data
            data = hook.get_odata_response(endpoint=full_url)

            # Apply the custom function to determine if condition is met
            result = self.success_fn(data)
            self.log.info(f"Custom sensor returned: {result}")

            return result

        except Exception as e:
            self.log.error(f"Error in custom FileMaker sensor: {str(e)}")
            return False
