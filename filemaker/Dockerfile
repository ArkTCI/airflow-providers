FROM apache/airflow:2.10.5

LABEL maintainer="Joshua Lipton <josh@arktci.com>"
LABEL description="Apache Airflow with FileMaker Provider pre-installed"

# Install the FileMaker provider package
RUN pip install --no-cache-dir "apache-airflow==2.10.5" arktci-airflow-provider-filemaker

# Verify the installation
RUN python -c "from airflow.providers.filemaker.version import __version__; print(f'FileMaker Provider {__version__} installed successfully')"
