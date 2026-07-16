import { useState } from 'react';
import useProfile from '../../hooks/useProfile';
import { Loader } from '../../components/common/Loader';
import { Card } from '../../components/common/Card';
import { Table } from '../../components/common/Table';
import Button from '../../components/common/Button';

interface ProfilingPanelProps {
  datasetId: string;
}

export const ProfilingPanel = ({ datasetId }: ProfilingPanelProps) => {
  const { data: profile, loading, error, refresh, triggerProfile } = useProfile(datasetId);
  const [isProfiling, setIsProfiling] = useState(false);

  const handleProfileTrigger = async () => {
    setIsProfiling(true);
    try {
      await triggerProfile();
      await refresh();
    } catch (err) {
      alert('Profiling failed. Please check the dataset file format.');
    } finally {
      setIsProfiling(false);
    }
  };

  if (loading && !profile) {
    return <Loader type="spinner" text="Parsing column profiling statistics..." />;
  }

  if (error) {
    return <div className="text-red-400 text-xs p-4 bg-red-950/20 border border-red-500/30 rounded-xl">{error}</div>;
  }

  if (!profile) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 bg-amber-950/50 border border-amber-500/30 text-amber-400 rounded-xl flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-slate-200 tracking-tight">Profiling report not found</h3>
          <p className="text-xs text-slate-400 font-medium max-w-sm">
            Data profile is required to calculate cleaning parameters, exploratory distributions, and smart suggestions.
          </p>
        </div>
        <Button onClick={handleProfileTrigger} isLoading={isProfiling} className="font-bold px-6">
          Trigger Data Profiling
        </Button>
      </div>
    );
  }

  const columns = [
    {
      header: 'Column Name',
      render: (row: any) => <code className="text-cyan-400 font-bold text-xs">{row.name}</code>,
    },
    {
      header: 'Data Type',
      render: (row: any) => (
        <span className="text-[10px] font-bold bg-slate-800 px-2 py-0.5 border border-slate-700/50 rounded-md uppercase tracking-wider text-slate-300">
          {row.dtype}
        </span>
      ),
    },
    {
      header: 'Unique Values',
      render: (row: any) => <span className="font-semibold text-slate-200">{row.unique_count}</span>,
    },
    {
      header: 'Missing Cells',
      render: (row: any) => <span className="font-semibold text-slate-200">{row.missing_count}</span>,
    },
    {
      header: 'Null Ratio',
      render: (row: any) => (
        <span className={`text-xs font-semibold ${row.missing_pct > 30 ? 'text-red-400' : 'text-slate-400'}`}>
          {row.missing_pct.toFixed(2)}%
        </span>
      ),
    },
    {
      header: 'Value Profile',
      render: (row: any) => {
        const samples = row.sample_values || [];
        return (
          <span className="text-[11px] text-slate-500 truncate max-w-[200px] block" title={samples.join(', ')}>
            [{samples.slice(0, 3).join(', ')}]
          </span>
        );
      },
    },
  ];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Profiling stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-emerald-950 border border-emerald-500/30 rounded-xl flex items-center justify-center text-emerald-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Quality Score Index</p>
            <h2 className="text-2xl font-black text-white">{profile.quality_score.toFixed(1)}/100</h2>
          </div>
        </Card>

        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-cyan-950 border border-cyan-500/30 rounded-xl flex items-center justify-center text-cyan-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Missing Cells</p>
            <h2 className="text-2xl font-black text-white">{profile.missing_values}</h2>
          </div>
        </Card>

        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-purple-950 border border-purple-500/30 rounded-xl flex items-center justify-center text-purple-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Duplicate Rows</p>
            <h2 className="text-2xl font-black text-white">{profile.duplicate_rows}</h2>
          </div>
        </Card>
      </div>

      {/* Profiling Grid details */}
      <Card
        title="Column Schema Diagnostics"
        subtitle="Detailed metrics for all variables discovered in this version"
        actions={
          <Button
            variant="secondary"
            onClick={handleProfileTrigger}
            isLoading={isProfiling}
            className="text-xs py-1.5 px-3 font-semibold"
          >
            Regenerate Diagnostics
          </Button>
        }
      >
        <Table data={profile.column_summary || []} columns={columns} />
      </Card>
    </div>
  );
};

export default ProfilingPanel;
