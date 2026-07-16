import { apiClient } from '../lib/apiClient';
import { Dataset, DatasetDetailResponse } from '../types/dataset';

export const datasetService = {
  list: async (params: {
    page?: number;
    page_size?: number;
    search?: string;
    status?: string;
    sort?: string;
    created_before?: string;
    created_after?: string;
  }): Promise<Dataset[]> => {
    const res = await apiClient.get('/datasets', { params });
    return res.data.data;
  },

  get: async (id: string): Promise<DatasetDetailResponse> => {
    const res = await apiClient.get(`/datasets/${id}`);
    return res.data.data;
  },

  upload: async (file: File, datasetName: string, description?: string): Promise<DatasetDetailResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('dataset_name', datasetName);
    if (description) {
      formData.append('description', description);
    }
    const res = await apiClient.post('/datasets', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data.data;
  },

  preview: async (
    id: string,
    params: {
      page?: number;
      page_size?: number;
      sort?: string;
      filter?: string;
    }
  ): Promise<any> => {
    const res = await apiClient.get(`/datasets/${id}/preview`, { params });
    return res.data.data;
  },

  bulkDelete: async (ids: string[]): Promise<{ deleted: number; failed: number }> => {
    const res = await apiClient.post('/datasets/bulk-delete', { ids });
    return res.data.data;
  },

  getDownloadUrl: (id: string): string => {
    return `${apiClient.defaults.baseURL}/datasets/${id}/download`;
  },
};

export default datasetService;
