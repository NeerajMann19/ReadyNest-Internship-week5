import { apiClient } from '../lib/apiClient';
import { Report, DatasetCompareResult } from '../types/report';

export const reportsService = {
  generate: async (datasetId: string, reportType: 'PDF' | 'EXCEL' | 'HTML' | 'JSON'): Promise<Report> => {
    const res = await apiClient.post(`/reports/generate`, null, {
      params: {
        dataset_id: datasetId,
        report_type: reportType,
      },
    });
    return res.data.data;
  },

  list: async (params: {
    page?: number;
    limit?: number;
    search?: string;
    status?: string;
    format?: string;
    dataset_id?: string;
    created_before?: string;
    created_after?: string;
    sort?: string;
  }): Promise<Report[]> => {
    const res = await apiClient.get('/reports', { params });
    return res.data.data;
  },

  get: async (id: string): Promise<Report> => {
    const res = await apiClient.get(`/reports/${id}`);
    return res.data.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`/reports/${id}`);
  },

  compare: async (datasetId: string, v1: number, v2: number): Promise<DatasetCompareResult> => {
    const res = await apiClient.get(`/datasets/${datasetId}/compare`, {
      params: { v1, v2 },
    });
    return res.data.data;
  },

  getDownloadUrl: (id: string): string => {
    return `${apiClient.defaults.baseURL}/reports/${id}/download`;
  },

  download: async (id: string, defaultFilename: string): Promise<void> => {
    try {
      const res = await apiClient.get(`/reports/${id}/download`, {
        responseType: 'blob',
      });
      
      let filename = defaultFilename;
      const disposition = res.headers['content-disposition'];
      if (typeof disposition === 'string' && disposition.includes('attachment')) {
        const filenameRegex = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/;
        const matches = filenameRegex.exec(disposition);
        if (matches != null && matches[1]) {
          filename = matches[1].replace(/['"]/g, '');
        }
      }
      
      let contentType = 'application/octet-stream';
      const rawContentType = res.headers['content-type'];
      if (typeof rawContentType === 'string') {
        contentType = rawContentType;
      }
      
      const blob = new Blob([res.data], { type: contentType });
      const downloadUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      
      setTimeout(() => {
        link.remove();
        window.URL.revokeObjectURL(downloadUrl);
      }, 100);
    } catch (err: any) {
      console.error('Failed to download report', err);
      alert(err.response?.data?.message || 'Failed to download report file. Please verify your connection.');
      throw err;
    }
  },
};

export default reportsService;
