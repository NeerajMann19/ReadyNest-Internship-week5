import { useState, useEffect, useCallback } from 'react';
import { insightsService } from '../services/insights';
import { AiInsight } from '../types/dataset';

export const useInsights = (datasetId: string | undefined) => {
  const [data, setData] = useState<AiInsight | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const insights = await insightsService.getInsights(datasetId);
      setData(insights);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setData(null);
      } else {
        setError(err.response?.data?.message || 'Failed to fetch AI Insights observations');
      }
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const runInsights = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const insights = await insightsService.runInsights(datasetId);
      setData(insights);
      return insights;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to run AI Insights model analysis');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const deleteInsights = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      await insightsService.deleteInsights(datasetId);
      setData(null);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to delete AI Insights observations');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh, runInsights, deleteInsights };
};

export default useInsights;
