FROM apache/airflow:2.10.5

LABEL maintainer="Joshua Lipton <josh@arktci.com>"
LABEL description="Apache Airflow with FileMaker Provider pre-installed"

# Install the FileMaker provider package
RUN pip install --no-cache-dir "apache-airflow==2.10.5" arktci-airflow-provider-filemaker

# Verify the installation
RUN python -c "import airflow.providers.filemaker; print('FileMaker Provider installed successfully')"
