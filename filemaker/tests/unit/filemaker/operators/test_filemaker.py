"""
Unit tests for the FileMaker operators.
"""
import unittest
from unittest.mock import patch, MagicMock

from airflow.providers.filemaker.operators.filemaker import FileMakerQueryOperator, FileMakerExtractOperator


class TestFileMakerQueryOperator(unittest.TestCase):
    """Test class for FileMakerQueryOperator."""

    @patch('airflow.providers.filemaker.operators.filemaker.FileMakerHook')
    def test_execute(self, mock_hook_class):
        """Test execute method."""
        # Setup mock
        mock_hook = MagicMock()
        mock_hook.get_base_url.return_value = "https://test-host/fmi/odata/v4/test-db"
        mock_hook.get_odata_response.return_value = {"value": [{"id": 1}]}
        mock_hook_class.return_value = mock_hook

        # Execute operator
        operator = FileMakerQueryOperator(
            task_id="test_task",
            endpoint="test_endpoint",
            filemaker_conn_id="test_conn_id"
        )
        result = operator.execute(context={})

        # Assertions
        self.assertEqual(result, {"value": [{"id": 1}]})
        mock_hook_class.assert_called_once_with(filemaker_conn_id="test_conn_id")
        mock_hook.get_base_url.assert_called_once()
        mock_hook.get_odata_response.assert_called_once_with(
            endpoint="https://test-host/fmi/odata/v4/test-db/test_endpoint",
            accept_format="application/json"
        )


class TestFileMakerExtractOperator(unittest.TestCase):
    """Test class for FileMakerExtractOperator."""

    @patch('airflow.providers.filemaker.operators.filemaker.FileMakerQueryOperator.execute')
    def test_execute(self, mock_query_execute):
        """Test execute method."""
        # Setup mock
        mock_query_execute.return_value = {"value": [{"id": 1}]}

        # Execute operator
        operator = FileMakerExtractOperator(
            task_id="test_task",
            endpoint="test_endpoint",
            filemaker_conn_id="test_conn_id"
        )
        result = operator.execute(context={})

        # Assertions
        self.assertEqual(result, {"value": [{"id": 1}]})
        mock_query_execute.assert_called_once_with({})


if __name__ == '__main__':
    unittest.main()
