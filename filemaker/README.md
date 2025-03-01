# FileMaker Cloud Provider for Apache Airflow

This is a custom provider package for Apache Airflow that enables integration with FileMaker Cloud's OData API.

## Features

- **FileMakerHook**: Handles authentication with FileMaker Cloud through AWS Cognito and provides methods to interact with the OData API.
- **FileMakerQueryOperator**: Executes OData queries against FileMaker Cloud.
- **FileMakerExtractOperator**: Extracts data from FileMaker Cloud and saves it in various formats.
- **FileMakerSchemaOperator**: Retrieves and parses the FileMaker Cloud OData metadata schema.
- **FileMakerDataSensor**: Sensor that monitors FileMaker tables for specific conditions.
- **FileMakerChangeSensor**: Sensor that detects changes in FileMaker tables since a timestamp.
- **FileMakerCustomSensor**: Customizable sensor that allows for complex monitoring logic.

## Installation

### Installation from PyPI (Recommended)

```bash
pip install arktci-airflow-provider-filemaker
```

### Provider Structure

This provider follows the official Apache Airflow provider structure:

```
providers/filemaker/
├── pyproject.toml
├── provider.yaml
├── setup.py
├── README.md
├── src/
│   └── airflow/
│       └── providers/filemaker/
│           ├── __init__.py
│           ├── hooks/
│           │   ├── __init__.py
│           │   └── filemaker.py
│           ├── operators/
│           │   ├── __init__.py
│           │   └── filemaker.py
│           ├── sensors/
│           │   ├── __init__.py
│           │   └── filemaker.py
│           └── auth/
│               ├── __init__.py
│               └── cognitoauth.py
└── tests/
    ├── unit/
    │   └── filemaker/
    │       ├── hooks/
    │       │   └── test_filemaker.py
    │       ├── operators/
    │       │   └── test_filemaker.py
    │       ├── sensors/
    │       │   └── test_filemaker.py
    │       └── auth/
    │           └── test_cognitoauth.py
    ├── integration/
    │   └── filemaker/
    │       └── test_integration_filemaker.py
    └── system/
        └── filemaker/
            └── example_filemaker.py
```

### Manual Installation

1. Copy the `providers/filemaker` directory to your Airflow project's `providers` directory.

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install the package:
   ```
   pip install -e .
   ```

4. Create a FileMaker connection in Airflow:
   - Connection ID: `filemaker_default` (or any ID you prefer)
   - Connection Type: `filemaker`
   - Host: Your FileMaker Cloud host (e.g., `my-fmcloud.filemaker-cloud.com`)
   - Schema: Your FileMaker database name
   - Login: Your FileMaker Cloud username (Claris ID)
   - Password: Your FileMaker Cloud password
   - Extra: JSON containing Cognito details (if not using auto-discovery):
     ```json
     {
       "user_pool_id": "your-cognito-user-pool-id",
       "client_id": "your-cognito-client-id",
       "region": "your-aws-region"
     }
     ```

## Development

### Setting Up Development Environment

1. Clone the repository:
   ```bash
   git clone https://github.com/your-org/airflow-dev.git
   cd airflow-dev/providers/filemaker
   ```

2. Install development requirements:
   ```bash
   pip install -r requirements-dev.txt
   ```

3. Set up your credentials for integration tests:
   - Copy `.env.template` to `.env`
   - Fill in your FileMaker Cloud credentials

```bash
cp .env.template .env
# Edit .env with your credentials
```

### Running Tests

#### Unit Tests

Unit tests can be run without FileMaker Cloud credentials:

```bash
pytest tests/unit
```

#### Integration Tests

Integration tests require valid FileMaker Cloud credentials.

**Important Note on Authentication:** The integration tests use AWS Cognito authentication with the `/fmi/odata/login/info` endpoint. If your FileMaker Cloud instance uses a different authentication method or if this endpoint is not accessible, the tests will fail with a 400 Bad Request error. You may need to modify the authentication code to match your FileMaker Cloud version's requirements.

To run integration tests:

