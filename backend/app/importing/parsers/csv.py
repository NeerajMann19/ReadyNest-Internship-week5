"""
CSV dataset parser implementation.
"""
import os
import pandas as pd
from app.exceptions.base import BadRequestException
from app.importing.parsers.base import BaseParser


class CSVParser(BaseParser):
    """
    Ingestion parser for CSV files, handling delimiters, encodings, and integrity checks.
    """
    def parse(self, file_path: str) -> pd.DataFrame:
        if not os.path.exists(file_path):
            raise BadRequestException("Target file path does not exist")
            
        encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]
        delimiters = [",", ";", "\t"]
        
        df = None
        last_error = None
        
        for enc in encodings:
            for delim in delimiters:
                try:
                    df = pd.read_csv(
                        file_path,
                        encoding=enc,
                        sep=delim,
                        low_memory=False
                    )
                    # If it successfully parses with multiple columns, accept it
                    if df is not None and len(df.columns) > 1:
                        break
                except Exception as e:
                    last_error = e
            if df is not None and len(df.columns) > 1:
                break
                
        # Fallback if delimiter auto-detect was too strict (e.g. single column CSV)
        if df is None or len(df.columns) <= 1:
            for enc in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=enc, low_memory=False)
                    break
                except Exception as e:
                    last_error = e
                    
        if df is None:
            raise BadRequestException(f"Failed to parse CSV file: {str(last_error or 'Unknown parsing error')}")
            
        return df

    def validate(self, df: pd.DataFrame) -> None:
        if df.empty:
            raise BadRequestException("Dataset file is empty and contains no records")
            
        # Check for empty or auto-generated unnamed headers
        if any(str(c).strip() == "" or "Unnamed:" in str(c) for c in df.columns):
            raise BadRequestException("Dataset contains invalid, empty, or unnamed column headers")
            
        # Check for duplicate headers
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
