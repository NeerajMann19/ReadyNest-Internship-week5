import { apiClient } from '../lib/apiClient';

export const dashboardService = {
  getSummary: async (): Promise<any> => {
    const res = await apiClient.get('/dashboard/summary');
    return res.data.data;
  },
};

export default dashboardService;
