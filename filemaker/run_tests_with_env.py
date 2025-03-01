#!/usr/bin/env python
"""
Test runner script for VS Code that loads environment variables from .env
"""
import os
import sys
import subprocess
from pathlib import Path
import pytest

# Find the .env file in the current directory
ENV_FILE = Path(__file__).parent / '.env'

def load_dotenv(env_file):
    """Load environment variables from .env file"""
    print(f"Loading environment from {env_file}")
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value
                    # Don't print password
                    if 'PASSWORD' not in key:
                        print(f"Set {key}={value}")
                    else:
                        print(f"Set {key}=********")
    except Exception as e:
        print(f"Error loading .env file: {e}")

def run_tests():
    """Run the integration tests with pytest"""
    # First make sure PYTHONPATH includes the src directory
    script_dir = Path(__file__).parent
    src_dir = script_dir / 'src'
    if 'PYTHONPATH' not in os.environ:
        os.environ['PYTHONPATH'] = str(src_dir)
    else:
        os.environ['PYTHONPATH'] = f"{str(src_dir)}:{os.environ['PYTHONPATH']}"
    
    print("\nAuthentication information:")
    print("===========================")
    print("Tests use AWS Cognito authentication with fixed pool credentials:")
    print("  - UserPoolId: us-west-2_NqkuZcXQY")
    print("  - ClientId: 4l9rvl4mv5es1eep1qe97cautn")
    print("  - Authorization Header: 'FMID {token}'")
    print("===========================\n")
    
    print("Running integration tests with these credentials:")
    print(f"  - Host: {os.environ.get('FILEMAKER_HOST')}")
    print(f"  - Database: {os.environ.get('FILEMAKER_DATABASE')}")
    print(f"  - Username: {os.environ.get('FILEMAKER_USERNAME')}")
    print(f"  - Password: {'*' * len(os.environ.get('FILEMAKER_PASSWORD', '')) if os.environ.get('FILEMAKER_PASSWORD') else None}")
    print("\n")
    
    # Run with more verbose output to help debugging
    print("Running integration tests...\n")
    return pytest.main(['tests/integration', '-v', '--no-header'])

if __name__ == "__main__":
    if ENV_FILE.exists():
        load_dotenv(ENV_FILE)
        
        # Verify required variables are set
        required_vars = [
            'FILEMAKER_HOST', 
            'FILEMAKER_DATABASE', 
            'FILEMAKER_USERNAME', 
            'FILEMAKER_PASSWORD'
        ]
        
        missing = [var for var in required_vars if not os.environ.get(var)]
        
        if missing:
            print(f"Missing required environment variables: {', '.join(missing)}")
            print("Please update your .env file with these values.")
            sys.exit(1)
        
        # Check if host has https:// protocol
        host = os.environ.get('FILEMAKER_HOST', '')
        if host and not host.startswith(('http://', 'https://')):
            print("WARNING: FILEMAKER_HOST doesn't include a protocol (https://)")
            print(f"Current value: {host}")
            print("This will likely cause authentication issues")
            print("Updating FILEMAKER_HOST to include https:// protocol")
            os.environ['FILEMAKER_HOST'] = f"https://{host}"
            print(f"Updated FILEMAKER_HOST to: {os.environ['FILEMAKER_HOST']}")
        
        exit_code = run_tests()
        sys.exit(exit_code)
    else:
        print(f"No .env file found at {ENV_FILE}")
        print("Please create a .env file with the required credentials.")
        sys.exit(1) 