import { useState } from 'react';
import useEDA from '../../hooks/useEDA';
import Loader from '../../components/common/Loader';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';

interface EdaPanelProps {
  datasetId: string;
}

export const EdaPanel = ({ datasetId }: EdaPanelProps) => {
  const { data: eda, loading, error, refresh, runEda, deleteEda } = useEDA(datasetId);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleCalculateEda = async () => {
    setIsCalculating(true);
    try {
      await runEda();
      await refresh();
    } catch (err) {
      alert('EDA calculation failed. Please check column data types.');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleDeleteEda = async () => {
    if (!window.confirm('Are you sure you want to flush calculations?')) return;
    setIsCalculating(true);
    try {
      await deleteEda();
      await refresh();
    } catch (err) {
      alert('Failed to clear cached computations.');
    } finally {
      setIsCalculating(false);
    }
  };

  if (loading && !eda) {
    return <Loader type="spinner" text="Resolving exploratory analysis matrices..." />;
  }

  if (error) {
    return <div className="text-red-400 text-xs p-4 bg-red-950/20 border border-red-500/30 rounded-xl">{error}</div>;
  }

  if (!eda) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4 animate-fade-in">
        <div className="w-12 h-12 bg-cyan-950/50 border border-cyan-500/30 text-cyan-400 rounded-xl flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-slate-200 tracking-tight">EDA calculations not computed</h3>
          <p className="text-xs text-slate-400 font-medium max-w-sm">
            Compute Pearson correlation scores and descriptive statistical distributions for numeric columns.
          </p>
        </div>
        <Button onClick={handleCalculateEda} isLoading={isCalculating} className="font-bold px-6">
          Compute Exploratory Analysis (EDA)
        </Button>
      </div>
    );
  }

  const numericStats = eda.statistics_json?.numeric_analysis || {};
  const numericCols = Object.keys(numericStats);

  // Reconstruct correlation matrix from flat correlation list
  const correlationMatrix: Record<string, Record<string, number | null>> = {};
  
  // Initialize identity diagonal and default below-threshold cells to null
  numericCols.forEach((rowCol) => {
    correlationMatrix[rowCol] = {};
    numericCols.forEach((col) => {
      correlationMatrix[rowCol][col] = rowCol === col ? 1.0 : null;
    });
  });

  const flatCorrelations = eda.charts_json?.correlations || [];
  if (Array.isArray(flatCorrelations)) {
    flatCorrelations.forEach((c: any) => {
      const { column1, column2, coefficient } = c;
      if (correlationMatrix[column1] && correlationMatrix[column2]) {
        correlationMatrix[column1][column2] = coefficient;
        correlationMatrix[column2][column1] = coefficient;
      }
    });
  }

  // Helper to color cells based on Pearson coefficient (-1 to 1)
  const getCellBgColor = (val: number | null) => {
    if (val === null) return 'rgba(30, 41, 59, 0.4)'; // Neutral dark gray for below threshold
    if (val === 1) return 'rgba(6, 182, 212, 0.4)'; // Self correlation
    const absVal = Math.abs(val);
    if (val > 0) {
      return `rgba(6, 182, 212, ${absVal * 0.25})`; // cyan scale
    }
    return `rgba(239, 68, 68, ${absVal * 0.25})`; // red scale
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Action Header */}
      <div className="flex justify-between items-center bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <span className="text-xs text-slate-400 font-semibold uppercase">
          Calculated in {eda.execution_time_ms}ms
        </span>
        <Button
          variant="danger"
          onClick={handleDeleteEda}
          isLoading={isCalculating}
          className="text-xs py-1.5 px-3 font-semibold"
        >
          Flush Calculations
        </Button>
      </div>

      {/* Correlation Matrix Heatmap */}
      {numericCols.length > 1 && (
        <Card title="Pearson Correlation Heatmap" subtitle="Strength and direction of relationships between numeric variables (values < 0.3 rendered as —)">
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="min-w-full divide-y divide-slate-800 text-left text-xs font-semibold">
              <thead className="bg-slate-900 text-slate-200">
                <tr>
                  <th className="px-4 py-3 border-r border-slate-800">Variable</th>
                  {numericCols.map((col) => (
                    <th key={col} className="px-4 py-3 text-center border-r border-slate-800 whitespace-nowrap">
                      {col.slice(0, 12)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 font-mono text-[11px] text-slate-200">
                {numericCols.map((rowCol) => (
                  <tr key={rowCol} className="hover:bg-slate-850">
                    <td className="px-4 py-3 font-bold bg-slate-900 border-r border-slate-800 whitespace-nowrap">
                      {rowCol}
                    </td>
                    {numericCols.map((col) => {
                      const coeff = correlationMatrix[rowCol]?.[col] ?? null;
                      return (
                        <td
                          key={col}
                          style={{ backgroundColor: getCellBgColor(coeff) }}
                          className="px-4 py-3 text-center border-r border-slate-800 font-bold whitespace-nowrap text-slate-300"
                          title={coeff !== null ? `${rowCol} vs ${col}: ${coeff.toFixed(4)}` : `${rowCol} vs ${col}: Correlation below threshold (< 0.3)`}
                        >
                          {coeff !== null ? coeff.toFixed(3) : '—'}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Numerical Analysis Metrics */}
      {numericCols.length > 0 && (
        <Card title="Numerical Descriptive Metrics" subtitle="Full statistics distributions calculated for continuous scales">
          <div className="overflow-x-auto border border-slate-800 rounded-xl">
            <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300 font-semibold">
              <thead className="bg-slate-900 text-slate-200">
                <tr>
                  <th className="px-6 py-3.5">Column</th>
                  <th className="px-6 py-3.5">Mean</th>
                  <th className="px-6 py-3.5">Median</th>
                  <th className="px-6 py-3.5">Std Dev</th>
                  <th className="px-6 py-3.5">Min</th>
                  <th className="px-6 py-3.5">Max</th>
                  <th className="px-6 py-3.5">Skewness</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-[11px]">
                {numericCols.map((col) => {
                  const stats = numericStats[col] || {};
                  return (
                    <tr key={col} className="hover:bg-slate-800/20">
                      <td className="px-6 py-3 font-bold text-cyan-400">{col}</td>
                      <td className="px-6 py-3 text-slate-200">{stats.mean?.toFixed(4) ?? '0.0000'}</td>
                      <td className="px-6 py-3 text-slate-200">{stats.median?.toFixed(4) ?? '0.0000'}</td>
                      <td className="px-6 py-3 text-slate-200">{stats.std?.toFixed(4) ?? '0.0000'}</td>
                      <td className="px-6 py-3 text-slate-250">{stats.min?.toFixed(4) ?? '0.0000'}</td>
                      <td className="px-6 py-3 text-slate-250">{stats.max?.toFixed(4) ?? '0.0000'}</td>
                      <td className={`px-6 py-3 font-bold ${Math.abs(stats.skewness || 0) > 1 ? 'text-amber-400' : 'text-slate-400'}`}>
                        {stats.skewness?.toFixed(3) ?? '0.000'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};

export default EdaPanel;
