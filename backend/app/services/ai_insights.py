"""
AI Insights Engine service logic.
"""
import time
import math
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.exceptions.base import BadRequestException, NotFoundException
from app.models.ai_insight import AiInsight
from app.models.dataset import Dataset
from app.models.dataset_version import DatasetVersion
from app.models.data_profile import DataProfile
from app.models.eda_result import EdaResult
from app.repositories.ai_insight import AiInsightRepository
from app.repositories.dataset import DatasetRepository
from app.repositories.dataset_version import DatasetVersionRepository
from app.repositories.data_profile import DataProfileRepository
from app.services.eda import EdaService


class AiInsightsService:
    """
    Orchestrates the statistical AI Insights rule-engine, priority ranking, and LLM context extraction.
    """
    def __init__(self, session: AsyncSession):
        self.session = session
        self.dataset_repo = DatasetRepository(session)
        self.version_repo = DatasetVersionRepository(session)
        self.profile_repo = DataProfileRepository(session)
        self.insights_repo = AiInsightRepository(session)

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

    def _rule_engine(self, profile: DataProfile, eda: EdaResult) -> List[Dict[str, Any]]:
        """
        Stage 1: Evaluates statistical profiles and EDA outputs to trigger analytical rules.
        """
        rules_triggered = []

        # 1. Missing Values (QUAL_001)
        if profile.missing_values > 0:
            summary = eda.summary_json
            total_cells = summary["rows_count"] * summary["columns_count"]
            missing_pct = (profile.missing_values / total_cells * 100.0) if total_cells > 0 else 0.0
            
            # Find the columns with the highest missing values from profile.column_summary
            worst_cols = []
            for col_info in profile.column_summary:
                m_count = col_info.get("missing_count", 0)
                if m_count > 0:
                    worst_cols.append((col_info["name"], m_count))
            worst_cols.sort(key=lambda x: x[1], reverse=True)
            
            rules_triggered.append({
                "rule_id": "QUAL_001",
                "category": "Quality",
                "missing_pct": missing_pct,
                "missing_count": profile.missing_values,
                "worst_columns": worst_cols[:3]
            })

        # 2. Duplicate Records (QUAL_002)
        if profile.duplicate_rows > 0:
            summary = eda.summary_json
            total_rows = summary["rows_count"]
            duplicate_pct = (profile.duplicate_rows / total_rows * 100.0) if total_rows > 0 else 0.0
            
            rules_triggered.append({
                "rule_id": "QUAL_002",
                "category": "Quality",
                "duplicate_pct": duplicate_pct,
                "duplicate_rows": profile.duplicate_rows
            })

        # 3. Numeric Outliers (OUT_003)
        outlier_data = eda.charts_json.get("outliers", {})
        worst_outliers = []
        for col, stats in outlier_data.items():
            count = stats.get("outlier_count", 0)
            if count > 0:
                worst_outliers.append((col, count, stats.get("outlier_percentage", 0.0)))
        
        worst_outliers.sort(key=lambda x: x[1], reverse=True)
        if worst_outliers:
            rules_triggered.append({
                "rule_id": "OUT_003",
                "category": "Risk",
                "outliers": worst_outliers[:3]
            })

        # 4. Correlations (CORR_004)
        correlations = eda.charts_json.get("correlations", [])
        strong_corrs = [c for c in correlations if abs(c["coefficient"]) >= 0.5]
        if strong_corrs:
            rules_triggered.append({
                "rule_id": "CORR_004",
                "category": "Correlation",
                "correlations": strong_corrs[:5]  # Limit to top 5 correlations
            })

        # 5. Cardinality (CARD_005)
        categorical_info = eda.statistics_json.get("categorical_analysis", {})
        high_cardinality_cols = []
        for col, stats in categorical_info.items():
            ratio = stats.get("cardinality_ratio", 0.0)
            unique_cnt = stats.get("unique_count", 0)
            if ratio > 0.5 and unique_cnt > 10:
                high_cardinality_cols.append((col, unique_cnt, ratio))
        
        if high_cardinality_cols:
            rules_triggered.append({
                "rule_id": "CARD_005",
                "category": "Statistics",
                "columns": high_cardinality_cols[:3]
            })

        # 6. Datetime Timeline coverage (TEMP_006)
        datetime_info = eda.statistics_json.get("datetime_analysis", {})
        if datetime_info:
            rules_triggered.append({
                "rule_id": "TEMP_006",
                "category": "Timeline",
                "info": datetime_info
            })

        return rules_triggered

    def _insight_generator(self, rules_triggered: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 2 & 3: Formulates descriptive business insights, confidence, actionability, and evidence.
        """
        raw_insights = []

        for rule in rules_triggered:
            rule_id = rule["rule_id"]
            
            if rule_id == "QUAL_001":
                worst_names = ", ".join(f"`{c[0]}` ({c[1]} nulls)" for c in rule["worst_columns"])
                pct = rule["missing_pct"]
                severity = "CRITICAL" if pct > 20.0 else "HIGH" if pct > 10.0 else "MEDIUM"
                
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Quality",
                    "severity": severity,
                    "confidence": 0.98,
                    "actionability": 0.90,
                    "observation": f"Data completeness issues detected. {pct:.2f}% of data cells contain missing values.",
                    "root_cause": f"A total of {rule['missing_count']} cells are empty in the active dataset version, primarily concentrated in columns: {worst_names}.",
                    "evidence": {
                        "missing_count": rule["missing_count"],
                        "missing_percentage": pct,
                        "columns_affected": [c[0] for c in rule["worst_columns"]]
                    },
                    "recommendation": "Address empty data cells using fill strategies. For continuous numeric parameters, median or mode fill is recommended.",
                    "recommended_cleaning": [
                        {
                            "type": "fill_missing",
                            "column": c[0],
                            "strategy": "median"
                        }
                        for c in rule["worst_columns"]
                    ]
                })

            elif rule_id == "QUAL_002":
                pct = rule["duplicate_pct"]
                severity = "HIGH" if pct > 10.0 else "MEDIUM"
                
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Quality",
                    "severity": severity,
                    "confidence": 0.99,
                    "actionability": 0.95,
                    "observation": f"Duplicate records identified. {pct:.2f}% of rows are exact duplicates.",
                    "root_cause": f"The dataset version contains {rule['duplicate_rows']} redundant rows, suggesting duplicate ingestion sessions or database record logging overlaps.",
                    "evidence": {
                        "duplicate_rows_count": rule["duplicate_rows"],
                        "duplicate_percentage": pct
                    },
                    "recommendation": "Execute standard drop duplicates cleaning to preserve data integrity and prevent calculation bias.",
                    "recommended_cleaning": [
                        {
                            "type": "drop_duplicates"
                        }
                    ]
                })

            elif rule_id == "OUT_003":
                worst_names = ", ".join(f"`{c[0]}` ({c[1]} outliers, {c[2]:.1f}%)" for c in rule["outliers"])
                # Extract first column for highest severity
                highest_pct = rule["outliers"][0][2]
                severity = "HIGH" if highest_pct > 5.0 else "MEDIUM"
                
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Risk",
                    "severity": severity,
                    "confidence": 0.92,
                    "actionability": 0.85,
                    "observation": "Extraneous value outliers detected in numeric variables.",
                    "root_cause": f"Outliers were discovered beyond standard 1.5x Interquartile Ranges (IQR), specifically in: {worst_names}.",
                    "evidence": {
                        "outlier_columns": [c[0] for c in rule["outliers"]],
                        "outlier_percentages": {c[0]: c[2] for c in rule["outliers"]}
                    },
                    "recommendation": "Evaluate outliers. Outliers can represent measurement faults or rare valid events. Consider applying IQR trimming to isolate distribution metrics.",
                    "recommended_cleaning": [
                        {
                            "type": "remove_outliers",
                            "column": c[0],
                            "strategy": "iqr"
                        }
                        for c in rule["outliers"]
                    ]
                })

            elif rule_id == "CORR_004":
                corrs = rule["correlations"]
                worst_names = ", ".join(f"`{c['column1']}` & `{c['column2']}` (r={c['coefficient']:.2f})" for c in corrs)
                
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Correlation",
                    "severity": "HIGH" if any(abs(c["coefficient"]) >= 0.8 for c in corrs) else "MEDIUM",
                    "confidence": 0.95,
                    "actionability": 0.70,
                    "observation": "Strong linear relationship detected between numeric columns.",
                    "root_cause": f"Pearson correlation analysis indicates strong associations: {worst_names}. Highly correlated variables move together systematically.",
                    "evidence": {
                        "strong_correlations": corrs
                    },
                    "recommendation": "These variables exhibit high linear dependency. Consider removing one column or performing dimensionality reduction to avoid multicollinearity in downstream models.",
                    "recommended_cleaning": []
                })

            elif rule_id == "CARD_005":
                cols = rule["columns"]
                worst_names = ", ".join(f"`{c[0]}` ({c[1]} unique, {c[2]*100:.1f}%)" for c in cols)
                
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Statistics",
                    "severity": "LOW",
                    "confidence": 0.90,
                    "actionability": 0.60,
                    "observation": "High cardinality in categorical data columns.",
                    "root_cause": f"Categorical parameters contain high ratios of unique values: {worst_names}, implying they represent textual logs, indexes, or identifiers.",
                    "evidence": {
                        "cardinality_details": {c[0]: {"unique_count": c[1], "ratio": c[2]} for c in cols}
                    },
                    "recommendation": "Ensure these columns are standard strings. Consider group standardizations or mapping key features.",
                    "recommended_cleaning": [
                        {
                            "type": "cast_type",
                            "column": c[0],
                            "target_type": "string"
                        }
                        for c in cols
                    ]
                })

            elif rule_id == "TEMP_006":
                # Datetimes spans
                datetime_dict = rule["info"]
                desc_list = []
                evidence_dict = {}
                for col, stats in datetime_dict.items():
                    desc_list.append(f"`{col}` spanning {stats['span_days']:.1f} days (from {stats['earliest_date']} to {stats['latest_date']})")
                    evidence_dict[col] = stats
                    
                raw_insights.append({
                    "rule_id": rule_id,
                    "category": "Timeline",
                    "severity": "INFO",
                    "confidence": 0.95,
                    "actionability": 0.50,
                    "observation": "Temporal timelines coverage loaded successfully.",
                    "root_cause": f"Datetime intervals spans detected: {', '.join(desc_list)}.",
                    "evidence": {
                        "temporal_spans": evidence_dict
                    },
                    "recommendation": "If running cyclic or seasonal forecasts, ensure this timeline span covers at least one complete calendar year or cyclic sales window.",
                    "recommended_cleaning": []
                })

        return raw_insights

    def _priority_ranker(self, insights: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 4: Sorts insights dynamically by severity level priority (CRITICAL -> HIGH -> MEDIUM -> LOW -> INFO).
        """
        priority_map = {
            "CRITICAL": 5,
            "HIGH": 4,
            "MEDIUM": 3,
            "LOW": 2,
            "INFO": 1
        }
        insights.sort(key=lambda x: priority_map.get(x["severity"], 0), reverse=True)
        return insights

    def _json_formatter(
        self,
        insights: List[Dict[str, Any]],
        profile: DataProfile,
        eda: EdaResult,
        dataset: Dataset
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Stage 5: Aggregates executive health summaries and LLM context blocks.
        """
        # Overall Health Score calculation
        quality = profile.quality_score
        
        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        for ins in insights:
            sev = ins["severity"].lower()
            if sev in severity_counts:
                severity_counts[sev] += 1
                
        # Deduce health status label
        if severity_counts["critical"] > 0 or quality < 50.0:
            health = "CRITICAL"
        elif severity_counts["high"] > 2 or quality < 70.0:
            health = "POOR"
        elif severity_counts["high"] > 0 or quality < 85.0:
            health = "FAIR"
        elif quality >= 95.0 and severity_counts["medium"] == 0:
            health = "EXCELLENT"
        else:
            health = "GOOD"

        summary_json = {
            "overall_health": health,
            "quality_score": quality,
            "total_insights_count": len(insights),
            "priority_distribution": severity_counts
        }

        # Build prompt context-ready string
        prompt_friendly_context = f"# DATASET METRICS SUMMARY: {dataset.dataset_name}\n"
        prompt_friendly_context += f"- **Shape**: {eda.summary_json['rows_count']} rows, {eda.summary_json['columns_count']} columns\n"
        prompt_friendly_context += f"- **Data Quality Score**: {quality:.1f}/100\n"
        prompt_friendly_context += f"- **Null Value Cells**: {profile.missing_values} empty cells\n"
        prompt_friendly_context += f"- **Duplicate Records**: {profile.duplicate_rows} duplicate rows\n\n"
        
        prompt_friendly_context += "## COLUMNS DETAILED SCHEMAS:\n"
        for col_info in profile.column_summary:
            prompt_friendly_context += f"- Column `{col_info['name']}`: dtype={col_info['dtype']}, unique_values={col_info['unique_count']}, missing_cells={col_info['missing_count']}\n"
            
        corrs = eda.charts_json.get("correlations", [])
        if corrs:
            prompt_friendly_context += "\n## LINEAR PEARSON CORRELATIONS (r >= 0.5):\n"
            for c in corrs:
                if abs(c["coefficient"]) >= 0.5:
                    prompt_friendly_context += f"- `{c['column1']}` and `{c['column2']}`: r={c['coefficient']:.2f}\n"

        prompt_context_json = {
            "dataset_name": dataset.dataset_name,
            "rows_count": eda.summary_json['rows_count'],
            "columns_count": eda.summary_json['columns_count'],
            "quality_score": quality,
            "prompt_friendly_string": prompt_friendly_context
        }

        return summary_json, prompt_context_json

    async def generate_insights(self, dataset_id: UUID, user_id: UUID) -> AiInsight:
        """
        Orchestration pipeline: resolves active profile and EDA files, runs rule engine,
        generates confidence ratings, formats LLM templates, and persists updates.
        """
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

        # Resolve EDA (or generate on-the-fly)
        eda_service = EdaService(self.session)
        eda = await eda_service.eda_repo.get_by_version_id(version.id)
        if not eda:
            eda = await eda_service.run_eda(dataset_id, user_id)

        start_time = time.perf_counter()

        # Run Pipeline Steps
        rules = self._rule_engine(profile, eda)
        insights = self._insight_generator(rules)
        insights = self._priority_ranker(insights)
        summary, prompt_context = self._json_formatter(insights, profile, eda, dataset)

        # Sanitize floats
        summary = self._sanitize_floats(summary)
        insights = self._sanitize_floats(insights)
        prompt_context = self._sanitize_floats(prompt_context)

        # Clear existing entries
        existing_insights = await self.insights_repo.get_by_version_id(version.id)
        if existing_insights:
            await self.insights_repo.delete(existing_insights.id)

        end_time = time.perf_counter()
        execution_time_ms = int((end_time - start_time) * 1000.0)

        insight = AiInsight(
            id=uuid4(),
            dataset_id=dataset_id,
            dataset_version_id=version.id,
            summary_json=summary,
            insights_json=insights,
            prompt_context_json=prompt_context,
            execution_time_ms=execution_time_ms,
            engine_version="1.0"
        )
        await self.insights_repo.create(insight)
        await self.session.flush()

        return insight

    async def get_insights(self, dataset_id: UUID, user_id: UUID) -> AiInsight:
        """
        Retrieves generated insights matching the active dataset version.
        """
        dataset = await self.dataset_repo.get(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise NotFoundException("Dataset workspace not found")

        version = await self.version_repo.get_current_version(dataset_id)
        if not version:
            raise BadRequestException("Dataset contains no active version")

        insight = await self.insights_repo.get_by_version_id(version.id)
        if not insight:
            raise NotFoundException("No AI Insights have been run yet for the active version")
            
        return insight

    async def get_insights_summary(self, dataset_id: UUID, user_id: UUID) -> dict:
        """
        Lightweight endpoint returning only summary stats metrics.
        """
        insight = await self.get_insights(dataset_id, user_id)
        return insight.summary_json
