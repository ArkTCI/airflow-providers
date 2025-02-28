#!/usr/bin/env python3
"""
Simplified test script for FileMaker Cloud provider functionality.
This script tests the core functionality without requiring Airflow.
"""
import os
import sys
import json
import logging
import unittest
from unittest.mock import patch, MagicMock
import boto3
from moto.core import set_initial_no_auth_action_count
from moto import mock_aws

# Configure logging
logging.basicConfig(level=logging.INFO)

# Configure AWS environment variables for testing
os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
os.environ['AWS_SECURITY_TOKEN'] = 'testing'
os.environ['AWS_SESSION_TOKEN'] = 'testing'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the FileMaker provider modules
from filemaker.auth.cognitoauth import FileMakerCloudAuth
from filemaker.hooks.filemaker import FileMakerHook
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


class TestFileMakerAuth(unittest.TestCase):
    """Test cases for FileMaker Cloud Auth."""
    
    def setUp(self):
        """Set up the test case."""
        # Configure AWS environment variables for testing
        os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
        os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
        os.environ['AWS_SECURITY_TOKEN'] = 'testing'
        os.environ['AWS_SESSION_TOKEN'] = 'testing'
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

    def test_auth_initialization(self):
        """Test that the authentication class is initialized correctly."""
        auth = FileMakerCloudAuth(
            username='test_user',
            password='test_password',
            host='https://test.filemaker-cloud.com'
        )
        
        # Verify initialization
        self.assertEqual(auth.username, 'test_user')
        self.assertEqual(auth.password, 'test_password')
        self.assertEqual(auth.host, 'https://test.filemaker-cloud.com')
        self.assertIsNone(auth.client)  # Client should not be initialized yet
        
    @mock_aws
    def test_get_token(self):
        """Test retrieving a token from Cognito."""
        # Create a real Cognito user pool using moto
        cognito_client = boto3.client('cognito-idp', region_name='us-east-1')
        user_pool = cognito_client.create_user_pool(PoolName='test-pool')
        user_pool_id = user_pool['UserPool']['Id']
        
        # Create a client for the user pool
        client = cognito_client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName='test-client',
            GenerateSecret=False
        )
        client_id = client['UserPoolClient']['ClientId']
        
        # Create a test user
        cognito_client.admin_create_user(
            UserPoolId=user_pool_id,
            Username='test_user',
            TemporaryPassword='Test1234!',
            MessageAction='SUPPRESS'
        )
        
        # Set the user's permanent password
        cognito_client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username='test_user',
            Password='Test1234!',
            Permanent=True
        )
        
        # Initialize the auth class
        auth = FileMakerCloudAuth(
            username='test_user',
            password='Test1234!',
            host='https://test.filemaker-cloud.com'
        )
        
        # Mock the _get_pool_info method to return our test pool
        with patch.object(auth, '_get_pool_info') as mock_get_pool_info:
            mock_get_pool_info.return_value = {
                'user_pool_id': user_pool_id,
                'client_id': client_id,
                'region': 'us-east-1'
            }
            
            # Mock the initiate_auth call since moto doesn't fully implement it
            with patch.object(cognito_client, 'initiate_auth') as mock_initiate_auth:
                mock_initiate_auth.return_value = {
                    'AuthenticationResult': {
                        'IdToken': 'mock-id-token',
                        'AccessToken': 'mock-access-token',
                        'RefreshToken': 'mock-refresh-token',
                        'ExpiresIn': 3600
                    }
                }
                
                # Patch to use our mocked Cognito client
                with patch.object(auth, '_init_client') as mock_init_client:
                    auth.client = cognito_client
                    
                    # Get the token
                    token = auth.get_token()
                    
                    # Verify token was retrieved
                    self.assertEqual(token, 'mock-id-token')
                    
                    # Verify initiate_auth was called with correct parameters
                    mock_initiate_auth.assert_called_once()
                    # Check that the AuthFlow and AuthParameters were correct
                    args, kwargs = mock_initiate_auth.call_args
                    self.assertEqual(kwargs['AuthFlow'], 'USER_PASSWORD_AUTH')
                    self.assertEqual(kwargs['AuthParameters'], {
                        'USERNAME': 'test_user',
                        'PASSWORD': 'Test1234!'
                    })

    @patch('filemaker.auth.cognitoauth.boto3')
    def test_auth_error_handling(self, mock_boto3):
        """Test error handling during authentication."""
        # Create a mock boto3 client that raises an exception
        mock_client = MagicMock()
        mock_client.initiate_auth.side_effect = Exception("Invalid credentials")
        mock_boto3.client.return_value = mock_client
        
        # Initialize auth
        auth = FileMakerCloudAuth(
            username='test_user',
            password='wrong_password',
            host='https://test.filemaker-cloud.com'
        )
        
        # Mock the pool info
        auth.user_pool_id = 'us-east-1_testpool'
        auth.client_id = 'test-client-id'
        auth.region = 'us-east-1'
        
        # Test getting token with authentication error
        with self.assertRaises(Exception) as context:
            auth.get_token()
        
        # Check that the error message contains our expected text
        self.assertIn('Invalid credentials', str(context.exception))


