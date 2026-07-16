"""
Excel dataset parser implementation.
"""
import os
import pandas as pd
from app.exceptions.base import BadRequestException
from app.importing.parsers.base import BaseParser


class ExcelParser(BaseParser):
    """
    Ingestion parser for Excel files (.xlsx, .xls) using openpyxl engine.
    """
    def parse(self, file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise BadRequestException("Target file path does not exist")
            
        try:
            # Read the first sheet of the Excel workbook
            df = pd.read_excel(file_path, sheet_name=0, engine="openpyxl")
            return df
        except Exception as e:
            raise BadRequestException(f"Failed to parse Excel workbook sheet: {str(e)}")

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise BadRequestException("Excel sheet is empty and contains no records")
            
        if any(str(c).strip() == "" or "Unnamed:" in str(c) for c in df.columns):
            raise BadRequestException("Dataset contains invalid, empty, or unnamed column headers")
            
        headers = [str(c).strip() for c in df.columns]
        if len(headers) != len(set(headers)):
            duplicates = set([h for h in headers if headers.count(h) > 1])
            raise BadRequestException(f"Dataset contains duplicate column headers: {', '.join(duplicates)}")

    def extract_metadata(self, df: pd.DataFrame) -> dict:
        rows_count = len(df)
        columns_count = len(df.columns)
        column_summary = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        memory_usage = int(df.memory_usage(deep=True).sum())
        
        return {
            "rows_count": rows_count,
            "columns_count": columns_count,
            "column_summary": column_summary,
            "memory_usage": memory_usage
        }
