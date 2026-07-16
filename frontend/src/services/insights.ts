import { apiClient } from '../lib/apiClient';
import { AiInsight } from '../types/dataset';

export const insightsService = {
  runInsights: async (id: string): Promise<AiInsight> => {
    const res = await apiClient.post(`/datasets/${id}/insights`);
    return res.data.data;
  },

  getInsights: async (id: string): Promise<AiInsight> => {
    const res = await apiClient.get(`/datasets/${id}/insights`);
    return res.data.data;
  },

  getSummary: async (id: string): Promise<any> => {
    const res = await apiClient.get(`/datasets/${id}/insights/summary`);
    return res.data.data;
  },

  deleteInsights: async (id: string): Promise<void> => {
    await apiClient.delete(`/datasets/${id}/insights`);
  },
};

export default insightsService;
