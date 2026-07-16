import { apiClient } from '../lib/apiClient';
import { EdaResult } from '../types/dataset';

export const edaService = {
  runEda: async (id: string): Promise<EdaResult> => {
    const res = await apiClient.post(`/datasets/${id}/eda`);
    return res.data.data;
  },

  getEda: async (id: string): Promise<EdaResult> => {
    const res = await apiClient.get(`/datasets/${id}/eda`);
    return res.data.data;
  },

  deleteEda: async (id: string): Promise<void> => {
    await apiClient.delete(`/datasets/${id}/eda`);
  },
};

export default edaService;
