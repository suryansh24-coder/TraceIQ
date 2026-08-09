from enum import Enum
from typing import Dict, Any, Optional
from pydantic import BaseModel

class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ConfidenceLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class BaseTraceIQModel(BaseModel):
    class Config:
        populate_by_name = True
        extra = "ignore"
