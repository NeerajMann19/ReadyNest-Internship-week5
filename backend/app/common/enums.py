"""
Application-wide enum structures.
"""
from enum import Enum


class DatasetStatus(str, Enum):
    """
    Tracks the lifecycle state of a dataset.
    """
    UPLOADED = "UPLOADED"
    PROFILED = "PROFILED"
    CLEANED = "CLEANED"
    ANALYZED = "ANALYZED"
    TRAINED = "TRAINED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