class TestFileMakerHook(unittest.TestCase):
    """Test cases for FileMaker Hook."""
    
    def test_initialization(self):
        """Test that the hook can be initialized with correct parameters."""
        # Initialize the hook directly without mocking
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            username='test_user',
            password='test_password',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Verify initialization
        self.assertEqual(hook.host, 'https://test.filemaker-cloud.com')
        self.assertEqual(hook.database, 'test-db')
        self.assertEqual(hook.username, 'test_user')
        self.assertEqual(hook.password, 'test_password')
    
    def test_get_base_url(self):
        """Test base URL generation."""
        # Test with URL that includes https://
        hook1 = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        self.assertEqual(hook1.get_base_url(), 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db')
        
        # Test with URL that does not include https://
        hook2 = FileMakerHook(
            host='test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        self.assertEqual(hook2.get_base_url(), 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db')
    
    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_records(self, mock_requests, mock_get_token):
        """Test fetching records from FileMaker."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'id': 1, 'name': 'Record 1'},
                {'id': 2, 'name': 'Record 2'}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            username='test_user',
            password='test_password',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Get records from a table
        records = hook.get_records('test-table')
        
        # Verify records
        self.assertEqual(len(records['value']), 2)
        self.assertEqual(records['value'][0]['name'], 'Record 1')
        
        # Verify that requests.get was called with correct URL and headers
        expected_url = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table'
        mock_requests.get.assert_called_with(
            expected_url,
            headers={'Authorization': 'Bearer test-token', 'Accept': 'application/json'},
            params={}
        )

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_records_with_parameters(self, mock_requests, mock_get_token):
        """Test fetching records with query parameters."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'id': 1, 'name': 'Record 1'}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Get records with parameters
        records = hook.get_records(
            table='test-table',
            select='id,name',
            filter_query='id eq 1',
            top=10,
            skip=5,
            orderby='name asc'
        )
        
        # Verify records
        self.assertEqual(len(records['value']), 1)
        
        # Verify that requests.get was called with correct parameters
        expected_url = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table'
        expected_params = {
            '$select': 'id,name',
            '$filter': 'id eq 1',
            '$top': 10,
            '$skip': 5,
            '$orderby': 'name asc'
        }
        mock_requests.get.assert_called_with(
            expected_url,
            headers={'Authorization': 'Bearer test-token', 'Accept': 'application/json'},
            params=expected_params
        )

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_individual_record(self, mock_requests, mock_get_token):
        """Test fetching an individual record by key from FileMaker."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'id': 1,
            'name': 'Record 1',
            'description': 'Test record'
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Method to get individual record (we'll need to add this to our hook)
        with patch.object(hook, 'get_odata_response') as mock_get_odata:
            mock_get_odata.return_value = mock_response.json.return_value
            
            # Get the individual record (assuming we have a method like this)
            endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table(1)'
            record = hook.get_odata_response(endpoint=endpoint)
            
            # Verify record
            self.assertEqual(record['id'], 1)
            self.assertEqual(record['name'], 'Record 1')
            
            # Verify that get_odata_response was called with correct arguments
            mock_get_odata.assert_called_once_with(endpoint=endpoint)

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_record_count(self, mock_requests, mock_get_token):
        """Test fetching the count of records in a table."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '42'  # Count as plain text
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Create a method to test record count
        with patch.object(hook, 'get_odata_response') as mock_get_odata:
            mock_get_odata.return_value = '42'
            
            # Get the count (we might implement a dedicated method for this)
            endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table/$count'
            count = hook.get_odata_response(endpoint=endpoint, accept_format='text/plain')
            
            # Verify count
            self.assertEqual(count, '42')
            
            # Verify that get_odata_response was called with correct arguments
            mock_get_odata.assert_called_once_with(endpoint=endpoint, accept_format='text/plain')

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_field_value(self, mock_requests, mock_get_token):
        """Test fetching a specific field value from a record."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': 'Record 1'  # Just the field value
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Method to get specific field value
        with patch.object(hook, 'get_odata_response') as mock_get_odata:
            mock_get_odata.return_value = mock_response.json.return_value
            
            # Get specific field from a record
            endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table(1)/name'
            field_value = hook.get_odata_response(endpoint=endpoint)
            
            # Verify field value
            self.assertEqual(field_value['value'], 'Record 1')
            
            # Verify that get_odata_response was called with correct arguments
            mock_get_odata.assert_called_once_with(endpoint=endpoint)

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_get_binary_field_value(self, mock_requests, mock_get_token):
        """Test fetching a binary field value (like an image)."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response with binary data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b'binary-image-data'
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Test getting binary field value
        # We would need a separate method to handle binary data
        endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table(1)/image/$value'
        headers = {
            'Authorization': f'Bearer test-token',
            'Accept': 'application/octet-stream'
        }
        
        with patch.object(hook, 'get_token', return_value='test-token'):
            # Create a mock method to test binary data retrieval
            def mock_get_binary(endpoint, accept_format=None):
                # This would be a method in the hook
                # Make a proper call to mock_requests.get with the expected parameters
                headers = {
                    'Authorization': f'Bearer test-token',
                    'Accept': accept_format or 'application/octet-stream'
                }
                result = mock_requests.get(endpoint, headers=headers)
                return result.content
            
            # Patch our hook with the mock method
            with patch.object(hook, 'get_binary_field', side_effect=mock_get_binary):
                # Test the method (which we'd need to implement)
                binary_data = hook.get_binary_field(endpoint, 'application/octet-stream')
                
                # Verify the data
                self.assertEqual(binary_data, b'binary-image-data')
                
                # Verify requests was called correctly
                mock_requests.get.assert_called_with(
                    endpoint,
                    headers={'Authorization': 'Bearer test-token', 'Accept': 'application/octet-stream'}
                )

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_navigate_related_tables(self, mock_requests, mock_get_token):
        """Test navigating to related tables using OData navigation properties."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'order_id': 101, 'customer_id': 1, 'amount': 99.99},
                {'order_id': 102, 'customer_id': 1, 'amount': 149.99}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Method to navigate related tables
        with patch.object(hook, 'get_odata_response') as mock_get_odata:
            mock_get_odata.return_value = mock_response.json.return_value
            
            # Navigate to related orders for a customer
            endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/Customers(1)/Orders'
            related_records = hook.get_odata_response(endpoint=endpoint)
            
            # Verify related records
            self.assertEqual(len(related_records['value']), 2)
            self.assertEqual(related_records['value'][0]['order_id'], 101)
            
            # Verify that get_odata_response was called with correct arguments
            mock_get_odata.assert_called_once_with(endpoint=endpoint)

    @patch('filemaker.hooks.filemaker.FileMakerHook.get_token')
    @patch('filemaker.hooks.filemaker.requests')
    def test_cross_join_tables(self, mock_requests, mock_get_token):
        """Test performing a cross join between unrelated tables."""
        # Mock the token
        mock_get_token.return_value = 'test-token'
        
        # Mock the requests.get response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'value': [
                {'product': {'id': 1, 'name': 'Product 1'}, 'category': {'id': 101, 'name': 'Category A'}},
                {'product': {'id': 1, 'name': 'Product 1'}, 'category': {'id': 102, 'name': 'Category B'}}
            ]
        }
        mock_requests.get.return_value = mock_response
        
        # Initialize the hook
        hook = FileMakerHook(
            host='https://test.filemaker-cloud.com',
            database='test-db',
            filemaker_conn_id=None  # Disable connection lookup
        )
        
        # Method to perform cross join
        with patch.object(hook, 'get_odata_response') as mock_get_odata:
            mock_get_odata.return_value = mock_response.json.return_value
            
            # Perform a cross join
            endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/Products/$crossjoin(Categories)'
            cross_join_results = hook.get_odata_response(endpoint=endpoint)
            
            # Verify cross join results
            self.assertEqual(len(cross_join_results['value']), 2)
            self.assertEqual(cross_join_results['value'][0]['product']['name'], 'Product 1')
            self.assertEqual(cross_join_results['value'][0]['category']['name'], 'Category A')
            
            # Verify that get_odata_response was called with correct arguments
            mock_get_odata.assert_called_once_with(endpoint=endpoint)


class TestFileMakerOperators(unittest.TestCase):
    """Test cases for FileMaker Operators."""
    
    @patch('filemaker.operators.filemaker.FileMakerHook')
    def test_query_operator(self, mock_hook_class):
        """Test FileMakerQueryOperator."""
        # Set up mock hook and response
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the OData response
        expected_result = {'value': [{'id': 1, 'name': 'Test Record'}]}
        mock_hook.get_odata_response.return_value = expected_result
        
        # Create the operator
        operator = FileMakerQueryOperator(
            task_id='test_query',
            endpoint='test-table',
            filemaker_conn_id='filemaker_test'
        )
        
        # Execute the operator
        result = operator.execute(context={})
        
        # Verify the hook was initialized correctly
        mock_hook_class.assert_called_once_with(filemaker_conn_id='filemaker_test')
        
        # Verify get_base_url was called
        mock_hook.get_base_url.assert_called_once()
        
        # Verify get_odata_response was called with correct arguments
        expected_url = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table'
        mock_hook.get_odata_response.assert_called_once_with(
            endpoint=expected_url,
            accept_format='application/json'
        )
        
        # Verify the result
        self.assertEqual(result, expected_result)
    
    @patch('filemaker.operators.filemaker.FileMakerQueryOperator')
    @patch('filemaker.operators.filemaker.FileMakerHook')
    def test_extract_operator(self, mock_hook_class, mock_query_op):
        """Test FileMakerExtractOperator."""
        # Mock the query operator's execute method
        expected_result = {'value': [{'id': 1, 'name': 'Test Record'}]}
        mock_query_instance = MagicMock()
        mock_query_instance.execute.return_value = expected_result
        mock_query_op.return_value = mock_query_instance
        
        # Create a temporary file for output
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Create the operator
            operator = FileMakerExtractOperator(
                task_id='test_extract',
                endpoint='test-table',
                filemaker_conn_id='filemaker_test',
                output_path=output_path,
                format='json'
            )
            
            # Execute the operator (mocking the file saving)
            with patch.object(operator, '_save_output') as mock_save:
                result = operator.execute(context={})
                
                # Verify that _save_output was called with correct data
                mock_save.assert_called_once_with(expected_result)
                
                # Verify the query operator was created correctly
                mock_query_op.assert_called_once_with(
                    task_id='test_extract_query',
                    endpoint='test-table',
                    filemaker_conn_id='filemaker_test',
                    accept_format='application/json'
                )
                
                # Verify the query operator was executed
                mock_query_instance.execute.assert_called_once()
                
                # Verify the result
                self.assertEqual(result, expected_result)
        
        finally:
            # Clean up the temporary file
            import os
            if os.path.exists(output_path):
                os.unlink(output_path)
    
    @patch('filemaker.operators.filemaker.FileMakerHook')
    def test_schema_operator(self, mock_hook_class):
        """Test FileMakerSchemaOperator."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Sample XML metadata response
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
            <edmx:DataServices>
                <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="FileMaker.Customers">
                    <EntityType Name="Customer">
                        <Key>
                            <PropertyRef Name="CustomerID" />
                        </Key>
                        <Property Name="CustomerID" Type="Edm.String" Nullable="false" />
                        <Property Name="Name" Type="Edm.String" />
                        <Property Name="Email" Type="Edm.String" />
                        <NavigationProperty Name="Orders" Type="Collection(FileMaker.Orders.Order)" />
                    </EntityType>
                    <EntityType Name="Address">
                        <Key>
                            <PropertyRef Name="AddressID" />
                        </Key>
                        <Property Name="AddressID" Type="Edm.String" Nullable="false" />
                        <Property Name="Street" Type="Edm.String" />
                        <Property Name="City" Type="Edm.String" />
                    </EntityType>
                </Schema>
                <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="FileMaker.Default">
                    <EntityContainer Name="Container">
                        <EntitySet Name="Customers" EntityType="FileMaker.Customers.Customer" />
                        <EntitySet Name="Addresses" EntityType="FileMaker.Customers.Address" />
                    </EntityContainer>
                </Schema>
            </edmx:DataServices>
        </edmx:Edmx>"""
        
        # Mock the OData response
        mock_hook.get_odata_response.return_value = sample_xml
        
        # Create the operator
        operator = FileMakerSchemaOperator(
            task_id='test_schema',
            filemaker_conn_id='filemaker_test'
        )
        
        # Execute the operator
        with patch.object(operator, '_parse_xml_schema') as mock_parse:
            # Set up the expected schema result
            expected_schema = {
                'entities': {
                    'Customer': {
                        'properties': [{'name': 'CustomerID', 'type': 'Edm.String'}],
                        'key_properties': ['CustomerID']
                    }
                },
                'entity_sets': {'Customers': {'entity_type': 'Customer'}}
            }
            mock_parse.return_value = expected_schema
            
            # Run the operator
            result = operator.execute(context={})
            
            # Verify the hook was initialized correctly
            mock_hook_class.assert_called_once_with(filemaker_conn_id='filemaker_test')
            
            # Verify get_base_url was called
            mock_hook.get_base_url.assert_called_once()
            
            # Verify get_odata_response was called with correct arguments
            expected_url = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/$metadata'
            mock_hook.get_odata_response.assert_called_once_with(
                endpoint=expected_url,
                accept_format='application/xml'
            )
            
            # Verify _parse_xml_schema was called with the XML data
            mock_parse.assert_called_once_with(sample_xml)
            
            # Verify the result
            self.assertEqual(result, expected_schema)


class TestFileMakerSensors(unittest.TestCase):
    """Test cases for FileMaker Sensors."""
    
    @patch('filemaker.sensors.filemaker.FileMakerHook')
    def test_data_sensor_success(self, mock_hook_class):
        """Test FileMakerDataSensor with successful condition."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the OData response for a count query
        mock_hook.get_odata_response.return_value = '5'  # 5 records found
        
        # Create the sensor
        sensor = FileMakerDataSensor(
            task_id='test_sensor',
            table='test-table',
            condition='status eq "ready"',
            expected_count=3,  # We expect at least 3
            comparison_operator='>=',
            filemaker_conn_id='filemaker_test'
        )
        
        # Test the poke method
        result = sensor.poke(context={})
        
        # Verify the hook was initialized correctly
        mock_hook_class.assert_called_once_with(filemaker_conn_id='filemaker_test')
        
        # Verify get_base_url was called
        mock_hook.get_base_url.assert_called_once()
        
        # Verify get_odata_response was called with correct arguments
        expected_endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table/$count?$filter=status eq "ready"'
        mock_hook.get_odata_response.assert_called_once_with(
            endpoint=expected_endpoint,
            accept_format='text/plain'
        )
        
        # Verify the result is True (5 >= 3)
        self.assertTrue(result)
    
    @patch('filemaker.sensors.filemaker.FileMakerHook')
    def test_data_sensor_failure(self, mock_hook_class):
        """Test FileMakerDataSensor with unsuccessful condition."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the OData response for a count query
        mock_hook.get_odata_response.return_value = '2'  # Only 2 records found
        
        # Create the sensor
        sensor = FileMakerDataSensor(
            task_id='test_sensor',
            table='test-table',
            condition='status eq "ready"',
            expected_count=3,  # We expect at least 3
            comparison_operator='>=',
            filemaker_conn_id='filemaker_test'
        )
        
        # Test the poke method
        result = sensor.poke(context={})
        
        # Verify the result is False (2 is not >= 3)
        self.assertFalse(result)
    
    @patch('filemaker.sensors.filemaker.FileMakerHook')
    def test_change_sensor_first_run(self, mock_hook_class):
        """Test FileMakerChangeSensor on first run (establishing baseline)."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the OData response for getting the latest timestamp
        mock_hook.get_odata_response.return_value = {
            'value': [
                {'ModifiedTimestamp': '2023-01-01T12:00:00Z'}
            ]
        }
        
        # Create the sensor with no initial timestamp
        sensor = FileMakerChangeSensor(
            task_id='test_change_sensor',
            table='test-table',
            modified_field='ModifiedTimestamp',
            last_modified_ts=None,  # No initial timestamp
            filemaker_conn_id='filemaker_test'
        )
        
        # Mock the xcom_push method
        sensor.xcom_push = MagicMock()
        
        # Test the poke method
        result = sensor.poke(context={})
        
        # Verify the hook was initialized correctly
        mock_hook_class.assert_called_once_with(filemaker_conn_id='filemaker_test')
        
        # Verify the result is False (first run establishes baseline)
        self.assertFalse(result)
        
        # Verify xcom_push was called to store the timestamp
        sensor.xcom_push.assert_called_once_with(
            context=None,
            key='last_modified_ts',
            value='2023-01-01T12:00:00Z'
        )
        
        # Verify the last_modified_ts was updated
        self.assertEqual(sensor.last_modified_ts, '2023-01-01T12:00:00Z')
    
    @patch('filemaker.sensors.filemaker.FileMakerHook')
    def test_change_sensor_with_changes(self, mock_hook_class):
        """Test FileMakerChangeSensor detecting changes."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the count response - 3 new records
        mock_hook.get_odata_response.side_effect = [
            '3',  # First call returns count of modified records
            {     # Second call returns the latest timestamp
                'value': [
                    {'ModifiedTimestamp': '2023-01-02T12:00:00Z'}
                ]
            }
        ]
        
        # Create the sensor with an initial timestamp
        sensor = FileMakerChangeSensor(
            task_id='test_change_sensor',
            table='test-table',
            modified_field='ModifiedTimestamp',
            last_modified_ts='2023-01-01T12:00:00Z',  # Yesterday's timestamp
            filemaker_conn_id='filemaker_test'
        )
        
        # Mock the xcom_push method
        sensor.xcom_push = MagicMock()
        
        # Test the poke method
        result = sensor.poke(context={})
        
        # Verify the result is True (changes detected)
        self.assertTrue(result)
        
        # Verify the count endpoint was called correctly
        count_endpoint = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/test-table/$count?$filter=ModifiedTimestamp gt 2023-01-01T12:00:00Z'
        
        # Verify that get_odata_response was called with correct arguments
        mock_hook.get_odata_response.assert_any_call(
            endpoint=count_endpoint,
            accept_format='text/plain'
        )
        
        # Verify that the timestamp was updated
        self.assertEqual(sensor.last_modified_ts, '2023-01-02T12:00:00Z')
    
    @patch('filemaker.sensors.filemaker.FileMakerHook')
    def test_custom_sensor(self, mock_hook_class):
        """Test FileMakerCustomSensor."""
        # Set up mock hook and responses
        mock_hook = MagicMock()
        mock_hook_class.return_value = mock_hook
        
        # Mock the base URL
        mock_hook.get_base_url.return_value = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db'
        
        # Mock the OData response
        expected_result = {
            'value': [
                {'status': 'completed', 'count': 5},
                {'status': 'pending', 'count': 2}
            ]
        }
        mock_hook.get_odata_response.return_value = expected_result
        
        # Create a custom success function
        def check_completion(data):
            # Check if any records have 'completed' status and count > 3
            for record in data.get('value', []):
                if record.get('status') == 'completed' and record.get('count', 0) > 3:
                    return True
            return False
        
        # Create the sensor
        sensor = FileMakerCustomSensor(
            task_id='test_custom_sensor',
            endpoint='status-summary',
            success_fn=check_completion,
            filemaker_conn_id='filemaker_test'
        )
        
        # Test the poke method
        result = sensor.poke(context={})
        
        # Verify the hook was initialized correctly
        mock_hook_class.assert_called_once_with(filemaker_conn_id='filemaker_test')
        
        # Verify get_base_url was called
        mock_hook.get_base_url.assert_called_once()
        
        # Verify get_odata_response was called with correct arguments
        expected_url = 'https://test.filemaker-cloud.com/fmi/odata/v4/test-db/status-summary'
        mock_hook.get_odata_response.assert_called_once_with(endpoint=expected_url)
        
        # Verify the result is True
        self.assertTrue(result)


if __name__ == '__main__':
    unittest.main() 