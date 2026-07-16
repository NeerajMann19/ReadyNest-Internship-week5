"""
Data Cleaning orchestrator engine.
"""
import time
import pandas as pd
from typing import List, Tuple, Any

from app.exceptions.base import BadRequestException
from app.cleaning.operations.missing import fill_missing
from app.cleaning.operations.duplicates import drop_duplicates
from app.cleaning.operations.text import clean_text
from app.cleaning.operations.datatype import cast_datatype
from app.cleaning.operations.outliers import remove_outliers


class DataCleaningEngine:
    """
    Coordinates modular cleaning operations and tracks modifications summary.
    """
    @staticmethod
    def validate_operations(df: pd.DataFrame, operations: List[dict]) -> None:
        """
        Validates sequence of cleaning operations for datatype compatibility.
        """
        for op in operations:
            op_type = op.get("type")
            column = op.get("column")
            
            if op_type in ["fill_missing", "cast_type", "clean_text", "remove_outliers"]:
                if not column:
                    raise BadRequestException(f"Operation '{op_type}' requires a target column name.")
                if column not in df.columns:
                    raise BadRequestException(f"Target column '{column}' does not exist in the dataset.")
            
            if op_type == "fill_missing":
                strategy = op.get("strategy")
                if strategy in ["mean", "median"]:
                    # Must be numeric
                    if not pd.api.types.is_numeric_dtype(df[column]):
                        raise BadRequestException(
                            f"Cannot calculate numeric strategy '{strategy}' on non-numeric column '{column}'"
                        )
            
            elif op_type == "clean_text":
                # Text ops are invalid on numeric/bool types
                if pd.api.types.is_numeric_dtype(df[column]) or pd.api.types.is_bool_dtype(df[column]):
                    raise BadRequestException(
                        f"Cannot perform text transformations on numeric/boolean column '{column}'"
                    )
            
            elif op_type == "remove_outliers":
                # Outlier detection requires numeric column
                if not pd.api.types.is_numeric_dtype(df[column]):
                    raise BadRequestException(
                        f"Outlier detection requires numeric data. Column '{column}' is not numeric."
                    )

    def clean_dataframe(self, df: pd.DataFrame, operations: List[dict]) -> Tuple[pd.DataFrame, List[dict], int]:
        """
        Executes cleaning rules sequentially and records per-operation stats and timing.
        """
        self.validate_operations(df, operations)
        
        start_time = time.perf_counter()
        
        # Make a copy to prevent modifying original dataframe context
        cleaned_df = df.copy()
        
        summary = []
        
        for op in operations:
            op_type = op.get("type")
            column = op.get("column", "")
            strategy = op.get("strategy", "")
            target_type = op.get("target_type", "")
            fill_value = op.get("fill_value", None)
            
            affected = 0
            
            if op_type == "drop_duplicates":
                cleaned_df, affected = drop_duplicates(cleaned_df)
                summary_item = {
                    "type": "drop_duplicates",
                    "affected": affected,
                    "parameters": {}
                }
            
            elif op_type == "fill_missing":
                cleaned_df, affected = fill_missing(cleaned_df, column, strategy, fill_value)
                summary_item = {
                    "type": "fill_missing",
                    "column": column,
                    "affected": affected,
                    "parameters": {"strategy": strategy, "fill_value": str(fill_value) if fill_value is not None else None}
                }
                
            elif op_type == "clean_text":
                cleaned_df, affected = clean_text(cleaned_df, column, strategy)
                summary_item = {
                    "type": "clean_text",
                    "column": column,
                    "affected": affected,
                    "parameters": {"strategy": strategy}
                }
                
            elif op_type == "cast_type":
                cleaned_df, affected = cast_datatype(cleaned_df, column, target_type)
                summary_item = {
                    "type": "cast_type",
                    "column": column,
                    "affected": affected,
                    "parameters": {"target_type": target_type}
                }
                
            elif op_type == "remove_outliers":
                cleaned_df, affected = remove_outliers(cleaned_df, column, strategy)
                summary_item = {
                    "type": "remove_outliers",
                    "column": column,
                    "affected": affected,
                    "parameters": {"strategy": strategy}
                }
            else:
                raise BadRequestException(f"Unsupported operation type '{op_type}'")
                
            summary.append(summary_item)
            
        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000.0)
        
        return cleaned_df, summary, execution_time_ms
