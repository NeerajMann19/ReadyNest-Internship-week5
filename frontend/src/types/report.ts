export interface Report {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  report_type: 'PDF' | 'EXCEL' | 'HTML' | 'JSON';
  storage_path: string;
  status: 'PENDING' | 'GENERATING' | 'COMPLETED' | 'FAILED' | 'EXPIRED';
  file_size: number;
  generated_from_version: number;
  generation_time_ms: number;
  report_schema_version: string;
  checksum: string | null;
  checksum_algorithm: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_ms: number | null;
  error_message: string | null;
  download_url: string;
  preview_url: string | null;
  created_at: string;
}

export interface DatasetCompareResult {
  version_difference: {
    v1_number: number;
    v2_number: number;
    rows_difference: number;
    columns_difference: number;
    file_size_difference: number;
    quality_score_improvement: number;
    changed_rows: number;
    added_rows: number;
    removed_rows: number;
  };
  columns_added: string[];
  columns_removed: string[];
  datatype_changes: Record<string, { v1_type: string; v2_type: string }>;
  cleaning_operations_applied: any[];
  profiling_difference: {
    missing_cells_difference: number;
    duplicate_rows_difference: number;
    quality_score_difference: number;
  };
  insights_difference: {
    v1_insights_count: number;
    v2_insights_count: number;
    new_insights: string[];
    resolved_insights: string[];
  };
  v1_metrics: Record<string, any>;
  v2_metrics: Record<string, any>;
}
