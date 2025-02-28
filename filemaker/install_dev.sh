#!/bin/bash
set -e

# Color codes for terminal output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Installing dependencies for FileMaker provider testing...${NC}"



# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source /Users/josh/Projects/airflow-dev/.venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Install the FileMaker provider in development mode
echo -e "${YELLOW}Installing FileMaker provider in development mode...${NC}"
pip install -e .

# Verify installation of direct dependencies
echo -e "${YELLOW}Verifying installation...${NC}"
pip list | grep -E "boto3|requests|pandas|pytest"

echo -e "${GREEN}Installation completed!${NC}"
echo -e "${GREEN}To run tests: source venv/bin/activate && python test_filemaker.py${NC}" 