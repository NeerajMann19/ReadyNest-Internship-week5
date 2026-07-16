import { useState, useEffect, useCallback } from 'react';
import { profilingService } from '../services/profiling';
import { DataProfile } from '../types/dataset';

export const useProfile = (datasetId: string | undefined) => {
  const [data, setData] = useState<DataProfile | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const profile = await profilingService.getProfile(datasetId);
      setData(profile);
    } catch (err: any) {
      // 404 is expected if profile hasn't been generated yet
      if (err.response?.status === 404) {
        setData(null);
      } else {
        setError(err.response?.data?.message || 'Failed to fetch dataset profile metrics');
      }
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  const triggerProfile = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);
    try {
      const profile = await profilingService.triggerProfile(datasetId);
      setData(profile);
      return profile;
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to trigger data profiling');
      throw err;
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { data, loading, error, refresh, triggerProfile };
};

export default useProfile;
