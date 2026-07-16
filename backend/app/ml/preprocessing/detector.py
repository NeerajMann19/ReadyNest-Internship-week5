"""
Target column problem type auto-detector.
"""
import pandas as pd

def detect_problem_type(series: pd.Series) -> str:
    """
    Infers whether a target column requires classification or regression:
    - Numeric values with cardinality > 10 → regression
    - Otherwise → classification
    """
    series_clean = series.dropna()
    if series_clean.empty:
        return "classification"  # Fallback
        
    is_numeric = pd.api.types.is_numeric_dtype(series_clean) and not pd.api.types.is_bool_dtype(series_clean)
    unique_count = series_clean.nunique()
    
    if is_numeric and unique_count > 10:
        return "regression"
    return "classification"