1. Ensure your `.env` file is properly configured with:
   - FILEMAKER_HOST (must include https:// protocol)
   - FILEMAKER_DATABASE
   - FILEMAKER_USERNAME
   - FILEMAKER_PASSWORD

2. Run the tests:
```bash
./run_tests.sh
```

Or run specific tests:
```bash
python -m pytest tests/integration -v
```

### Continuous Integration

For CI/CD with GitHub Actions, add the following secrets to your repository:

- FILEMAKER_HOST
- FILEMAKER_DATABASE
- FILEMAKER_USERNAME
- FILEMAKER_PASSWORD

This will allow integration tests to run during the release workflow.

## Troubleshooting

### Integration Test Authentication Failures

If you're seeing authentication errors like `400 Client Error: Bad Request for url: https://your-host/fmi/odata/login/info`, it may indicate:

1. Your FileMaker Cloud instance is using a different authentication endpoint
2. The FileMaker Cloud version has updated its API format
3. Your credentials don't have the necessary permissions

Check your FileMaker Cloud documentation for the correct API endpoint format and authentication requirements.

## License

This provider is licensed under the same license as Apache Airflow.

**Important Note**: If you use placeholder values like "your-filemaker-host.com" in your .env file, the integration tests will attempt to run but will fail with connection errors. This is expected behavior since the placeholders are not valid hosts. You need real FileMaker Cloud credentials for the integration tests to pass.

To run only specific tests, you can use pytest directly:

```bash
# Run only unit tests
python -m pytest tests/unit -v

# Run only integration tests
python -m pytest tests/integration -v

# Run a specific test file
python -m pytest tests/unit/filemaker/hooks/test_filemaker.py -v
```

When running integration tests in a CI/CD environment, you'll need to securely provide credentials:

1. In your GitHub repository, go to Settings > Secrets and add the following secrets:
   - `FILEMAKER_HOST` (include the https:// protocol)
   - `FILEMAKER_DATABASE`
   - `FILEMAKER_USERNAME`
   - `FILEMAKER_PASSWORD`

2. These secrets will be automatically used by the GitHub Actions workflow when running integration tests.

## Authentication Information

### OData Authentication Details

This provider implements authentication using AWS Cognito with the following fixed credentials (same as the JavaScript implementation):

- **User Pool ID**: `us-west-2_NqkuZcXQY`
- **Client ID**: `4l9rvl4mv5es1eep1qe97cautn`

The authentication header format used is:
```
Authorization: FMID <token>
```

This matches the implementation in JavaScript examples like:

```javascript
// JavaScript example
const response = await fetch(baseUrl, {
  headers: {
    'Authorization': `FMID ${fmidToken}`,
    'Accept': 'application/json'
  }
});
```

This authentication implementation:
1. Uses a standard AWS Cognito authentication flow (`USER_PASSWORD_AUTH`)
2. Retrieves an ID token for your FileMaker credentials
3. Uses the ID token with the "FMID" prefix in the Authorization header

### Authentication Troubleshooting

If you're experiencing authentication issues:

1. Ensure your FileMaker host URL includes the protocol (`https://`)
2. Verify your credentials are correct
3. Check network logs to confirm the token is being sent correctly with the `FMID` prefix

The integration tests have been enhanced to provide detailed debugging information to help diagnose authentication issues.

## Integration Tests

The integration tests for this provider require valid FileMaker Cloud credentials. The tests will authenticate with FileMaker Cloud and then run a series of tests to validate the functionality of the provider.

To run the integration tests:

1. Ensure your `.env` file is properly configured with:
   - FILEMAKER_HOST (must include https:// protocol)
   - FILEMAKER_DATABASE
   - FILEMAKER_USERNAME
   - FILEMAKER_PASSWORD

2. Run the tests:
```bash
./run_tests.sh
```

Or run specific tests:
```bash
python -m pytest tests/integration -v
```

When running integration tests in a CI/CD environment, you'll need to securely provide credentials:

1. In your GitHub repository, go to Settings > Secrets and add the following secrets:
   - `FILEMAKER_HOST` (include the https:// protocol)
   - `FILEMAKER_DATABASE`
   - `FILEMAKER_USERNAME`
   - `FILEMAKER_PASSWORD`

2. These secrets will be automatically used by the GitHub Actions workflow when running integration tests. 