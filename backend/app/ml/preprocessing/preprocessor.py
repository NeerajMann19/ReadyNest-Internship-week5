"""
Scikit-Learn preprocessor ColumnTransformer configurations.
"""
from typing import List
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

def create_preprocessor(numeric_cols: List[str], categorical_cols: List[str]) -> ColumnTransformer:
    """
    Creates a scikit-learn ColumnTransformer preprocessor pipeline:
    - Numeric columns: Imputed with median, scaled with StandardScaler.
    - Categorical columns: Imputed with most frequent, encoded with OneHotEncoder.
    """
    transformers = []
    
    if numeric_cols:
        transformers.append(
            ('num', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]), numeric_cols)
        )
        
    if categorical_cols:
        transformers.append(
            ('cat', Pipeline(steps=[
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
            ]), categorical_cols)
        )
        
    return ColumnTransformer(transformers=transformers)
