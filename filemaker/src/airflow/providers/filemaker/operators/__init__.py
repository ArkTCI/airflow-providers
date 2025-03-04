"""
FileMaker operators for Apache Airflow.
"""

from airflow.providers.filemaker.operators.filemaker import (
    FileMakerBulkCreateOperator,
    FileMakerCreateRecordOperator,
    FileMakerDeleteRecordOperator,
    FileMakerExecuteFunctionOperator,
    FileMakerExtractOperator,
    FileMakerQueryOperator,
    FileMakerSchemaOperator,
    FileMakerToS3Operator,
    FileMakerUpdateRecordOperator,
)

__all__ = [
    "FileMakerQueryOperator",
    "FileMakerExtractOperator",
    "FileMakerSchemaOperator",
    "FileMakerCreateRecordOperator",
    "FileMakerUpdateRecordOperator",
    "FileMakerDeleteRecordOperator",
    "FileMakerBulkCreateOperator",
    "FileMakerExecuteFunctionOperator",
    "FileMakerToS3Operator",
]
