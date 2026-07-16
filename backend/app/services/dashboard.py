"""
Dashboard API aggregation service logic.
"""
import time
import math
from typing import List, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.data_profile import DataProfile
from app.models.cleaning_job import CleaningJob
from app.models.eda_result import EdaResult
from app.models.ai_insight import AiInsight
from app.common.enums import DatasetStatus


class DashboardService:
    """
    Consolidates dataset lifecycles, sizes, versions, cleaning logs, and insights into unified frontend-ready JSON.
    """
    def __init__(self, session: AsyncSession):
        self.session = session

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

    def _build_kpis(self, datasets: List[Dataset]) -> Dict[str, Any]:
        """Calculates total sizes, versions count, and averages of quality scores."""
        total_datasets = len(datasets)
        total_versions = sum(len(d.versions) for d in datasets)
        total_storage_bytes = sum(v.file_size for d in datasets for v in d.versions)
        
        quality_scores = [d.profile.quality_score for d in datasets if d.profile is not None]
        avg_quality = (sum(quality_scores) / len(quality_scores)) if quality_scores else 100.0
        
        return {
            "total_datasets": total_datasets,
            "total_versions": total_versions,
            "total_storage_bytes": total_storage_bytes,
            "average_quality_score": avg_quality
        }

    def _build_charts(self, datasets: List[Dataset]) -> Dict[str, Any]:
        """Formulates status distribution, quality rankings, and storage breakdowns ready for plotting."""
        # Status distribution (Pie Chart)
        status_counts = {}
        for d in datasets:
            current_v = next((v for v in d.versions if v.is_current), None)
            stat = current_v.status.value if current_v else "UPLOADED"
            status_counts[stat] = status_counts.get(stat, 0) + 1
            
        status_chart = {
            "type": "pie",
            "title": "Dataset Status Distribution",
            "labels": list(status_counts.keys()),
            "values": list(status_counts.values())
        }

        # Quality Scores (Bar Chart)
        quality_labels = []
        quality_values = []
        for d in datasets[:10]:
            quality_labels.append(d.dataset_name)
            quality_values.append(d.profile.quality_score if d.profile else 100.0)
            
        quality_chart = {
            "type": "bar",
            "title": "Top Dataset Quality Scores",
            "labels": quality_labels,
            "values": quality_values
        }

        # Storage breakdown (Pie/Bar Chart)
        storage_labels = []
        storage_values = []
        total_bytes = sum(v.file_size for d in datasets for v in d.versions)
        
        for d in datasets[:10]:
            d_bytes = sum(v.file_size for v in d.versions)
            storage_labels.append(d.dataset_name)
            storage_values.append(d_bytes)
            
        storage_chart = {
            "type": "pie",
            "title": "Storage Allocation Breakdown",
            "labels": storage_labels,
            "values": storage_values,
            "percentages": [(v / total_bytes * 100.0) if total_bytes > 0 else 0.0 for v in storage_values]
        }

        return {
            "status_distribution": status_chart,
            "quality_scores": quality_chart,
            "storage_breakdown": storage_chart
        }

    def _build_recent_activity(self, datasets: List[Dataset]) -> List[Dict[str, Any]]:
        """Merges version creations, cleanings, and analyses into a single sorted log."""
        activities = []
        for d in datasets:
            # Uploads
            for v in d.versions:
                activities.append({
                    "type": "UPLOAD",
                    "icon": "upload",
                    "color": "blue",
                    "dataset_name": d.dataset_name,
                    "version": v.version_number,
                    "title": "Dataset uploaded",
                    "description": f"Version {v.version_number} saved ({v.file_size} bytes)",
                    "timestamp": v.created_at
                })
            # Cleanings
            for c in d.cleaning_jobs:
                activities.append({
                    "type": "CLEAN",
                    "icon": "sparkles",
                    "color": "green",
                    "dataset_name": d.dataset_name,
                    "version": None,
                    "title": "Data clean applied",
                    "description": f"Dropped {c.rows_removed} rows, filled {c.missing_handled} nulls",
                    "timestamp": c.created_at
                })
            # EDA
            for eda in d.eda_results:
                activities.append({
                    "type": "EDA",
                    "icon": "chart-bar",
                    "color": "purple",
                    "dataset_name": d.dataset_name,
                    "version": None,
                    "title": "EDA analyzed",
                    "description": "Exploratory statistics computed",
                    "timestamp": eda.created_at
                })
            # Insights
            for insight in d.ai_insights:
                activities.append({
                    "type": "INSIGHTS",
                    "icon": "lightbulb",
                    "color": "yellow",
                    "dataset_name": d.dataset_name,
                    "version": None,
                    "title": "AI insights compiled",
                    "description": f"Generated {insight.summary_json.get('total_insights_count', 0)} data observations",
                    "timestamp": insight.created_at
                })

        # Sort descending by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)
        # Standardize timestamps to ISO strings and return top 10
        recent = activities[:10]
        for act in recent:
            if isinstance(act["timestamp"], datetime):
                act["timestamp"] = act["timestamp"].isoformat()
        return recent

    def _build_recent_datasets(self, datasets: List[Dataset]) -> List[Dict[str, Any]]:
        """Fetches top 5 updated datasets with version info and current quality metrics."""
        sorted_datasets = sorted(datasets, key=lambda x: x.updated_at, reverse=True)
        recent = []
        for d in sorted_datasets[:5]:
            current_v = next((v for v in d.versions if v.is_current), None)
            recent.append({
                "id": d.id,
                "name": d.dataset_name,
                "status": current_v.status.value if current_v else "UPLOADED",
                "quality_score": d.profile.quality_score if d.profile else 100.0,
                "version": len(d.versions),
                "last_updated": d.updated_at.isoformat()
            })
        return recent

    def _build_cleaning_jobs(self, datasets: List[Dataset]) -> List[Dict[str, Any]]:
        """Aggregates recent 5 cleaning sessions metrics."""
        jobs = []
        for d in datasets:
            for c in d.cleaning_jobs:
                jobs.append({
                    "dataset_name": d.dataset_name,
                    "removed_duplicates": c.duplicates_removed,
                    "removed_outliers": c.outliers_handled,
                    "missing_handled": c.missing_handled,
                    "execution_time_ms": c.execution_time_ms,
                    "timestamp": c.created_at
                })
        jobs.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_jobs = jobs[:5]
        for job in recent_jobs:
            if isinstance(job["timestamp"], datetime):
                job["timestamp"] = job["timestamp"].isoformat()
        return recent_jobs

    def _build_insights(self, datasets: List[Dataset]) -> List[Dict[str, Any]]:
        """Collects top severity AI insights warnings across all datasets."""
        high_severity_warnings = []
        for d in datasets:
            for insight in d.ai_insights:
                # Retrieve list of insights
                for ins in insight.insights_json:
                    if ins.get("severity") in ["CRITICAL", "HIGH"]:
                        high_severity_warnings.append({
                            "dataset_name": d.dataset_name,
                            "rule_id": ins.get("rule_id"),
                            "severity": ins.get("severity"),
                            "observation": ins.get("observation"),
                            "recommendation": ins.get("recommendation"),
                            "timestamp": insight.created_at
                        })
        high_severity_warnings.sort(key=lambda x: x["timestamp"], reverse=True)
        recent_warnings = high_severity_warnings[:5]
        for warn in recent_warnings:
            if isinstance(warn["timestamp"], datetime):
                warn["timestamp"] = warn["timestamp"].isoformat()
        return recent_warnings

    async def get_dashboard_summary(self, user_id: UUID) -> Dict[str, Any]:
        """
        Gathers eagerly loaded database collections, coordinates builders,
        and returns a unified dashboard summary payload.
        """
        start_time = time.perf_counter()
        
        # Load user datasets eagerly
        result = await self.session.execute(
            select(Dataset)
            .filter_by(user_id=user_id)
            .options(
                selectinload(Dataset.versions),
                selectinload(Dataset.profile),
                selectinload(Dataset.cleaning_jobs),
                selectinload(Dataset.eda_results),
                selectinload(Dataset.ai_insights)
            )
        )
        datasets = list(result.scalars().all())

        # Construct payload segments
        kpis = self._build_kpis(datasets)
        charts = self._build_charts(datasets)
        recent_activity = self._build_recent_activity(datasets)
        recent_datasets = self._build_recent_datasets(datasets)
        cleaning_jobs = self._build_cleaning_jobs(datasets)
        insights = self._build_insights(datasets)

        # Load user reports
        dataset_ids = [d.id for d in datasets]
        recent_reports = []
        if dataset_ids:
            from app.models.report import Report
            rep_result = await self.session.execute(
                select(Report)
                .filter(Report.dataset_id.in_(dataset_ids))
                .order_by(Report.created_at.desc())
                .limit(5)
            )
            reports_list = list(rep_result.scalars().all())
            for rep in reports_list:
                dataset_name = next((d.dataset_name for d in datasets if d.id == rep.dataset_id), "Unknown")
                recent_reports.append({
                    "id": str(rep.id),
                    "dataset_name": dataset_name,
                    "report_type": rep.report_type,
                    "status": rep.status,
                    "file_size": rep.file_size,
                    "generated_from_version": rep.generated_from_version,
                    "download_url": rep.download_url,
                    "created_at": rep.created_at.isoformat()
                })

        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000.0)

        # Assemble and sanitize response
        response = {
            "kpis": kpis,
            "charts": charts,
            "recent_activity": recent_activity,
            "recent_datasets": recent_datasets,
            "recent_cleaning_jobs": cleaning_jobs,
            "recent_insights": insights,
            "recent_reports": recent_reports,
            "metadata": {
                "generated_at": datetime.utcnow().isoformat(),
                "api_version": "v1",
                "execution_time_ms": execution_time_ms
            }
        }
        
        return self._sanitize_floats(response)

