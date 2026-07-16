export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_number: number;
  storage_path: string;
  file_size: number;
  status: string;
  created_at: string;
  is_current: boolean;
}

export interface ColumnSummary {
  name: string;
  dtype: string;
  missing_count: number;
  missing_pct: number;
  unique_count: number;
  sample_values: any[];
  mean?: number;
  median?: number;
  min?: number;
  max?: number;
  std?: number;
  avg_length?: number;
  max_length?: number;
  min_date?: string;
  max_date?: string;
}

export interface DataProfile {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  rows_count: number;
  columns_count: number;
  missing_values: number;
  duplicate_rows: number;
  quality_score: number;
  column_summary: ColumnSummary[];
  created_at: string;
}

export interface CleaningJob {
  id: string;
  dataset_id: string;
  source_version_id: string;
  target_version_id: string;
  operations_applied: any[];
  rows_removed: number;
  duplicates_removed: number;
  missing_handled: number;
  outliers_handled: number;
  execution_time_ms: number;
  created_at: string;
}

export interface Dataset {
  id: string;
  user_id: string;
  dataset_name: string;
  original_filename: string;
  description: string | null;
  source_type: string;
  created_at: string;
  versions?: DatasetVersion[];
  profile?: DataProfile | null;
  cleaning_jobs?: CleaningJob[];
}

export interface DatasetDetailResponse extends Dataset {
  versions: DatasetVersion[];
}

export interface EdaResult {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  statistics_json: {
    numeric_analysis?: Record<string, {
      mean: number;
      median: number;
      min: number;
      max: number;
      std: number;
      variance: number;
      skewness: number;
      kurtosis: number;
    }>;
    correlation_matrix?: Record<string, Record<string, number>>;
  };
  charts_json?: {
    correlations?: Array<{
      column1: string;
      column2: string;
      coefficient: number;
    }>;
  };
  execution_time_ms: number;
  created_at: string;
}

export interface AiInsightItem {
  rule_id: string;
  category: string;
  severity: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  actionability: number;
  observation: string;
  root_cause: string;
  evidence: any;
  recommendation: string;
  recommended_cleaning: any[];
}

export interface AiInsight {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  summary_json: {
    overall_health: string;
    quality_score: number;
    total_insights_count: number;
    priority_distribution: {
      critical: number;
      high: number;
      medium: number;
      low: number;
      info: number;
    };
  };
  insights_json: AiInsightItem[];
  execution_time_ms: number;
  created_at: string;
}
