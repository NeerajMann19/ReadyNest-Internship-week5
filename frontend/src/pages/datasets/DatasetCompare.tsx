import React, { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import { reportsService } from '../../services/reports';
import { datasetService } from '../../services/dataset';
import { PageContainer, PageHeader } from '../../components/layout/PageContainer';
import { Loader } from '../../components/common/Loader';
import { Card } from '../../components/common/Card';
import Button from '../../components/common/Button';
import { DatasetCompareResult } from '../../types/report';

export const DatasetCompare: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();

  // Parse query params v1 and v2
  const query = new URLSearchParams(location.search);
  const v1 = parseInt(query.get('v1') || '1', 10);
  const v2 = parseInt(query.get('v2') || '2', 10);

  const [compareData, setCompareData] = useState<DatasetCompareResult | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchComparison = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const [comp, dataset] = await Promise.all([
          reportsService.compare(id, v1, v2),
          datasetService.get(id),
        ]);
        setCompareData(comp);
        setDatasetName(dataset.dataset_name);
      } catch (err: any) {
        setError(err.response?.data?.message || 'Failed to calculate side-by-side comparison.');
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [id, v1, v2]);

  if (loading) {
    return <Loader type="spinner" text="Calculating row differentials and quality improvements..." />;
  }

  if (error || !compareData) {
    return (
      <div className="bg-red-950/40 border border-red-500/30 text-red-400 p-6 rounded-2xl flex flex-col space-y-3 max-w-xl mx-auto mt-12">
        <h3 className="font-bold text-lg">Comparison Error</h3>
        <p className="text-sm">{error || 'Could not load comparative version metrics.'}</p>
        <Button onClick={() => navigate(`/datasets/${id}`)} className="w-fit">
          Back to Workspace
        </Button>
      </div>
    );
  }

  const diff = compareData.version_difference;
  const colsAdded = compareData.columns_added || [];
  const colsRemoved = compareData.columns_removed || [];
  const typeChanges = compareData.datatype_changes || {};
  const operations = compareData.cleaning_operations_applied || [];
  const insightsDiff = compareData.insights_difference || {
    v1_insights_count: 0,
    v2_insights_count: 0,
    new_insights: [],
    resolved_insights: [],
  };

  return (
    <PageContainer>
      <PageHeader
        title={`Compare Versions — ${datasetName}`}
        subtitle={`Audit changes and metadata updates between Version ${v1} and Version ${v2}`}
        actions={
          <Button
            variant="secondary"
            onClick={() => navigate(`/datasets/${id}`)}
            className="text-xs py-2 px-3 font-semibold"
          >
            Back to Workspace
          </Button>
        }
      />

      {/* Metrics Cards comparison layout */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <Card className="text-center space-y-1">
          <p className="text-xs text-slate-400 font-semibold uppercase">Row Count Delta</p>
          <h2 className="text-2xl font-black text-white">
            {diff.rows_difference >= 0 ? `+${diff.rows_difference}` : diff.rows_difference}
          </h2>
          <p className="text-[10px] text-slate-500 font-medium">Rows affected during cleanups</p>
        </Card>

        {/* Metric 2 */}
        <Card className="text-center space-y-1">
          <p className="text-xs text-slate-400 font-semibold uppercase">Quality Score Offset</p>
          <h2 className={`text-2xl font-black ${diff.quality_score_improvement >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
            {diff.quality_score_improvement >= 0 ? `+${diff.quality_score_improvement.toFixed(1)}%` : `${diff.quality_score_improvement.toFixed(1)}%`}
          </h2>
          <p className="text-[10px] text-slate-500 font-medium">Aggregate score index gain</p>
        </Card>

        {/* Metric 3 */}
        <Card className="text-center space-y-1">
          <p className="text-xs text-slate-400 font-semibold uppercase">Rows Modified</p>
          <h2 className="text-2xl font-black text-cyan-400">{diff.changed_rows}</h2>
          <p className="text-[10px] text-slate-500 font-medium">Cells mutated or filled</p>
        </Card>

        {/* Metric 4 */}
        <Card className="text-center space-y-1">
          <p className="text-xs text-slate-400 font-semibold uppercase">Removed Rows</p>
          <h2 className="text-2xl font-black text-red-400">{diff.removed_rows}</h2>
          <p className="text-[10px] text-slate-500 font-medium">Duplicates or outlier rows dropped</p>
        </Card>
      </div>

      {/* Main split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Columns & Data Type changes */}
        <div className="space-y-6">
          <Card title="Variable Schema Changes" subtitle="Audit structural adjustments, column additions, and type casts">
            <div className="space-y-4 text-xs font-semibold">
              {/* Added cols */}
              {colsAdded.length > 0 && (
                <div className="space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Added Columns</span>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {colsAdded.map((c) => (
                      <span key={c} className="bg-emerald-950/40 border border-emerald-500/30 text-emerald-400 px-2 py-0.5 rounded text-[10px]">
                        +{c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Removed cols */}
              {colsRemoved.length > 0 && (
                <div className="space-y-1">
                  <span className="text-slate-500 uppercase text-[10px]">Removed Columns</span>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {colsRemoved.map((c) => (
                      <span key={c} className="bg-red-950/40 border border-red-500/30 text-red-400 px-2 py-0.5 rounded text-[10px]">
                        -{c}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Datatype shifts */}
              {Object.keys(typeChanges).length > 0 ? (
                <div className="space-y-2 border-t border-slate-800/60 pt-3">
                  <span className="text-slate-500 uppercase text-[10px] block">Datatype Conversions</span>
                  <div className="overflow-hidden border border-slate-800 rounded-lg">
                    <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300 font-medium">
                      <thead className="bg-slate-900 text-slate-200">
                        <tr>
                          <th className="px-4 py-2">Column</th>
                          <th className="px-4 py-2">Original Type</th>
                          <th className="px-4 py-2">New Type</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 font-mono text-[10px]">
                        {Object.keys(typeChanges).map((col) => (
                          <tr key={col}>
                            <td className="px-4 py-2 text-cyan-400 font-bold">{col}</td>
                            <td className="px-4 py-2 text-slate-400">{typeChanges[col].v1_type}</td>
                            <td className="px-4 py-2 text-emerald-400 font-bold">{typeChanges[col].v2_type}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : null}

              {colsAdded.length === 0 && colsRemoved.length === 0 && Object.keys(typeChanges).length === 0 && (
                <p className="text-xs text-slate-500 font-medium italic py-4 text-center">
                  No structural column changes or datatype conversions recorded.
                </p>
              )}
            </div>
          </Card>

          {/* AI Insights offsets */}
          <Card title="Expert System Observation Shifts" subtitle="Anomalies introduced, resolved, or handled between versions">
            <div className="space-y-4 text-xs font-semibold">
              <div className="flex justify-between border-b border-slate-800/60 pb-2">
                <span className="text-slate-400">Version {v1} Insights Count</span>
                <span className="text-slate-200">{insightsDiff.v1_insights_count}</span>
              </div>
              <div className="flex justify-between border-b border-slate-800/60 pb-2">
                <span className="text-slate-400">Version {v2} Insights Count</span>
                <span className="text-slate-200">{insightsDiff.v2_insights_count}</span>
              </div>

              {/* Resolved anomalies list */}
              {insightsDiff.resolved_insights && insightsDiff.resolved_insights.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <span className="text-emerald-400 uppercase text-[10px] block font-bold">Resolved Anomalies</span>
                  <div className="space-y-1 pl-2">
                    {insightsDiff.resolved_insights.map((res, i) => (
                      <p key={i} className="text-slate-300 font-medium">✓ {res}</p>
                    ))}
                  </div>
                </div>
              )}

              {/* Newly discovered anomalies list */}
              {insightsDiff.new_insights && insightsDiff.new_insights.length > 0 && (
                <div className="space-y-1.5 border-t border-slate-800/60 pt-3">
                  <span className="text-red-400 uppercase text-[10px] block font-bold">Newly Discovered Anomalies</span>
                  <div className="space-y-1 pl-2">
                    {insightsDiff.new_insights.map((newIns, i) => (
                      <p key={i} className="text-slate-300 font-medium">⚠ {newIns}</p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Cleaning Pipeline Lineage */}
        <Card title="Cleaning Rules History" subtitle="Lineage log of transformations applied to construct Version {v2}">
          <div className="relative border-l border-slate-800 pl-4 ml-2 space-y-6">
            {operations.map((op: any, index: number) => (
              <div key={index} className="relative">
                {/* Node icon circle */}
                <div className="absolute -left-[21px] top-0.5 w-3.5 h-3.5 bg-cyan-500 rounded-full border-2 border-slate-900 shadow"></div>
                <div className="space-y-1">
                  <span className="text-xs font-bold text-slate-100 uppercase tracking-wide block">
                    {op.type?.replace('_', ' ')}
                  </span>
                  {op.column && (
                    <p className="text-xs text-slate-400 font-medium">
                      Applied on variable <code className="text-cyan-400 font-bold">{op.column}</code>
                    </p>
                  )}
                  {op.parameters && (
                    <div className="bg-slate-950 border border-slate-850 p-2.5 rounded-lg text-[10px] font-mono text-slate-400 max-w-sm mt-1.5">
                      {JSON.stringify(op.parameters, null, 2)}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {operations.length === 0 && (
              <div className="relative">
                <div className="absolute -left-[20px] top-0.5 w-3 h-3 bg-slate-700 rounded-full"></div>
                <p className="text-xs text-slate-500 font-medium italic pl-1">
                  No automated cleaning rules applied directly.
                </p>
              </div>
            )}
          </div>
        </Card>
      </div>
    </PageContainer>
  );
};

export default DatasetCompare;
