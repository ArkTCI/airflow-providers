"""
Unit tests for the FileMaker sensors.
"""
import unittest
from unittest.mock import patch, MagicMock

from airflow.providers.filemaker.sensors.filemaker import FileMakerDataSensor, FileMakerChangeSensor


class TestFileMakerDataSensor(unittest.TestCase):
    """Test class for FileMakerDataSensor."""

    @patch('airflow.providers.filemaker.sensors.filemaker.FileMakerHook')
    def test_poke_success(self, mock_hook_class):
        """Test poke method when condition is met."""
        # Setup mock
        mock_hook = MagicMock()
        mock_hook.get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_hook.get_odata_response.return_value = "5"  # 5 records found
        mock_hook_class.return_value = mock_hook

        # Execute sensor
        sensor = FileMakerDataSensor(
            task_id="test_task",
            table="test_table",
            condition="field eq 'value'",
            expected_count=3,  # Expecting at least 3 records
            filemaker_conn_id="test_conn_id"
        )
        result = sensor.poke(context={})

        # Assertions
        self.assertTrue(result)  # 5 >= 3, so condition is met
        mock_hook_class.assert_called_once_with(filemaker_conn_id="test_conn_id")
        mock_hook.get_base_url.assert_called_once()
        mock_hook.get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/test_table/$count?$filter=field eq 'value'",
            accept_format="text/plain"
        )

    @patch('airflow.providers.filemaker.sensors.filemaker.FileMakerHook')
    def test_poke_failure(self, mock_hook_class):
        """Test poke method when condition is not met."""
        # Setup mock
        mock_hook = MagicMock()
        mock_hook.get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_hook.get_odata_response.return_value = "2"  # 2 records found
        mock_hook_class.return_value = mock_hook

        # Execute sensor
        sensor = FileMakerDataSensor(
            task_id="test_task",
            table="test_table",
            condition="field eq 'value'",
            expected_count=3,  # Expecting at least 3 records
            filemaker_conn_id="test_conn_id"
        )
        result = sensor.poke(context={})

        # Assertions
        self.assertFalse(result)  # 2 < 3, so condition is not met


class TestFileMakerChangeSensor(unittest.TestCase):
    """Test class for FileMakerChangeSensor."""

    @patch('airflow.providers.filemaker.sensors.filemaker.FileMakerHook')
    def test_poke_with_changes(self, mock_hook_class):
        """Test poke method when changes are detected."""
        # Setup mock
        mock_hook = MagicMock()
        mock_hook.get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_hook.get_odata_response.return_value = "3"  # 3 changed records
        mock_hook_class.return_value = mock_hook

        # Execute sensor
        sensor = FileMakerChangeSensor(
            task_id="test_task",
            table="test_table",
            modified_field="modified_date",
            last_modified_ts="2023-01-01T00:00:00Z",
            filemaker_conn_id="test_conn_id"
        )
        result = sensor.poke(context={})

        # Assertions
        self.assertTrue(result)  # Changes detected
        mock_hook_class.assert_called_once_with(filemaker_conn_id="test_conn_id")


if __name__ == '__main__':
    unittest.main()
