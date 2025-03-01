FROM apache/airflow:2.10.5

LABEL maintainer="Joshua Lipton <liptonj@example.com>"
LABEL description="Apache Airflow with FileMaker Provider pre-installed"

# Simply install the FileMaker provider package
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" apache-airflow-providers-filemaker

# Verify the installation
RUN python -c "from airflow.providers.filemaker.version import __version__; print(f'FileMaker Provider {__version__} installed successfully')"
