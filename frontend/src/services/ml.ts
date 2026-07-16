/**
 * Frontend API client service for Machine Learning operations.
 */
import { apiClient } from '../lib/apiClient';

export interface MLModelTrainRequest {
  target_column: string;
  problem_type?: string;
  candidate_algorithms?: string[];
  cross_validation?: boolean;
  random_state?: number;
}

export interface MLModelResponse {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  model_version: number;
  target_column: string;
  features: string[];
  problem_type: string;
  model_type: string;
  status: string;
  training_config: Record<string, any>;
  evaluation_metrics?: Record<string, any>;
  feature_importances?: Record<string, number>;
  model_size_bytes?: number;
  dataset_quality_score?: number;
  dataset_hash?: string;
  best_score?: number;
  training_log?: { timestamp: string; message: string }[];
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  training_rows?: number;
  testing_rows?: number;
  created_at: string;
}

export interface PredictionResponse {
  prediction: any;
  confidence?: number;
}

export interface PredictionLogResponse {
  id: string;
  model_id: string;
  input_payload: Record<string, any>;
  prediction: string;
  confidence?: number;
  created_at: string;
}

export const mlService = {
  trainModel: async (datasetId: string, params: MLModelTrainRequest): Promise<any> => {
    const res = await apiClient.post(`/ml/train?dataset_id=${datasetId}`, params);
    return res.data;
  },

  listModels: async (datasetId?: string): Promise<MLModelResponse[]> => {
    const url = datasetId ? `/ml?dataset_id=${datasetId}` : '/ml';
    const res = await apiClient.get(url);
    return res.data.data;
  },

  getModelDetails: async (modelId: string): Promise<MLModelResponse> => {
    const res = await apiClient.get(`/ml/${modelId}`);
    return res.data.data;
  },

  makePrediction: async (modelId: string, inputData: Record<string, any>): Promise<PredictionResponse> => {
    const res = await apiClient.post(`/ml/${modelId}/predict`, { input_data: inputData });
    return res.data.data;
  },

  getPredictionHistory: async (modelId: string): Promise<PredictionLogResponse[]> => {
    const res = await apiClient.get(`/ml/${modelId}/history`);
    return res.data.data;
  },

  deleteModel: async (modelId: string): Promise<void> => {
    await apiClient.delete(`/ml/${modelId}`);
  },
};

export default mlService;
