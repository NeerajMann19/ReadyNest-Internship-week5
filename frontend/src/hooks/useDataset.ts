import { useState, useEffect, useCallback } from 'react';
import { datasetService } from '../services/dataset';
import { Dataset, DatasetDetailResponse } from '../types/dataset';

export const useDatasetList = (initialParams: {
  page?: number;
  page_size?: number;
  search?: string;
  status?: string;
  sort?: string;
} = {}) => {
  const [data, setData] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [params, setParams] = useState(initialParams);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const list = await datasetService.list(params);
      setData(list);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch datasets list');
    } finally {
      setLoading(false);
    }
  }, [params]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh, params, setParams };
};

export const useDatasetDetail = (id: string | undefined) => {
  const [data, setData] = useState<DatasetDetailResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const detail = await datasetService.get(id);
      setData(detail);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to fetch dataset workspace details');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh };
};
