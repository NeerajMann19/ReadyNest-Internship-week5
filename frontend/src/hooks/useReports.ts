import { useState, useEffect, useCallback } from 'react';
import { reportsService } from '../services/reports';
import { Report } from '../types/report';

export const useReports = (initialParams: {
  page?: number;
  limit?: number;
  search?: string;
  status?: string;
  format?: string;
  dataset_id?: string;
  created_before?: string;
  created_after?: string;
  sort?: string;
} = {}) => {
  const [data, setData] = useState<Report[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState(initialParams);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await reportsService.list(params);
      setData(list);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch reports management list');
    } finally {
      setLoading(false);
    }
  }, [params]);

  const generateReport = async (datasetId: string, format: 'PDF' | 'EXCEL' | 'HTML' | 'JSON') => {
    setLoading(true);
    setError(null);
    try {
      const newReport = await reportsService.generate(datasetId, format);
      await refresh();
      return newReport;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to compile analytical report');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteReport = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      await reportsService.delete(id);
      await refresh();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete report file');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh, generateReport, deleteReport, params, setParams };
};

export default useReports;
