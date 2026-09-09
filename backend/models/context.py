"""
Service context model — frozen §3.8. Manual assignment mechanism (no UI/DB
entry yet; context is assigned via explicit ServiceContext instances in code
or a config file for this phase).
"""
from enum import Enum
from pydantic import BaseModel


class Criticality(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Exposure(str, Enum):
    INTERNAL_ONLY = "INTERNAL_ONLY"
    INTERNAL_NETWORK = "INTERNAL_NETWORK"
    INTERNET_FACING = "INTERNET_FACING"


class DataSensitivity(str, Enum):
    NONE = "NONE"
    INTERNAL = "INTERNAL"
    SENSITIVE_PII = "SENSITIVE_PII"
    SENSITIVE_CREDENTIALS = "SENSITIVE_CREDENTIALS"


# Frozen point tables — §3.8. Do not modify without MEMOIRE UPDATE REQUIRED.
CRITICALITY_POINTS = {
    Criticality.LOW: 0, Criticality.MEDIUM: 1,
    Criticality.HIGH: 2, Criticality.CRITICAL: 3,
}
EXPOSURE_POINTS = {
    Exposure.INTERNAL_ONLY: 0, Exposure.INTERNAL_NETWORK: 1,
    Exposure.INTERNET_FACING: 2,
}
DATA_SENSITIVITY_POINTS = {
    DataSensitivity.NONE: 0, DataSensitivity.INTERNAL: 1,
    DataSensitivity.SENSITIVE_PII: 2, DataSensitivity.SENSITIVE_CREDENTIALS: 3,
}


class ServiceContext(BaseModel):
    service: str
    criticality: Criticality
    exposure: Exposure
    data_sensitivity: DataSensitivity
