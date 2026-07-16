import { useState, useEffect, useCallback } from 'react';
import { edaService } from '../services/eda';
import { EdaResult } from '../types/dataset';

export const useEDA = (datasetId: string | undefined) => {
  const [data, setData] = useState<EdaResult | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const eda = await edaService.getEda(datasetId);
      setData(eda);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setData(null);
      } else {
        setError(err.response?.data?.message || 'Failed to fetch EDA statistics');
      }
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const runEda = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const eda = await edaService.runEda(datasetId);
      setData(eda);
      return eda;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to run EDA calculations');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteEda = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      await edaService.deleteEda(datasetId);
      setData(null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete EDA statistics');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh, runEda, deleteEda };
};

export default useEDA;
