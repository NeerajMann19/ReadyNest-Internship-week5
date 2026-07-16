"""
Exploratory Data Analysis (EDA) service logic.
"""
import os
import math
import time
import pandas as pd
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.common.enums import DatasetStatus
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.eda_result import EdaResult
from app.repositories.eda_result import EdaResultRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.importing.parsers.csv import CSVParser
from app.importing.parsers.excel import ExcelParser


class EdaService:
    """
    Orchestrates Exploratory Data Analysis computations, saving reports and HTML previews.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.eda_repo = EdaResultRepository(session)

    def _sanitize_floats(self, obj: Any) -> Any:
        """Recursively replaces float NaN/Inf with None to guarantee clean JSON serialization."""
        if isinstance(obj, dict):
            return {k: self._sanitize_floats(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._sanitize_floats(x) for x in obj]
        elif isinstance(obj, float):
            if math.isnan(obj) or math.isinf(obj):
                return None
            return obj
        return obj

    def _generate_html_table(self, title: str, headers: List[str], rows: List[List[Any]]) -> str:
        """Compiles clean, responsive frontend-ready styled HTML tables."""
        html = f"<div class='overflow-x-auto my-4 rounded-lg border border-slate-200 dark:border-slate-800 shadow-sm'>\n"
        html += f"  <h4 class='text-sm font-semibold text-slate-800 dark:text-slate-200 p-3 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800'>{title}</h4>\n"
        html += f"  <table class='min-w-full divide-y divide-slate-200 dark:divide-slate-800 text-left text-xs'>\n"
        html += f"    <thead class='bg-slate-100 dark:bg-slate-900 text-slate-700 dark:text-slate-300 font-medium'>\n"
        html += f"      <tr>\n"
        for h in headers:
            html += f"        <th class='px-4 py-3'>{h}</th>\n"
        html += f"      </tr>\n"
        html += f"    </thead>\n"
        html += f"    <tbody class='divide-y divide-slate-200 dark:divide-slate-800 bg-white dark:bg-slate-950 text-slate-800 dark:text-slate-200'>\n"
        
        for r in rows:
            html += f"      <tr class='hover:bg-slate-50 dark:hover:bg-slate-900/50 transition-colors'>\n"
            for cell in r:
                cell_val = "" if cell is None else str(cell)
                html += f"        <td class='px-4 py-2.5 whitespace-nowrap'>{cell_val}</td>\n"
            html += f"      </tr>\n"
            
        html += f"    </tbody>\n"
        html += f"  </table>\n"
        html += f"</div>"
        return html

    async def run_eda(self, dataset_id: UUID, user_id: UUID) -> EdaResult:
        """
        Loads the active version, computes in-depth descriptive statistics (with 100k sampling for scaling),
        builds clean HTML table logs, and saves results in PostgreSQL.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version to analyze")

        local_path = version.storage_path.replace("local://", "", 1)
        ext = os.path.splitext(version.storage_path)[1].lower()

        parser = CSVParser() if ext == ".csv" else ExcelParser()
        try:
            df = parser.parse(local_path)
        except Exception as e:
            raise BadRequestException(f"Failed to read file for EDA: {str(e)}")

        start_time = time.perf_counter()

        # Handle Large Dataset Sampling (100k limit)
        is_sampled = len(df) > settings.EDA_MAX_SAMPLE_ROWS
        if is_sampled:
            df_sample = df.sample(settings.EDA_MAX_SAMPLE_ROWS, random_state=42)
        else:
            df_sample = df

        # --- 1. OVERVIEW ANALYSIS ---
        rows_count = len(df)
        cols_count = len(df.columns)
        total_cells = len(df_sample) * cols_count
        missing_cells = int(df_sample.isna().sum().sum())
        duplicate_rows = int(df_sample.duplicated().sum())
        memory_usage_bytes = int(df.memory_usage(deep=True).sum())
        
        # Quality score
        quality_score = 100.0
        if total_cells > 0:
            missing_ratio = missing_cells / total_cells
            quality_score -= missing_ratio * settings.QUALITY_MISSING_WEIGHT
        if len(df_sample) > 0:
            duplicate_ratio = duplicate_rows / len(df_sample)
            quality_score -= duplicate_ratio * settings.QUALITY_DUPLICATE_WEIGHT
        quality_score = max(0.0, min(100.0, float(quality_score)))

        summary_json = {
            "rows_count": rows_count,
            "columns_count": cols_count,
            "memory_usage_bytes": memory_usage_bytes,
            "missing_cells": missing_cells,
            "duplicate_rows": duplicate_rows,
            "quality_score": quality_score,
            "is_sampled": is_sampled,
            "sample_rows_count": len(df_sample)
        }

        # --- 2. STATISTICS & TYPE-SPECIFIC ANALYSIS ---
        numeric_analysis = {}
        categorical_analysis = {}
        datetime_analysis = {}
        distributions = {}
        outliers = {}

        # Placeholders for future feature additions
        summary_json["placeholders"] = {
            "feature_importance": None,
            "association_rules": None,
            "time_series_forecast": None,
            "geospatial_bounds": None,
            "text_linguistics": None
        }

        # Classify columns by dtype
        numeric_cols = []
        categorical_cols = []
        datetime_cols = []

        for col in df_sample.columns:
            series = df_sample[col]
            if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
                numeric_cols.append(col)
            elif pd.api.types.is_datetime64_any_dtype(series):
                datetime_cols.append(col)
            else:
                # Try datetimes parsing check
                try:
                    sample_non_nulls = series.dropna().head(10)
                    if not sample_non_nulls.empty:
                        pd.to_datetime(sample_non_nulls)
                        datetime_cols.append(col)
                        continue
                except Exception:
                    pass
                categorical_cols.append(col)

        # A. Numeric Column Stats
        numeric_rows_html = []
        for col in numeric_cols:
            col_series = df_sample[col].dropna()
            if col_series.empty:
                continue
            
            mean_val = float(col_series.mean())
            med_val = float(col_series.median())
            mode_series = col_series.mode()
            mode_val = float(mode_series[0]) if not mode_series.empty else None
            std_val = float(col_series.std())
            var_val = float(col_series.var())
            min_val = float(col_series.min())
            max_val = float(col_series.max())
            q1 = float(col_series.quantile(0.25))
            q2 = float(col_series.quantile(0.50))
            q3 = float(col_series.quantile(0.75))
            iqr_val = q3 - q1
            skew_val = float(col_series.skew())
            kurt_val = float(col_series.kurt())

            numeric_analysis[col] = {
                "mean": mean_val,
                "median": med_val,
                "mode": mode_val,
                "std": std_val,
                "variance": var_val,
                "min": min_val,
                "max": max_val,
                "quartiles": {"25%": q1, "50%": q2, "75%": q3},
                "iqr": iqr_val,
                "skewness": skew_val,
                "kurtosis": kurt_val
            }

            numeric_rows_html.append([
                col,
                f"{mean_val:.2f}" if mean_val is not None else "",
                f"{med_val:.2f}" if med_val is not None else "",
                f"{std_val:.2f}" if std_val is not None else "",
                f"{skew_val:.2f}" if skew_val is not None else "",
                f"{kurt_val:.2f}" if kurt_val is not None else "",
                f"{min_val:.2f}" if min_val is not None else "",
                f"{max_val:.2f}" if max_val is not None else ""
            ])

            # Numeric Distributions
            counts, bin_edges = np.histogram(col_series, bins=settings.EDA_HISTOGRAM_BINS)
            distributions[col] = {
                "type": "numeric",
                "counts": [int(c) for c in counts],
                "bin_edges": [float(b) for b in bin_edges]
            }

            # Outlier Detection (IQR Method)
            lower_bound = q1 - 1.5 * iqr_val
            upper_bound = q3 + 1.5 * iqr_val
            outlier_mask = (col_series < lower_bound) | (col_series > upper_bound)
            outlier_count = int(outlier_mask.sum())
            outliers[col] = {
                "outlier_count": outlier_count,
                "outlier_percentage": float((outlier_count / len(col_series)) * 100.0) if len(col_series) > 0 else 0.0,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound
            }

        # B. Categorical Stats
        categorical_rows_html = []
        for col in categorical_cols:
            col_series = df_sample[col].dropna()
            unique_count = int(col_series.nunique())
            cardinality = float(unique_count / len(df_sample)) if len(df_sample) > 0 else 0.0
            
            value_counts = col_series.value_counts().head(20)
            frequencies = {str(k): int(v) for k, v in value_counts.items()}
            top_val = str(value_counts.index[0]) if not value_counts.empty else None

            categorical_analysis[col] = {
                "unique_count": unique_count,
                "cardinality_ratio": cardinality,
                "top_value": top_val
            }

            categorical_rows_html.append([
                col,
                unique_count,
                f"{cardinality:.4f}",
                top_val if top_val else ""
            ])

            distributions[col] = {
                "type": "categorical",
                "frequencies": frequencies
            }

        # C. Datetime Stats
        datetime_rows_html = []
        for col in datetime_cols:
            col_series = pd.to_datetime(df_sample[col], errors='coerce').dropna()
            if col_series.empty:
                continue
            
            min_date = col_series.min()
            max_date = col_series.max()
            span = (max_date - min_date).days

            datetime_analysis[col] = {
                "earliest_date": min_date.isoformat(),
                "latest_date": max_date.isoformat(),
                "span_days": float(span)
            }

            datetime_rows_html.append([
                col,
                min_date.isoformat(),
                max_date.isoformat(),
                span
            ])

        # --- 3. CORRELATION ANALYSIS (PEARSON) ---
        correlation_list = []
        if len(numeric_cols) > 1:
            corr_matrix = df_sample[numeric_cols].corr(method="pearson")
            # Flatten correlation matrix and filter threshold
            for i in range(len(numeric_cols)):
                for j in range(i + 1, len(numeric_cols)):
                    col1 = numeric_cols[i]
                    col2 = numeric_cols[j]
                    coeff = float(corr_matrix.loc[col1, col2])
                    if not pd.isna(coeff) and abs(coeff) >= settings.EDA_CORRELATION_THRESHOLD:
                        correlation_list.append({
                            "column1": col1,
                            "column2": col2,
                            "coefficient": coeff
                        })

        # --- 4. MISSING VALUES ANALYSIS ---
        col_missing = df_sample.isna().sum().to_dict()
        col_missing_pct = (df_sample.isna().sum() / len(df_sample) * 100.0).to_dict()
        
        missing_rows_html = []
        for col in df_sample.columns:
            missing_rows_html.append([
                col,
                int(col_missing[col]),
                f"{col_missing_pct[col]:.2f}%"
            ])

        # Row-wise missing counts distribution
        row_nulls = df_sample.isna().sum(axis=1)
        row_missing_dist = {int(k): int(v) for k, v in row_nulls.value_counts().items()}

        missing_analysis = {
            "column_wise": {
                col: {"count": int(col_missing[col]), "percentage": float(col_missing_pct[col])}
                for col in df_sample.columns
            },
            "row_wise_distribution": row_missing_dist
        }

        # Combine into categorized targets
        statistics_json = {
            "numeric_analysis": numeric_analysis,
            "categorical_analysis": categorical_analysis,
            "datetime_analysis": datetime_analysis
        }

        charts_json = {
            "distributions": distributions,
            "correlations": correlation_list,
            "missing_analysis": missing_analysis,
            "outliers": outliers
        }

        # --- 5. HTML PREVIEW TABULATION GENERATION ---
        html_reports_json = {
            "numeric_table_html": self._generate_html_table(
                "Descriptive Numeric Statistics",
                ["Column Name", "Mean", "Median", "Std Dev", "Skewness", "Kurtosis", "Min", "Max"],
                numeric_rows_html
            ) if numeric_rows_html else "",
            
            "categorical_table_html": self._generate_html_table(
                "Categorical Unique Cardinalities",
                ["Column Name", "Unique Count", "Cardinality Ratio", "Top Value"],
                categorical_rows_html
            ) if categorical_rows_html else "",
            
            "datetime_table_html": self._generate_html_table(
                "Datetime Ranges & Spans",
                ["Column Name", "Earliest Date", "Latest Date", "Span (Days)"],
                datetime_rows_html
            ) if datetime_rows_html else "",
            
            "missing_table_html": self._generate_html_table(
                "Missing Values Summary",
                ["Column Name", "Missing Counts", "Missing Percentage"],
                missing_rows_html
            )
        }

        # Sanitize everything to prevent JSON encoding crashes
        summary_json = self._sanitize_floats(summary_json)
        statistics_json = self._sanitize_floats(statistics_json)
        charts_json = self._sanitize_floats(charts_json)

        # Clear existing EDA results for this version to handle rerun overwrite logic
        existing_eda = await self.eda_repo.get_by_version_id(version.id)
        if existing_eda:
            await self.eda_repo.delete(existing_eda.id)

        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000.0)

        # Save fresh analysis report
        eda = EdaResult(
            id=uuid4(),
            dataset_id=dataset_id,
            dataset_version_id=version.id,
            summary_json=summary_json,
            statistics_json=statistics_json,
            charts_json=charts_json,
            html_reports_json=html_reports_json,
            execution_time_ms=execution_time_ms,
            engine_version="1.0",
            pandas_version=str(pd.__version__)
        )
        await self.eda_repo.create(eda)

        # Update dataset version status to ANALYZED
        await self.version_repo.update(version, {"status": DatasetStatus.ANALYZED})
        
        await self.session.flush()

        return eda

    async def get_eda(self, dataset_id: UUID, user_id: UUID) -> EdaResult:
        """
        Fetches stored exploratory analysis results matching the active dataset version.
        """
        dataset = await self.dataset_repo.get(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        version = await self.version_repo.get_current_version(dataset_id)
        if not version:
            raise BadRequestException("Dataset contains no active version")

        eda = await self.eda_repo.get_by_version_id(version.id)
        if not eda:
            raise NotFoundException("No EDA analysis has been run yet for the active version")
            
        return eda
