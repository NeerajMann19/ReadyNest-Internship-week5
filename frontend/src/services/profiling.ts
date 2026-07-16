import { apiClient } from '../lib/apiClient';
import { DataProfile } from '../types/dataset';

export const profilingService = {
  triggerProfile: async (id: string): Promise<DataProfile> => {
    const res = await apiClient.post(`/datasets/${id}/profile`);
    return res.data.data;
  },

  getProfile: async (id: string): Promise<DataProfile> => {
    const res = await apiClient.get(`/datasets/${id}/profile`);
    return res.data.data;
  },
};

export default profilingService;
