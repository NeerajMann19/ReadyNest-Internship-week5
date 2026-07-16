import { useState } from 'react';
import useInsights from '../../hooks/useInsights';
import Loader from '../../components/common/Loader';
import Card from '../../components/common/Card';
import Button from '../../components/common/Button';

interface InsightsPanelProps {
  datasetId: string;
}

export const InsightsPanel = ({ datasetId }: InsightsPanelProps) => {
  const { data: insights, loading, error, refresh, runInsights, deleteInsights } = useInsights(datasetId);
  const [isCalculating, setIsCalculating] = useState(false);

  const handleCalculateInsights = async () => {
    setIsCalculating(true);
    try {
      await runInsights();
      await refresh();
    } catch (err) {
      alert('AI Insights compilation failed.');
    } finally {
      setIsCalculating(false);
    }
  };

  const handleDeleteInsights = async () => {
    if (!window.confirm('Are you sure you want to flush observations?')) return;
    setIsCalculating(true);
    try {
      await deleteInsights();
      await refresh();
    } catch (err) {
      alert('Failed to clear cached insights.');
    } finally {
      setIsCalculating(false);
    }
  };

  if (loading && !insights) {
    return <Loader type="spinner" text="Running rule-based expert engines..." />;
  }

  if (error) {
    return <div className="text-red-400 text-xs p-4 bg-red-950/20 border border-red-500/30 rounded-xl">{error}</div>;
  }

  if (!insights) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4 animate-fade-in">
        <div className="w-12 h-12 bg-indigo-950/50 border border-indigo-500/30 text-indigo-400 rounded-xl flex items-center justify-center animate-pulse">
          <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
          </svg>
        </div>
        <div className="space-y-1">
          <h3 className="font-bold text-slate-200 tracking-tight">AI Insights not generated</h3>
          <p className="text-xs text-slate-400 font-medium max-w-sm">
            Trigger rule-based intelligence systems to extract anomalies, detect data leakage, and resolve schema problems.
          </p>
        </div>
        <Button onClick={handleCalculateInsights} isLoading={isCalculating} className="font-bold px-6">
          Generate AI Insights
        </Button>
      </div>
    );
  }

  const overallHealth = insights.summary_json?.overall_health ?? null;
  const criticalFindingsCount = insights.summary_json?.priority_distribution?.critical ?? 0;
  const highFindingsCount = insights.summary_json?.priority_distribution?.high ?? 0;
  const totalFindingsCount = insights.summary_json?.total_insights_count ?? 0;

  const generalHealthAssessment = overallHealth
    ? `The dataset health is assessed as ${overallHealth}. We identified a total of ${totalFindingsCount} quality anomalies, including ${criticalFindingsCount} critical and ${highFindingsCount} high-priority findings that require immediate cleaning.`
    : 'Assessment unavailable. No health metrics were found in the generated observations.';

  const findings = insights.insights_json || [];

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Overview Metadata */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <Card className="lg:col-span-3 space-y-3 bg-indigo-950/10 border-indigo-500/20">
          <div className="flex items-center space-x-2 text-indigo-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 flex-shrink-0 animate-pulse" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h4 className="font-bold text-xs uppercase tracking-wider">Executive Summary</h4>
          </div>
          <p className="text-sm font-semibold text-slate-200 leading-relaxed">
            {generalHealthAssessment}
          </p>
        </Card>

        <Card className="text-center flex flex-col items-center justify-center space-y-1">
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Critical Findings</p>
          <h2 className="text-3xl font-black text-red-400">{criticalFindingsCount}</h2>
          <Button
            variant="danger"
            onClick={handleDeleteInsights}
            isLoading={isCalculating}
            className="text-[10px] py-1 px-3 mt-2 font-bold"
          >
            Flush Insights
          </Button>
        </Card>
      </div>

      {/* Findings list */}
      <div className="space-y-4">
        <h3 className="font-bold text-slate-100 text-sm tracking-tight border-b border-slate-800 pb-2">
          Discovered Anomalies & Recommendations
        </h3>
        
        {findings.map((item, idx) => (
          <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex flex-col md:flex-row gap-4 items-start transition hover:border-slate-700">
            {/* Severity Tag column */}
            <div className="flex flex-row md:flex-col items-center gap-2 md:items-start justify-between min-w-[120px]">
              <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${
                item.severity === 'HIGH'
                  ? 'bg-red-950/40 border-red-500/30 text-red-400'
                  : item.severity === 'MEDIUM'
                  ? 'bg-amber-950/40 border-amber-500/30 text-amber-400'
                  : 'bg-blue-950/40 border-blue-500/30 text-blue-400'
              }`}>
                {item.severity} severity
              </span>
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider md:mt-1">
                Category: {item.category}
              </span>
            </div>

            {/* Content Details */}
            <div className="flex-1 space-y-2">
              <h4 className="font-bold text-slate-200 text-sm leading-snug">{item.observation}</h4>
              
              <div className="bg-slate-950 border border-slate-850 p-3 rounded-lg text-xs leading-relaxed space-y-1 font-medium">
                <p className="text-slate-300">
                  <span className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mr-1">Root Cause:</span>
                  {item.root_cause}
                </p>
                <p className="text-cyan-400 mt-1">
                  <span className="text-slate-500 font-bold uppercase tracking-wider text-[10px] mr-1">Recommendation:</span>
                  {item.recommendation}
                </p>
              </div>
            </div>

            {/* Actionability Badge */}
            <div className="bg-slate-950 border border-slate-850 px-3 py-2 rounded-xl text-center self-stretch md:self-auto flex flex-col items-center justify-center min-w-[100px]">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Actionability</span>
              <span className="text-lg font-black text-cyan-400">{(item.actionability * 100).toFixed(0)}%</span>
            </div>
          </div>
        ))}

        {findings.length === 0 && (
          <p className="text-xs text-slate-500 font-medium italic text-center py-6">
            No specific anomalies flagged for this version. The dataset is general and ready.
          </p>
        )}
      </div>
    </div>
  );
};

export default InsightsPanel;
