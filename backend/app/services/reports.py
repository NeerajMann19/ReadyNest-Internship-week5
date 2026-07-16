"""
Reports and export service logic.
"""
import os
import time
import math
import hashlib
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID, uuid4
from datetime import datetime
import pandas as pd
from sqlalchemy import select

from app.core.config import settings
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.report import Report
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.cleaning_job import CleaningJob
from app.models.data_profile import DataProfile
from app.models.eda_result import EdaResult
from app.models.ai_insight import AiInsight
from app.repositories.report import ReportRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.repositories.data_profile import DataProfileRepository
from app.repositories.cleaning_job import CleaningJobRepository
from app.services.eda import EdaService
from app.services.ai_insights import AiInsightsService

# ReportLab imports for PDF generation
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class ReportsService:
    """
    Coordinates reports exports (PDF, Excel, HTML, JSON) and dataset before-and-after comparisons.
    """
    def __init__(self, session):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.profile_repo = DataProfileRepository(session)
        self.report_repo = ReportRepository(session)
        self.cleaning_job_repo = CleaningJobRepository(session)

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

    def _calculate_checksum(self, filepath: str) -> str:
        """Computes SHA256 checksum of generated report file."""
        sha256 = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _compute_file_stats(self, local_path: str) -> dict:
        """Helper to parse a dataset version file from disk in-memory and return profile metrics."""
        from app.importing.parsers.csv import CSVParser
        from app.importing.parsers.excel import ExcelParser
        
        ext = os.path.splitext(local_path)[1].lower()
        parser = CSVParser() if ext == ".csv" else ExcelParser()
        
        df = parser.parse(local_path)
        rows = len(df)
        cols = len(df.columns)
        missing = int(df.isnull().sum().sum())
        duplicates = int(df.duplicated().sum())
        
        # Calculate quality score
        total_cells = rows * cols
        missing_pct = (missing / total_cells * 100.0) if total_cells > 0 else 0.0
        dup_pct = (duplicates / rows * 100.0) if rows > 0 else 0.0
        quality = 100.0 - (missing_pct * 0.5) - (dup_pct * 0.5)
        quality = max(0.0, min(100.0, quality))
        
        columns_info = {str(col): str(dtype) for col, dtype in df.dtypes.items()}
        
        return {
            "rows_count": rows,
            "columns_count": cols,
            "missing_count": missing,
            "duplicate_count": duplicates,
            "quality_score": quality,
            "columns": columns_info,
            "dataframe": df
        }

    # Generators
    def _generate_json(self, filepath: str, dataset: Dataset, version: DatasetVersion, profile: DataProfile, eda: EdaResult, insights: AiInsight, report_id: UUID, user_id: UUID, ml_model: Optional[Any] = None) -> None:
        """Generates self-contained JSON export representation of the dataset version."""
        import json
        
        export_dict = {
            "metadata": {
                "generated_by": "PrismIQ",
                "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "report_id": str(report_id),
                "user_id": str(user_id),
                "engine_version": "1.0",
                "report_schema_version": "1.0"
            },
            "dataset": {
                "id": str(dataset.id),
                "name": dataset.dataset_name,
                "original_filename": dataset.original_filename,
                "description": dataset.description,
                "created_at": dataset.created_at.isoformat(),
                "active_version": version.version_number,
                "file_size_bytes": version.file_size
            },
            "quality": {
                "quality_score": profile.quality_score,
                "missing_cells": profile.missing_values,
                "duplicate_rows": profile.duplicate_rows
            },
            "profiling": {
                "column_summary": profile.column_summary
            },
            "cleaning": {
                "cleaning_history": [
                    {
                        "source_version_id": str(job.source_version_id),
                        "target_version_id": str(job.target_version_id),
                        "rows_removed": job.rows_removed,
                        "duplicates_removed": job.duplicates_removed,
                        "missing_handled": job.missing_handled,
                        "outliers_handled": job.outliers_handled,
                        "execution_time_ms": job.execution_time_ms,
                        "created_at": job.created_at.isoformat()
                    }
                    for job in dataset.cleaning_jobs
                ]
            },
            "eda": {
                "summary": eda.summary_json if eda else None,
                "statistics": eda.statistics_json if eda else None,
                "charts": eda.charts_json if eda else None
            },
            "insights": {
                "summary": insights.summary_json if insights else None,
                "insights": insights.insights_json if insights else None,
                "prompt_context": insights.prompt_context_json if insights else None
            },
            "dashboard": {
                "kpis": {
                    "quality_score": profile.quality_score,
                    "missing_values": profile.missing_values,
                    "duplicate_rows": profile.duplicate_rows
                }
            },
            "ml_model": {
                "id": str(ml_model.id),
                "model_version": ml_model.model_version,
                "target_column": ml_model.target_column,
                "features": ml_model.features,
                "problem_type": ml_model.problem_type,
                "model_type": ml_model.model_type,
                "best_score": ml_model.best_score,
                "training_rows": ml_model.training_rows,
                "testing_rows": ml_model.testing_rows,
                "duration_ms": ml_model.duration_ms,
                "evaluation_metrics": ml_model.evaluation_metrics,
                "feature_importances": ml_model.feature_importances,
                "training_config": ml_model.training_config,
                "created_at": ml_model.created_at.isoformat()
            } if ml_model else None
        }
        
        export_dict = self._sanitize_floats(export_dict)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_dict, f, indent=2)

    def _generate_excel(self, filepath: str, dataset: Dataset, version: DatasetVersion, profile: DataProfile, eda: EdaResult, insights: AiInsight, local_path: str, report_id: UUID, user_id: UUID, ml_model: Optional[Any] = None) -> None:
        """Generates a rich, multi-sheet Excel report with pandas/openpyxl."""
        # Load Raw Data Top 100 rows
        file_stats = self._compute_file_stats(local_path)
        df_head = file_stats["dataframe"].head(100)

        with pd.ExcelWriter(filepath, engine="openpyxl") as writer:
            # 1. Cover sheet
            cover_data = {
                "Report Parameter": [
                    "Report Title",
                    "Generated By",
                    "Generated At",
                    "Report ID",
                    "User ID",
                    "Dataset ID",
                    "Engine Version",
                    "Report Schema Version"
                ],
                "Value": [
                    "PrismIQ Data Intelligence Report",
                    "PrismIQ",
                    datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                    str(report_id),
                    str(user_id),
                    str(dataset.id),
                    "1.0",
                    "1.0"
                ]
            }
            pd.DataFrame(cover_data).to_excel(writer, sheet_name="Cover", index=False)

            # 2. Dataset Summary sheet
            summary_data = {
                "Metric": [
                    "Dataset Name",
                    "Original Filename",
                    "Active Version",
                    "File Size (Bytes)",
                    "Description",
                    "Created At"
                ],
                "Value": [
                    dataset.dataset_name,
                    dataset.original_filename,
                    f"Version {version.version_number}",
                    version.file_size,
                    dataset.description or "No description",
                    dataset.created_at.isoformat()
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Dataset Summary", index=False)

            # 3. Data Quality sheet
            quality_data = {
                "Metric": [
                    "Quality Score",
                    "Total Rows",
                    "Total Columns",
                    "Total Missing Cells",
                    "Total Duplicate Rows"
                ],
                "Value": [
                    profile.quality_score,
                    file_stats["rows_count"],
                    file_stats["columns_count"],
                    profile.missing_values,
                    profile.duplicate_rows
                ]
            }
            pd.DataFrame(quality_data).to_excel(writer, sheet_name="Data Quality", index=False)

            # 4. Profiling sheet
            profile_list = []
            for col in profile.column_summary:
                profile_list.append({
                    "Column Name": col.get("name"),
                    "Data Type": col.get("dtype"),
                    "Unique Values": col.get("unique_count"),
                    "Missing Values": col.get("missing_count"),
                    "Null %": col.get("missing_pct")
                })
            pd.DataFrame(profile_list).to_excel(writer, sheet_name="Profiling", index=False)

            # 5. Cleaning sheet
            jobs_list = []
            for job in dataset.cleaning_jobs:
                jobs_list.append({
                    "Removed Rows": job.rows_removed,
                    "Removed Duplicates": job.duplicates_removed,
                    "Missing Handled": job.missing_handled,
                    "Outliers Handled": job.outliers_handled,
                    "Time (ms)": job.execution_time_ms,
                    "Applied At": job.created_at.isoformat()
                })
            if not jobs_list:
                jobs_list.append({
                    "Removed Rows": 0,
                    "Removed Duplicates": 0,
                    "Missing Handled": 0,
                    "Outliers Handled": 0,
                    "Time (ms)": 0,
                    "Applied At": "None"
                })
            pd.DataFrame(jobs_list).to_excel(writer, sheet_name="Cleaning", index=False)

            # 6. EDA sheet
            eda_list = []
            if eda and eda.statistics_json:
                num_analysis = eda.statistics_json.get("numeric_analysis", {})
                for col, stats in num_analysis.items():
                    eda_list.append({
                        "Column": col,
                        "Mean": stats.get("mean"),
                        "Median": stats.get("median"),
                        "Min": stats.get("min"),
                        "Max": stats.get("max"),
                        "Std Dev": stats.get("std"),
                        "Skewness": stats.get("skewness"),
                        "Kurtosis": stats.get("kurtosis")
                    })
            if not eda_list:
                eda_list.append({
                    "Column": "None",
                    "Mean": "N/A",
                    "Median": "N/A",
                    "Min": "N/A",
                    "Max": "N/A",
                    "Std Dev": "N/A",
                    "Skewness": "N/A",
                    "Kurtosis": "N/A"
                })
            pd.DataFrame(eda_list).to_excel(writer, sheet_name="EDA", index=False)

            # 7. AI Insights sheet
            ins_list = []
            if insights and insights.insights_json:
                for ins in insights.insights_json:
                    ins_list.append({
                        "Rule ID": ins.get("rule_id"),
                        "Category": ins.get("category"),
                        "Severity": ins.get("severity"),
                        "Confidence": ins.get("confidence"),
                        "Actionability": ins.get("actionability"),
                        "Observation": ins.get("observation"),
                        "Recommendation": ins.get("recommendation")
                    })
            if not ins_list:
                ins_list.append({
                    "Rule ID": "None",
                    "Category": "N/A",
                    "Severity": "N/A",
                    "Confidence": "N/A",
                    "Actionability": "N/A",
                    "Observation": "N/A",
                    "Recommendation": "N/A"
                })
            pd.DataFrame(ins_list).to_excel(writer, sheet_name="AI Insights", index=False)

            # 8. Dashboard KPIs sheet
            kpi_data = {
                "KPI Metric": [
                    "Data Quality Index",
                    "Missing Cell Count",
                    "Duplicate Row Count",
                    "Active Dataset Version",
                    "Raw Records Count",
                    "Cleaning Jobs Executed"
                ],
                "KPI Value": [
                    profile.quality_score,
                    profile.missing_values,
                    profile.duplicate_rows,
                    version.version_number,
                    file_stats["rows_count"],
                    len(dataset.cleaning_jobs)
                ]
            }
            pd.DataFrame(kpi_data).to_excel(writer, sheet_name="Dashboard KPIs", index=False)

            # 9. Raw Statistics sheet
            df_head.to_excel(writer, sheet_name="Raw Statistics", index=False)

            # 10. ML Model Summary sheet
            if ml_model:
                ml_info = {
                    "Model Property": [
                        "Model ID",
                        "Model Version",
                        "Target Column",
                        "Problem Type",
                        "Algorithm/Model Type",
                        "Best Score",
                        "Training Rows",
                        "Testing Rows",
                        "Training Duration (ms)",
                        "File Size (Bytes)",
                        "Training Configuration"
                    ],
                    "Value": [
                        str(ml_model.id),
                        f"Model v{ml_model.model_version}",
                        ml_model.target_column,
                        ml_model.problem_type,
                        ml_model.model_type,
                        ml_model.best_score,
                        ml_model.training_rows,
                        ml_model.testing_rows,
                        ml_model.duration_ms,
                        ml_model.model_size_bytes,
                        str(ml_model.training_config)
                    ]
                }
                pd.DataFrame(ml_info).to_excel(writer, sheet_name="ML Model Summary", index=False)
                
                if ml_model.feature_importances:
                    feat_list = [{"Feature": f, "Importance": imp} for f, imp in ml_model.feature_importances.items()]
                    pd.DataFrame(feat_list).to_excel(writer, sheet_name="ML Feature Importances", index=False)

            # Access Workbook to set footers on each sheet
            workbook = writer.book
            for name in workbook.sheetnames:
                ws = workbook[name]
                ws.oddFooter.left.text = "Generated By: PrismIQ | Engine Version: 1.0 | Report Schema: 1.0"
                ws.oddFooter.center.text = f"Report ID: {report_id}"
                ws.oddFooter.right.text = "Generated At: &D &T"

    def _generate_html(self, filepath: str, dataset: Dataset, version: DatasetVersion, profile: DataProfile, eda: EdaResult, insights: AiInsight, report_id: UUID, user_id: UUID, ml_model: Optional[Any] = None) -> None:
        """Generates a responsive, styled standalone HTML report."""
        import jinja2
        
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>PrismIQ Data Intelligence Report</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body { background-color: #08090B; color: #F3F4F6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
                .report-header { background: linear-gradient(135deg, #111827 0%, #1A1D24 100%); border-left: 5px solid #3B82F6; padding: 30px; border-radius: 12px; margin-bottom: 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.6); }
                .premium-card { background-color: #111827; border: 1px solid #1A1D24; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 4px 10px rgba(0,0,0,0.4); }
                .metric-card { background-color: #1A1D24; border: 1px solid #3B82F633; border-radius: 8px; padding: 18px; text-align: center; }
                .metric-value { font-size: 26px; font-weight: 700; color: #3B82F6; }
                .section-title { font-size: 20px; font-weight: 600; color: #3B82F6; border-bottom: 1px solid #1A1D24; padding-bottom: 8px; margin-bottom: 16px; }
                .table-premium { color: #F3F4F6; }
                .table-premium th { background-color: #1A1D24; color: #3B82F6; border-bottom: 2px solid #3B82F633; }
                .table-premium td { border-bottom: 1px solid #1A1D24; background-color: transparent !important; color: #F3F4F6 !important; }
                .badge-success { background-color: #22C55E; color: white; }
                .badge-warning { background-color: #F59E0B; color: black; }
                .badge-danger { background-color: #EF4444; color: white; }
                .code-block { font-family: 'Courier New', Courier, monospace; color: #06B6D4; }
                .text-muted-custom { color: #9CA3AF; }
                .footer-text { font-size: 12px; color: #6B7280; text-align: center; margin-top: 40px; border-top: 1px solid #1A1D24; padding-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container my-5">
                <!-- Header -->
                <div class="report-header">
                    <div class="d-flex justify-content-between align-items-center flex-wrap">
                        <div>
                            <h1 class="text-white mb-1">PrismIQ Data Intelligence Report</h1>
                            <p class="mb-0 text-muted-custom">Interactive Analytical Export Pipeline Summary</p>
                        </div>
                        <div class="text-end">
                            <span class="badge bg-primary px-3 py-2">Engine v1.0</span>
                        </div>
                    </div>
                </div>

                <!-- Metadata Card -->
                <div class="premium-card">
                    <div class="section-title">Audit Metadata</div>
                    <div class="row g-3">
                        <div class="col-md-6 col-lg-3">
                            <div class="small text-muted-custom">Generated By</div>
                            <div class="fw-semibold">PrismIQ</div>
                        </div>
                        <div class="col-md-6 col-lg-3">
                            <div class="small text-muted-custom">Generated At</div>
                            <div class="fw-semibold">{{ generated_at }}</div>
                        </div>
                        <div class="col-md-6 col-lg-3">
                            <div class="small text-muted-custom">Report ID</div>
                            <div class="fw-semibold small code-block">{{ report_id }}</div>
                        </div>
                        <div class="col-md-6 col-lg-3">
                            <div class="small text-muted-custom">User Session ID</div>
                            <div class="fw-semibold small code-block">{{ user_id }}</div>
                        </div>
                    </div>
                </div>

                <!-- Dataset Summary -->
                <div class="premium-card">
                    <div class="section-title">Dataset Summary</div>
                    <div class="row g-3">
                        <div class="col-md-4">
                            <div class="small text-muted-custom">Dataset Name</div>
                            <div class="fw-semibold">{{ dataset.dataset_name }}</div>
                        </div>
                        <div class="col-md-4">
                            <div class="small text-muted-custom">Original Filename</div>
                            <div class="fw-semibold text-truncate">{{ dataset.original_filename }}</div>
                        </div>
                        <div class="col-md-4">
                            <div class="small text-muted-custom">Active Version</div>
                            <div class="fw-semibold">Version {{ version.version_number }}</div>
                        </div>
                        <div class="col-md-4">
                            <div class="small text-muted-custom">File Size</div>
                            <div class="fw-semibold">{{ version.file_size }} bytes</div>
                        </div>
                        <div class="col-md-4">
                            <div class="small text-muted-custom">Description</div>
                            <div class="fw-semibold">{{ dataset.description or "No description provided" }}</div>
                        </div>
                        <div class="col-md-4">
                            <div class="small text-muted-custom">Import Time</div>
                            <div class="fw-semibold">{{ dataset.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") }}</div>
                        </div>
                    </div>
                </div>

                <!-- Quality Score KPIs -->
                <div class="premium-card">
                    <div class="section-title">Data Quality Score</div>
                    <div class="row g-3">
                        <div class="col-md-4">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Quality Score Index</div>
                                <div class="metric-value">{{ profile.quality_score | round(2) }}/100</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Total Missing Cells</div>
                                <div class="metric-value text-cyan">{{ profile.missing_values }}</div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Total Duplicate Rows</div>
                                <div class="metric-value text-cyan">{{ profile.duplicate_rows }}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Profiling -->
                <div class="premium-card">
                    <div class="section-title">Data Profiling Schema</div>
                    <div class="table-responsive">
                        <table class="table table-premium align-middle mb-0">
                            <thead>
                                <tr>
                                    <th>Column Name</th>
                                    <th>Data Type</th>
                                    <th>Unique Values</th>
                                    <th>Missing Values</th>
                                    <th>Missing Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for col in profile.column_summary %}
                                <tr>
                                    <td class="fw-semibold"><code>{{ col.name }}</code></td>
                                    <td><span class="badge bg-secondary">{{ col.dtype }}</span></td>
                                    <td>{{ col.unique_count }}</td>
                                    <td>{{ col.missing_count }}</td>
                                    <td>{{ col.missing_pct | round(2) }}%</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Cleaning History -->
                <div class="premium-card">
                    <div class="section-title">Cleaning Lineage Log</div>
                    <div class="table-responsive">
                        <table class="table table-premium align-middle mb-0">
                            <thead>
                                <tr>
                                    <th>Rows Removed</th>
                                    <th>Duplicates Removed</th>
                                    <th>Missing Handled</th>
                                    <th>Outliers Handled</th>
                                    <th>Processing Duration</th>
                                    <th>Execution Time</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for job in dataset.cleaning_jobs %}
                                <tr>
                                    <td class="fw-bold">{{ job.rows_removed }}</td>
                                    <td>{{ job.duplicates_removed }}</td>
                                    <td>{{ job.missing_handled }}</td>
                                    <td>{{ job.outliers_handled }}</td>
                                    <td>{{ job.execution_time_ms }} ms</td>
                                    <td class="small">{{ job.created_at.strftime("%Y-%m-%d %H:%M:%S UTC") }}</td>
                                </tr>
                                {% else %}
                                <tr>
                                    <td colspan="6" class="text-center text-muted-custom py-3">No cleaning operations have been applied to this dataset yet.</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- EDA Statistics -->
                <div class="premium-card">
                    <div class="section-title">Exploratory Data Analysis (EDA) Statistics</div>
                    <div class="table-responsive">
                        <table class="table table-premium align-middle mb-0">
                            <thead>
                                <tr>
                                    <th>Column</th>
                                    <th>Mean</th>
                                    <th>Median</th>
                                    <th>Min</th>
                                    <th>Max</th>
                                    <th>Std Dev</th>
                                    <th>Skewness</th>
                                    <th>Kurtosis</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if eda and eda.statistics_json and eda.statistics_json.numeric_analysis %}
                                    {% for col, stats in eda.statistics_json.numeric_analysis.items() %}
                                    <tr>
                                        <td class="fw-semibold"><code>{{ col }}</code></td>
                                        <td>{{ stats.mean | round(2) if stats.mean is not none else "N/A" }}</td>
                                        <td>{{ stats.median | round(2) if stats.median is not none else "N/A" }}</td>
                                        <td>{{ stats.min | round(2) if stats.min is not none else "N/A" }}</td>
                                        <td>{{ stats.max | round(2) if stats.max is not none else "N/A" }}</td>
                                        <td>{{ stats.std | round(2) if stats.std is not none else "N/A" }}</td>
                                        <td>{{ stats.skewness | round(2) if stats.skewness is not none else "N/A" }}</td>
                                        <td>{{ stats.kurtosis | round(2) if stats.kurtosis is not none else "N/A" }}</td>
                                    </tr>
                                    {% endfor %}
                                {% else %}
                                    <tr>
                                        <td colspan="8" class="text-center text-muted-custom py-3">No numeric variables available for EDA.</td>
                                    </tr>
                                {% endif %}
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Insights -->
                <div class="premium-card">
                    <div class="section-title">AI Insights Observations</div>
                    <div class="row g-3">
                        {% if insights and insights.insights_json %}
                            {% for ins in insights.insights_json %}
                            <div class="col-md-6">
                                <div class="card h-100 border-0 bg-dark text-white p-3">
                                    <div class="d-flex justify-content-between align-items-center mb-2">
                                        <span class="badge {% if ins.severity == 'CRITICAL' or ins.severity == 'HIGH' %}badge-danger{% else %}badge-warning{% endif %} px-2 py-1">{{ ins.severity }}</span>
                                        <span class="small text-cyan">Confidence: {{ ins.confidence }}%</span>
                                    </div>
                                    <h6 class="text-primary mb-2">{{ ins.category }}</h6>
                                    <p class="small mb-1"><strong>Observation:</strong> {{ ins.observation }}</p>
                                    <p class="small text-muted-custom mb-2"><strong>Root Cause:</strong> {{ ins.root_cause }}</p>
                                    <div class="p-2 bg-secondary bg-opacity-25 rounded small text-cyan">
                                        <strong>Recommendation:</strong> {{ ins.recommendation }}
                                    </div>
                                </div>
                            </div>
                            {% endfor %}
                        {% else %}
                            <div class="col-12 py-3 text-center text-muted-custom">No insights have been generated.</div>
                        {% endif %}
                    </div>
                </div>

                <!-- ML Model Summary -->
                {% if ml_model %}
                <div class="premium-card">
                    <div class="section-title">Machine Learning Model Summary</div>
                    <div class="row g-3 mb-4">
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Target Column</div>
                                <div class="fw-bold"><code>{{ ml_model.target_column }}</code></div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Problem Type</div>
                                <div class="fw-bold text-uppercase">{{ ml_model.problem_type }}</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Champion Algorithm</div>
                                <div class="fw-bold text-cyan">{{ ml_model.model_type }}</div>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="metric-card">
                                <div class="text-muted-custom small mb-1">Best Evaluation Score</div>
                                <div class="metric-value">{{ ml_model.best_score | round(4) }}</div>
                            </div>
                        </div>
                    </div>

                    <div class="row">
                        <div class="col-md-6">
                            <h6 class="text-primary mb-3">Model Performance Details</h6>
                            <table class="table table-premium align-middle mb-0 text-xs">
                                <tbody>
                                    <tr>
                                        <td><strong>Training Configuration</strong></td>
                                        <td><code>Split: {{ ml_model.training_config.train_test_split * 100 }}% | CV: {{ ml_model.training_config.cross_validation }}</code></td>
                                    </tr>
                                    <tr>
                                        <td><strong>Training Rows</strong></td>
                                        <td>{{ ml_model.training_rows }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Testing Rows</strong></td>
                                        <td>{{ ml_model.testing_rows }}</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Model Binary Size</strong></td>
                                        <td>{{ (ml_model.model_size_bytes / 1024) | round(2) }} KB</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Training Duration</strong></td>
                                        <td>{{ ml_model.duration_ms }} ms</td>
                                    </tr>
                                    <tr>
                                        <td><strong>Dataset fingerprint (SHA-256)</strong></td>
                                        <td><small class="text-muted-custom">{{ ml_model.dataset_hash or "N/A" }}</small></td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                        <div class="col-md-6">
                            <h6 class="text-primary mb-3">Top Features Importance</h6>
                            <table class="table table-premium align-middle mb-0 text-xs">
                                <thead>
                                    <tr>
                                        <th>Feature</th>
                                        <th>Normalized Importance</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% if ml_model.feature_importances %}
                                        {% for feat, imp in ml_model.feature_importances.items() %}
                                        <tr>
                                            <td><code>{{ feat }}</code></td>
                                            <td>
                                                <div class="d-flex align-items-center">
                                                    <span class="me-2 fw-semibold">{{ (imp * 100) | round(2) }}%</span>
                                                    <div class="progress w-100 bg-secondary bg-opacity-25" style="height: 6px;">
                                                        <div class="progress-bar bg-info" role="progressbar" style="width: {{ imp * 100 }}%"></div>
                                                    </div>
                                                </div>
                                            </td>
                                        </tr>
                                        {% endfor %}
                                    {% else %}
                                        <tr>
                                            <td colspan="2" class="text-center text-muted-custom">No importances computed.</td>
                                        </tr>
                                    {% endif %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
                {% endif %}

                <!-- Footer -->
                <div class="footer-text">
                    <p class="mb-1">Report Generated By PrismIQ Data Intelligence Engine Version 1.0</p>
                    <p class="mb-0">Report ID: {{ report_id }} | Schema Version: 1.0 | Security Hash validation supported</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        t = jinja2.Template(html_template)
        rendered = t.render(
            dataset=dataset,
            version=version,
            profile=profile,
            eda=eda,
            insights=insights,
            ml_model=ml_model,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            report_id=report_id,
            user_id=user_id
        )
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(rendered)

    def _generate_pdf(self, filepath: str, dataset: Dataset, version: DatasetVersion, profile: DataProfile, eda: EdaResult, insights: AiInsight, report_id: UUID, user_id: UUID, ml_model: Optional[Any] = None) -> None:
        """Generates cover page, descriptive logs, and text summaries using ReportLab flowables."""
        doc = SimpleDocTemplate(filepath, pagesize=letter, leftMargin=40, rightMargin=40, topMargin=40, bottomMargin=40)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'CoverTitle',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=26,
            leading=30,
            textColor=colors.HexColor("#1A365D"),
            spaceAfter=15
        )
        subtitle_style = ParagraphStyle(
            'CoverSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor("#4A5568"),
            spaceAfter=40
        )
        h1_style = ParagraphStyle(
            'SectionH1',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#2B6CB0"),
            spaceBefore=20,
            spaceAfter=10
        )
        body_style = ParagraphStyle(
            'ReportBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#2D3748"),
            spaceAfter=8
        )
        
        # 1. Cover Page
        story.append(Spacer(1, 80))
        story.append(Paragraph("PrismIQ Analytics Report", title_style))
        story.append(Paragraph("Dataset Intelligence & Data Quality Summary", subtitle_style))
        story.append(Spacer(1, 20))
        
        meta_table_data = [
            [Paragraph("<b>Generated By:</b>", body_style), Paragraph("PrismIQ", body_style)],
            [Paragraph("<b>Generated At:</b>", body_style), Paragraph(datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"), body_style)],
            [Paragraph("<b>Dataset Name:</b>", body_style), Paragraph(dataset.dataset_name, body_style)],
            [Paragraph("<b>Dataset Version:</b>", body_style), Paragraph(f"Version {version.version_number}", body_style)],
            [Paragraph("<b>Quality Score:</b>", body_style), Paragraph(f"{profile.quality_score:.2f}/100", body_style)],
            [Paragraph("<b>Report ID:</b>", body_style), Paragraph(str(report_id), body_style)],
            [Paragraph("<b>User ID:</b>", body_style), Paragraph(str(user_id), body_style)],
            [Paragraph("<b>Engine Version:</b>", body_style), Paragraph("1.0", body_style)],
            [Paragraph("<b>Report Schema:</b>", body_style), Paragraph("1.0", body_style)]
        ]
        t_meta = Table(meta_table_data, colWidths=[150, 300])
        t_meta.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
            ('PADDING', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_meta)
        story.append(PageBreak())
        
        # 2. Executive Summary
        story.append(Paragraph("Executive Summary", h1_style))
        summary_text = (
            f"The dataset '{dataset.dataset_name}' currently holds a quality health score of "
            f"<b>{profile.quality_score:.2f}/100</b>. The active version contains a total of "
            f"{profile.missing_values} missing data cells and {profile.duplicate_rows} duplicate rows. "
            f"This summary highlights structural anomalies, cleaning lineages, and AI-recommended preprocessing steps."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))

        # 3. Dataset Information
        story.append(Paragraph("Dataset Information", h1_style))
        info_table_data = [
            [Paragraph("<b>Dataset Name:</b>", body_style), Paragraph(dataset.dataset_name, body_style)],
            [Paragraph("<b>Original Filename:</b>", body_style), Paragraph(dataset.original_filename, body_style)],
            [Paragraph("<b>Description:</b>", body_style), Paragraph(dataset.description or "No description provided", body_style)],
            [Paragraph("<b>File Size (Bytes):</b>", body_style), Paragraph(str(version.file_size), body_style)],
            [Paragraph("<b>Import Timestamp:</b>", body_style), Paragraph(dataset.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), body_style)]
        ]
        t_info = Table(info_table_data, colWidths=[150, 300])
        t_info.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ]))
        story.append(t_info)
        story.append(Spacer(1, 15))
        
        # 4. Quality Metrics
        story.append(Paragraph("Quality Metrics & Schema Profile", h1_style))
        profile_headers = [Paragraph("<b>Column Name</b>", body_style), Paragraph("<b>Data Type</b>", body_style), Paragraph("<b>Missing</b>", body_style), Paragraph("<b>Null %</b>", body_style)]
        profile_rows = [profile_headers]
        
        for col in profile.column_summary:
            profile_rows.append([
                Paragraph(col.get("name"), body_style),
                Paragraph(col.get("dtype"), body_style),
                Paragraph(str(col.get("missing_count")), body_style),
                Paragraph(f"{col.get('missing_pct'):.2f}%", body_style)
            ])
            
        t_prof = Table(profile_rows, colWidths=[150, 120, 90, 90])
        t_prof.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ]))
        story.append(t_prof)
        story.append(PageBreak())

        # 5. Cleaning Summary
        story.append(Paragraph("Cleaning Summary & History", h1_style))
        clean_headers = [Paragraph("<b>Removed Rows</b>", body_style), Paragraph("<b>Duplicates</b>", body_style), Paragraph("<b>Missing Handled</b>", body_style), Paragraph("<b>Outliers Handled</b>", body_style), Paragraph("<b>Time</b>", body_style)]
        clean_rows = [clean_headers]
        for job in dataset.cleaning_jobs:
            clean_rows.append([
                Paragraph(str(job.rows_removed), body_style),
                Paragraph(str(job.duplicates_removed), body_style),
                Paragraph(str(job.missing_handled), body_style),
                Paragraph(str(job.outliers_handled), body_style),
                Paragraph(f"{job.execution_time_ms} ms", body_style)
            ])
        if len(clean_rows) == 1:
            clean_rows.append([Paragraph("No cleaning jobs applied yet.", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style), Paragraph("", body_style)])
        t_clean = Table(clean_rows, colWidths=[90, 90, 100, 100, 70])
        t_clean.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
            ('PADDING', (0,0), (-1,-1), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ]))
        story.append(t_clean)
        story.append(Spacer(1, 15))

        # 6. EDA Statistics
        story.append(Paragraph("Exploratory Data Analysis (EDA)", h1_style))
        if eda and eda.statistics_json and eda.statistics_json.get("numeric_analysis"):
            num_analysis = eda.statistics_json.get("numeric_analysis")
            eda_headers = [Paragraph("<b>Column</b>", body_style), Paragraph("<b>Mean</b>", body_style), Paragraph("<b>Median</b>", body_style), Paragraph("<b>Std Dev</b>", body_style)]
            eda_rows = [eda_headers]
            for col, stats in num_analysis.items():
                eda_rows.append([
                    Paragraph(col, body_style),
                    Paragraph(f"{stats.get('mean'):.2f}" if stats.get('mean') is not None else "N/A", body_style),
                    Paragraph(f"{stats.get('median'):.2f}" if stats.get('median') is not None else "N/A", body_style),
                    Paragraph(f"{stats.get('std'):.2f}" if stats.get('std') is not None else "N/A", body_style)
                ])
            t_eda = Table(eda_rows, colWidths=[150, 100, 100, 100])
            t_eda.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ]))
            story.append(t_eda)
        else:
            story.append(Paragraph("No numeric data columns found for EDA calculations.", body_style))
        story.append(Spacer(1, 15))

        # 7. Insights
        story.append(Paragraph("AI Insights Observations", h1_style))
        if insights and insights.insights_json:
            for ins in insights.insights_json:
                ins_table_data = [
                    [Paragraph(f"<b>[{ins.get('rule_id')}] Category: {ins.get('category')}</b>", body_style), Paragraph(f"Severity: <b>{ins.get('severity')}</b>", body_style)],
                    [Paragraph(f"<b>Observation:</b> {ins.get('observation')}", body_style), Paragraph(f"Confidence: {ins.get('confidence')}%", body_style)],
                    [Paragraph(f"<b>Root Cause:</b> {ins.get('root_cause')}", body_style), Paragraph("", body_style)]
                ]
                t_ins = Table(ins_table_data, colWidths=[330, 120])
                t_ins.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
                    ('PADDING', (0,0), (-1,-1), 6),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                    ('SPAN', (0,2), (1,2))
                ]))
                story.append(t_ins)
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No insights generated.", body_style))
        story.append(PageBreak())

        # 8. Recommendations
        story.append(Paragraph("Actionable Recommendations", h1_style))
        if insights and insights.insights_json:
            rec_headers = [Paragraph("<b>Observation Link</b>", body_style), Paragraph("<b>Recommended Action</b>", body_style), Paragraph("<b>Actionability</b>", body_style)]
            rec_rows = [rec_headers]
            for ins in insights.insights_json:
                act = ins.get("actionability")
                act_str = f"{act * 100:.0f}%" if isinstance(act, (int, float)) else str(act or "N/A")
                rec_rows.append([
                    Paragraph(str(ins.get("category") or "N/A"), body_style),
                    Paragraph(str(ins.get("recommendation") or "N/A"), body_style),
                    Paragraph(act_str, body_style)
                ])
            t_rec = Table(rec_rows, colWidths=[120, 230, 100])
            t_rec.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ]))
            story.append(t_rec)
        else:
            story.append(Paragraph("No recommendations available.", body_style))
        story.append(Spacer(1, 15))

        # 8.5 Machine Learning Model Summary
        if ml_model:
            story.append(PageBreak())
            story.append(Paragraph("Machine Learning Model Summary", h1_style))
            story.append(Spacer(1, 10))
            
            ml_rows = [
                [Paragraph("<b>Model Parameter</b>", body_style), Paragraph("<b>Value</b>", body_style)],
                [Paragraph("Target Column", body_style), Paragraph(ml_model.target_column, body_style)],
                [Paragraph("Problem Type", body_style), Paragraph(ml_model.problem_type.upper(), body_style)],
                [Paragraph("Champion Estimator", body_style), Paragraph(ml_model.model_type, body_style)],
                [Paragraph("Evaluation Score (Best)", body_style), Paragraph(f"{ml_model.best_score:.4f}", body_style)],
                [Paragraph("Training / Testing Rows", body_style), Paragraph(f"{ml_model.training_rows} / {ml_model.testing_rows}", body_style)],
                [Paragraph("Training Duration", body_style), Paragraph(f"{ml_model.duration_ms} ms", body_style)],
                [Paragraph("Dataset Hash (SHA-256)", body_style), Paragraph(ml_model.dataset_hash or "N/A", body_style)],
            ]
            t_ml = Table(ml_rows, colWidths=[180, 270])
            t_ml.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                ('PADDING', (0,0), (-1,-1), 6),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
            ]))
            story.append(t_ml)
            story.append(Spacer(1, 15))
            
            if ml_model.feature_importances:
                story.append(Paragraph("<b>Top Features Importance</b>", h2_style))
                story.append(Spacer(1, 5))
                feat_rows = [[Paragraph("<b>Feature Column Name</b>", body_style), Paragraph("<b>Normalized Importance</b>", body_style)]]
                for feat, imp in ml_model.feature_importances.items():
                    feat_rows.append([
                        Paragraph(f"<code>{feat}</code>", body_style),
                        Paragraph(f"{imp * 100:.2f}%", body_style)
                    ])
                t_feat = Table(feat_rows, colWidths=[250, 200])
                t_feat.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EDF2F7")),
                    ('PADDING', (0,0), (-1,-1), 4),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                ]))
                story.append(t_feat)
                story.append(Spacer(1, 15))

        # 9. Appendix
        story.append(Paragraph("Appendix & Methodology Documentation", h1_style))
        story.append(Paragraph(
            "<b>Quality Score Index</b> is calculated as a weighted average of missing cell percentages "
            "and duplicate row ratios. Missing weights and duplicate weights default to 50.0% each, "
            "adjusted via server configuration parameters. <br/>"
            "<b>Engine Version</b>: 1.0.0 | <b>Report Schema</b>: 1.0 | <b>Checksum Algorithm</b>: SHA-256",
            body_style
        ))

        doc.build(story)

    async def generate_report(self, dataset_id: UUID, report_type: str, user_id: UUID) -> Report:
        """
        Orchestration pipeline: creates PENDING DB row, compiles report on disk asynchronously,
        updates status to COMPLETED, and logs checksum hashes and timings.
        """
        report_type = report_type.upper()
        if report_type not in ["PDF", "EXCEL", "HTML", "JSON"]:
            raise BadRequestException("Invalid report type requested")

        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        version = next((v for v in dataset.versions if v.is_current), None)
        if not version:
            raise BadRequestException("Dataset contains no active version to analyze")

        # Resolve Data Profile
        profile = await self.profile_repo.get_by_dataset_id(dataset_id)
        if not profile:
            raise BadRequestException("Data Profile has not been generated yet for this dataset")

        # Resolve EDA
        eda_service = EdaService(self.session)
        eda = await eda_service.eda_repo.get_by_version_id(version.id)
        if not eda:
            eda = await eda_service.run_eda(dataset_id, user_id)

        # Resolve AI Insights
        insights_service = AiInsightsService(self.session)
        insights = await insights_service.insights_repo.get_by_version_id(version.id)
        if not insights:
            insights = await insights_service.generate_insights(dataset_id, user_id)

        # Resolve ML Model champion if exists
        from app.models.ml_model import MLModel
        ml_result = await self.session.execute(
            select(MLModel)
            .filter_by(dataset_version_id=version.id, status="COMPLETED")
            .order_by(MLModel.created_at.desc())
        )
        ml_model = ml_result.scalars().first()

        # 1. Register PENDING record in DB
        report_id = uuid4()
        ext = "xlsx" if report_type == "EXCEL" else report_type.lower()
        filename = f"report_{report_id}.{ext}"
        storage_path = f"local://reports/{report_type.lower()}/{filename}"
        
        # Computed URLs
        download_url = f"/api/v1/reports/{report_id}/download"
        preview_url = f"/api/v1/reports/{report_id}/download" if report_type == "HTML" else None

        started_time = datetime.utcnow()

        report = Report(
            id=report_id,
            dataset_id=dataset_id,
            dataset_version_id=version.id,
            report_type=report_type,
            storage_path=storage_path,
            status="PENDING",
            file_size=0,
            generated_from_version=version.version_number,
            generation_time_ms=0,
            started_at=started_time,
            checksum_algorithm="SHA-256",
            report_schema_version="1.0",
            download_url=download_url,
            preview_url=preview_url
        )
        await self.report_repo.create(report)
        await self.session.commit()

        # Update status to GENERATING
        report.status = "GENERATING"
        await self.session.commit()

        # Local file storage folders preparation
        reports_folder = os.path.join(settings.STORAGE_ROOT, "reports", report_type.lower())
        os.makedirs(reports_folder, exist_ok=True)
        local_filepath = os.path.join(reports_folder, filename)

        try:
            if report_type == "JSON":
                self._generate_json(local_filepath, dataset, version, profile, eda, insights, report_id, user_id, ml_model)
            elif report_type == "HTML":
                self._generate_html(local_filepath, dataset, version, profile, eda, insights, report_id, user_id, ml_model)
            elif report_type == "EXCEL":
                local_csv_path = version.storage_path.replace("local://", "", 1)
                self._generate_excel(local_filepath, dataset, version, profile, eda, insights, local_csv_path, report_id, user_id, ml_model)
            elif report_type == "PDF":
                self._generate_pdf(local_filepath, dataset, version, profile, eda, insights, report_id, user_id, ml_model)
                
            completed_time = datetime.utcnow()
            generation_time_ms = int((completed_time - started_time).total_seconds() * 1000.0)

            # Update DB with completion metrics
            report.status = "COMPLETED"
            report.file_size = os.path.getsize(local_filepath)
            report.checksum = self._calculate_checksum(local_filepath)
            report.completed_at = completed_time
            report.generation_time_ms = generation_time_ms
            report.duration_ms = generation_time_ms
            await self.session.commit()
            
        except Exception as e:
            completed_time = datetime.utcnow()
            generation_time_ms = int((completed_time - started_time).total_seconds() * 1000.0)
            
            report.status = "FAILED"
            report.error_message = str(e)
            report.completed_at = completed_time
            report.generation_time_ms = generation_time_ms
            report.duration_ms = generation_time_ms
            await self.session.commit()
            if os.path.exists(local_filepath):
                os.remove(local_filepath)
            raise BadRequestException(f"Failed to generate report: {str(e)}")

        return report

    async def get_comparison_summary(self, dataset_id: UUID, v1_num: int, v2_num: int, user_id: UUID) -> dict:
        """
        Computes differences in schemas, data types, quality parameters, and row sizes side-by-side.
        """
        dataset = await self.dataset_repo.get_with_versions(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        v1 = next((v for v in dataset.versions if v.version_number == v1_num), None)
        v2 = next((v for v in dataset.versions if v.version_number == v2_num), None)
        if not v1 or not v2:
            raise BadRequestException(f"Specified version pairs ({v1_num}, {v2_num}) do not exist")

        v1_local = v1.storage_path.replace("local://", "", 1)
        v2_local = v2.storage_path.replace("local://", "", 1)

        v1_stats = self._compute_file_stats(v1_local)
        v2_stats = self._compute_file_stats(v2_local)

        # Computes delta
        rows_diff = v2_stats["rows_count"] - v1_stats["rows_count"]
        cols_diff = v2_stats["columns_count"] - v1_stats["columns_count"]
        size_diff = v2.file_size - v1.file_size
        quality_diff = v2_stats["quality_score"] - v1_stats["quality_score"]

        # Hashing rows to compute added/removed/changed rows count
        df1 = v1_stats["dataframe"]
        df2 = v2_stats["dataframe"]
        s1 = set(tuple(x) for x in df1.fillna("").values)
        s2 = set(tuple(x) for x in df2.fillna("").values)
        removed_rows_count = len(s1 - s2)
        added_rows_count = len(s2 - s1)
        changed_rows_count = max(0, len(df2) - len(df1) - added_rows_count + removed_rows_count)

        # Columns Added / Removed
        v1_cols = set(v1_stats["columns"].keys())
        v2_cols = set(v2_stats["columns"].keys())
        cols_added = list(v2_cols - v1_cols)
        cols_removed = list(v1_cols - v2_cols)

        # DataType Changes
        datatype_changes = {}
        for col in v1_cols & v2_cols:
            if v1_stats["columns"][col] != v2_stats["columns"][col]:
                datatype_changes[col] = {
                    "v1_type": v1_stats["columns"][col],
                    "v2_type": v2_stats["columns"][col]
                }

        # Query Cleaning Operations Applied (if any) in Target version
        result = await self.session.execute(
            select(CleaningJob).filter_by(target_version_id=v2.id)
        )
        job = result.scalar_one_or_none()
        ops_applied = job.cleaning_summary if job else []

        # Resolve AI Insights for v1 and v2
        insights_service = AiInsightsService(self.session)
        v1_insights = await insights_service.insights_repo.get_by_version_id(v1.id)
        v2_insights = await insights_service.insights_repo.get_by_version_id(v2.id)
        v1_ins_cats = set(ins.get("category") for ins in (v1_insights.insights_json if v1_insights else []))
        v2_ins_cats = set(ins.get("category") for ins in (v2_insights.insights_json if v2_insights else []))
        insights_added = list(v2_ins_cats - v1_ins_cats)
        insights_resolved = list(v1_ins_cats - v2_ins_cats)

        return {
            "version_difference": {
                "v1_number": v1_num,
                "v2_number": v2_num,
                "rows_difference": rows_diff,
                "columns_difference": cols_diff,
                "file_size_difference": size_diff,
                "quality_score_improvement": quality_diff,
                "changed_rows": changed_rows_count,
                "added_rows": added_rows_count,
                "removed_rows": removed_rows_count
            },
            "columns_added": cols_added,
            "columns_removed": cols_removed,
            "datatype_changes": datatype_changes,
            "cleaning_operations_applied": ops_applied,
            "profiling_difference": {
                "missing_cells_difference": v2_stats["missing_count"] - v1_stats["missing_count"],
                "duplicate_rows_difference": v2_stats["duplicate_count"] - v1_stats["duplicate_count"],
                "quality_score_difference": quality_diff
            },
            "insights_difference": {
                "v1_insights_count": len(v1_ins_cats),
                "v2_insights_count": len(v2_ins_cats),
                "new_insights": insights_added,
                "resolved_insights": insights_resolved
            },
            "v1_metrics": {
                "rows_count": v1_stats["rows_count"],
                "columns_count": v1_stats["columns_count"],
                "missing_count": v1_stats["missing_count"],
                "duplicate_count": v1_stats["duplicate_count"],
                "quality_score": v1_stats["quality_score"]
            },
            "v2_metrics": {
                "rows_count": v2_stats["rows_count"],
                "columns_count": v2_stats["columns_count"],
                "missing_count": v2_stats["missing_count"],
                "duplicate_count": v2_stats["duplicate_count"],
                "quality_score": v2_stats["quality_score"]
            }
        }

    async def list_reports(
        self,
        user_id: UUID,
        page: int = 1,
        limit: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        format: Optional[str] = None,
        dataset_id: Optional[UUID] = None,
        created_before: Optional[datetime] = None,
        created_after: Optional[datetime] = None,
        sort: Optional[str] = None
    ) -> List[Report]:
        """
        Retrieves user owned reports with pagination and complex filters.
        """
        stmt = select(Report).join(Dataset).filter(Dataset.user_id == user_id)
        
        # Search: check if dataset name matches search
        if search:
            stmt = stmt.filter(Dataset.dataset_name.ilike(f"%{search}%"))
            
        # Status
        if status:
            stmt = stmt.filter(Report.status == status.upper())
            
        # Format (report_type)
        if format:
            stmt = stmt.filter(Report.report_type == format.upper())
            
        # Dataset ID
        if dataset_id:
            stmt = stmt.filter(Report.dataset_id == dataset_id)
            
        # Created after / before
        if created_after:
            stmt = stmt.filter(Report.created_at >= created_after)
        if created_before:
            stmt = stmt.filter(Report.created_at <= created_before)
            
        # Offset & Limit
        skip = (page - 1) * limit
        stmt = stmt.offset(skip).limit(limit)
        
        # Sorting
        if sort:
            parts = sort.split(":")
            col = parts[0]
            direction = parts[1] if len(parts) > 1 else "asc"
            
            if col == "created_at":
                stmt = stmt.order_by(Report.created_at.desc() if direction == "desc" else Report.created_at.asc())
            elif col == "file_size":
                stmt = stmt.order_by(Report.file_size.desc() if direction == "desc" else Report.file_size.asc())
            elif col == "report_type":
                stmt = stmt.order_by(Report.report_type.desc() if direction == "desc" else Report.report_type.asc())
            elif col == "status":
                stmt = stmt.order_by(Report.status.desc() if direction == "desc" else Report.status.asc())
        else:
            stmt = stmt.order_by(Report.created_at.desc())
            
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

