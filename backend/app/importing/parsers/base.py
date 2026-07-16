"""
Abstract base class for dataset parsers.
"""
from abc import ABC, abstractmethod
import pandas as pd


class BaseParser(ABC):
    """
    Abstract interface defining methods required for dataset ingestion and parsing.
    """
    @abstractmethod
    def parse(self, file_path: str) -> pd.DataFrame:
        """
        Parses a file from disk into a Pandas DataFrame.
        """
        pass

    @abstractmethod
    def validate(self, df: pd.DataFrame) -> None:
        """
        Validates the parsed DataFrame. Raises exceptions on failure.
        """
        pass

    @abstractmethod
    def extract_metadata(self, df: pd.DataFrame) -> dict:
        """
        Extracts structural metadata (rows, columns count, types, memory usage) from the DataFrame.
        """
        pass
