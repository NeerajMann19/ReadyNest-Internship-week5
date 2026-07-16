import { apiClient } from '../lib/apiClient';
import { DatasetDetailResponse } from '../types/dataset';

export interface CleaningOperation {
  type: string;
  column?: string;
  parameters?: Record<string, any>;
}

export const cleaningService = {
  preview: async (id: string, operations: CleaningOperation[]): Promise<any> => {
    const res = await apiClient.post(`/datasets/${id}/clean/preview`, { operations });
    return res.data.data;
  },

  apply: async (id: string, operations: CleaningOperation[]): Promise<DatasetDetailResponse> => {
    const res = await apiClient.post(`/datasets/${id}/clean`, { operations });
    return res.data.data;
  },
};

export default cleaningService;
