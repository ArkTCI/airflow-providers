#!/usr/bin/env python
"""
Test script for FileMaker provider package.

This script provides simple tests to verify the functionality
of the FileMaker provider components.
"""
import os
import sys
import json
import logging
from typing import Dict, Any, Optional
from unittest.mock import MagicMock, patch
import unittest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger('filemaker_provider_test')

# Try to import provider components
try:
    # Add current directory to path for package discovery
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from filemaker.hooks.filemaker import FileMakerHook
    from filemaker.auth.cognitoauth import FileMakerCloudAuth
    from filemaker.operators.filemaker import (
        FileMakerQueryOperator,
        FileMakerExtractOperator,
        FileMakerSchemaOperator
    )
    from filemaker.sensors.filemaker import (
        FileMakerDataSensor,
        FileMakerChangeSensor,
        FileMakerCustomSensor
    )
    from filemaker import get_provider_info
    
    logger.info("Successfully imported FileMaker provider components")
except ImportError as e:
    logger.error(f"Failed to import FileMaker provider components: {e}")
    logger.info("Make sure you've installed the package in development mode: `pip install -e .`")
    sys.exit(1)

def test_provider_info():
    """Test that provider info is correctly defined."""
    info = get_provider_info()
    logger.info(f"Provider info: {json.dumps(info, indent=2)}")
    
    assert info['name'] == 'FileMaker Cloud', f"Unexpected provider name: {info['name']}"
    assert info['package-name'] == 'arktci-airflow-provider-filemaker', \
        f"Unexpected package name: {info['package-name']}"
    
    # Check for required provider info fields
    required_fields = ['name', 'package-name', 'versions']
    for field in required_fields:
        assert field in info, f"Missing required field in provider info: {field}"
    
    # Verify that versions is a non-empty list
    assert isinstance(info['versions'], list), "Versions should be a list"
    assert len(info['versions']) > 0, "Versions list should not be empty"
    
    logger.info("✅ Provider info test passed")
    return info

def test_hook_initialization():
    """Test that the FileMaker hook can be initialized."""
    try:
        # Mock the get_connection method to avoid connection lookup errors
        with patch('airflow.hooks.base.BaseHook.get_connection') as mock_get_connection:
            # Set up the mock to return a connection object with our test parameters
            conn_params = mock_connection_params()
            mock_conn = MagicMock()
            mock_conn.host = conn_params['host']
            mock_conn.schema = conn_params['schema']
            mock_conn.login = conn_params['login']
            mock_conn.password = conn_params['password']
            mock_get_connection.return_value = mock_conn
            
            hook = FileMakerHook()
            logger.info(f"Successfully initialized hook: {hook}")
            
            # Check hook properties if available
            # The hook might not have these properties depending on implementation
            try:
                logger.info(f"Hook default connection name: {hook.default_conn_name}")
            except AttributeError:
                logger.info("Hook does not have default_conn_name property")
                
            try:
                logger.info(f"Hook connection type: {hook.conn_type}")
            except AttributeError:
                logger.info("Hook does not have conn_type property")
            
            # Test with connection parameters
            custom_hook = FileMakerHook(
                host=conn_params['host'],
                database=conn_params['schema'],
                username=conn_params['login'],
                password=conn_params['password']
            )
            
            assert custom_hook.host == conn_params['host'], "Host not set correctly"
            assert custom_hook.database == conn_params['schema'], "Database not set correctly"
            assert custom_hook.username == conn_params['login'], "Username not set correctly"
            assert custom_hook.password == conn_params['password'], "Password not set correctly"
            
            logger.info("✅ Hook initialization test passed")
            return hook
    except Exception as e:
        logger.error(f"Failed to initialize hook: {e}")
        return None

def test_operators_initialization():
    """Test that all FileMaker operators can be initialized."""
    try:
        # Initialize query operator
        query_op = FileMakerQueryOperator(
            task_id="test_query",
            endpoint="TestTable",
            filemaker_conn_id="filemaker_default"
        )
        assert query_op.endpoint == "TestTable", "Query operator endpoint not set correctly"
        
        # Initialize extract operator
        extract_op = FileMakerExtractOperator(
            task_id="test_extract",
            endpoint="TestTable",
            output_path="/tmp/test_output.json",
            format="json",
            filemaker_conn_id="filemaker_default"
        )
        assert extract_op.output_path == "/tmp/test_output.json", "Extract operator path not set correctly"
        
        # Initialize schema operator
        schema_op = FileMakerSchemaOperator(
            task_id="test_schema",
            filemaker_conn_id="filemaker_default"
        )
        
        logger.info("✅ Operators initialization test passed")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize operators: {e}")
        return False

def test_sensors_initialization():
    """Test that all FileMaker sensors can be initialized."""
    try:
        # Initialize data sensor
        data_sensor = FileMakerDataSensor(
            task_id="test_data_sensor",
            table="TestTable",
            condition="status eq 'ready'",
            expected_count=1,
            filemaker_conn_id="filemaker_default"
        )
        assert data_sensor.table == "TestTable", "Data sensor table not set correctly"
        
        # Initialize change sensor
        change_sensor = FileMakerChangeSensor(
            task_id="test_change_sensor",
            table="TestTable",
            modified_field="ModifiedTimestamp",
            filemaker_conn_id="filemaker_default"
        )
        assert change_sensor.modified_field == "ModifiedTimestamp", "Change sensor field not set correctly"
        
        # Initialize custom sensor with a test function
        def test_success_fn(data):
            return True
            
        custom_sensor = FileMakerCustomSensor(
            task_id="test_custom_sensor",
            endpoint="test/endpoint",
            success_fn=test_success_fn,
            filemaker_conn_id="filemaker_default"
        )
        assert custom_sensor.endpoint == "test/endpoint", "Custom sensor endpoint not set correctly"
        
        logger.info("✅ Sensors initialization test passed")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize sensors: {e}")
        return False

def test_hook_get_base_url():
    """Test the get_base_url method of FileMakerHook."""
    # Test with URL that includes https://
    hook1 = FileMakerHook(
        host='https://test.filemaker-cloud.com',
        database='test-db',
        filemaker_conn_id=None  # Disable connection lookup
    )
    base_url1 = hook1.get_base_url()
    assert base_url1 == 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db', f"Incorrect base URL: {base_url1}"
    
    # Test with URL that does not include https://
    hook2 = FileMakerHook(
        host='test.filemaker-cloud.com',
        database='test-db',
        filemaker_conn_id=None  # Disable connection lookup
    )
    base_url2 = hook2.get_base_url()
    assert base_url2 == 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db', f"Incorrect base URL: {base_url2}"
    
    logger.info("✅ Hook get_base_url test passed")
    return True

def mock_connection_params() -> Dict[str, Any]:
    """Return mock connection parameters for testing."""
    return {
        'host': 'mock-fmcloud.claris.com',
        'login': 'test-username',
        'password': 'test-password',
        'schema': 'TestDatabase',
        'extra': json.dumps({
            'user_pool_id': 'us-west-2_abcdefghi',
            'client_id': '1a2b3c4d5e6f7g8h9i0j',
            'region': 'us-west-2'
        })
    }

def main():
    """Run all tests."""
    logger.info("Testing FileMaker provider...")
    
    # Run provider info test
    test_provider_info()
    
    # Run hook initialization test
    test_hook_initialization()
    
    # Test hook get_base_url method
    test_hook_get_base_url()
    
    # Test operators initialization
    test_operators_initialization()
    
    # Test sensors initialization
    test_sensors_initialization()
    
    logger.info("All tests completed!")

if __name__ == "__main__":
    main() 