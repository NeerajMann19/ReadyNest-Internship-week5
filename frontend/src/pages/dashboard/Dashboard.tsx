import React from 'react';
import { useNavigate, Link } from 'react-router-dom';
import useDashboard from '../../hooks/useDashboard';
import { PageContainer, PageHeader } from '../../components/layout/PageContainer';
import { Loader } from '../../components/common/Loader';
import { Card } from '../../components/common/Card';
import { QualityHistoryChart, ReportsDistributionChart } from '../../components/charts/DashboardCharts';

interface KPIResponse {
  total_datasets: number;
  total_versions: number;
  total_storage_bytes: number;
  average_quality_score: number;
}

interface RecentDataset {
  id: string;
  name?: string;
  dataset_name?: string;
  status?: string;
  quality_score?: number;
  version?: number;
  last_updated?: string;
  profile?: {
    quality_score?: number;
  };
  versions?: any[];
}

interface RecentReport {
  id: string;
  dataset_name: string;
  report_type: string;
  status: string;
  file_size: number;
  generated_from_version: number;
  download_url: string;
  created_at: string;
}

interface RecentActivity {
  type: string;
  icon: string;
  color: string;
  dataset_name: string;
  version: number | null;
  title?: string;
  event_type?: string;
  description: string;
  timestamp: string;
}

interface DashboardSummary {
  kpis?: KPIResponse;
  recent_activity?: RecentActivity[];
  recent_datasets?: RecentDataset[];
  recent_cleaning_jobs?: any[];
  recent_insights?: any[];
  recent_reports?: RecentReport[];
}

export const Dashboard: React.FC = () => {
  const { data, loading, error, refresh } = useDashboard();
  const navigate = useNavigate();


  if (loading) {
    return <Loader type="spinner" text="Compiling dashboard telemetry..." />;
  }

  if (error) {
    return (
      <div className="bg-red-950/40 border border-red-500/30 text-red-400 p-6 rounded-2xl flex flex-col space-y-3 max-w-xl mx-auto mt-12">
        <h3 className="font-bold text-lg">Failed to load Dashboard</h3>
        <p className="text-sm">{error}</p>
        <button
          onClick={refresh}
          className="w-fit bg-red-800 hover:bg-red-700 text-white font-medium py-1.5 px-4 rounded-xl text-xs transition active:scale-95"
        >
          Retry Load
        </button>
      </div>
    );
  }

  // Fallbacks if data is empty or naming mismatches
  const summary: DashboardSummary = data || {};
  const kpis = summary.kpis;
  
  const metrics = {
    total_datasets: kpis?.total_datasets ?? 0,
    total_reports: (Array.isArray(summary.recent_reports) ? summary.recent_reports : []).length,
    average_quality_score: kpis?.average_quality_score ?? 100.0,
    active_jobs_count: (Array.isArray(summary.recent_cleaning_jobs) ? summary.recent_cleaning_jobs : []).length,
  };

  const recentDatasets = Array.isArray(summary.recent_datasets) ? summary.recent_datasets : [];
  const recentReports = Array.isArray(summary.recent_reports) ? summary.recent_reports : [];
  const activityTimeline = Array.isArray(summary.recent_activity) ? summary.recent_activity : [];

  // Parse chart data structures defensively
  const qualityHistoryData = recentDatasets.map((d: RecentDataset) => {
    const datasetName = d.name ?? d.dataset_name ?? 'Unnamed';
    const quality = d.quality_score ?? d.profile?.quality_score ?? 100.0;
    return {
      name: typeof datasetName === 'string' ? datasetName.slice(0, 10) : 'Unnamed',
      quality: typeof quality === 'number' ? quality : 0.0,
    };
  }).reverse();

  // Count reports by format defensively
  const reportCounts: Record<string, number> = { PDF: 0, EXCEL: 0, HTML: 0, JSON: 0 };
  recentReports.forEach((r: RecentReport) => {
    if (r && r.report_type) {
      reportCounts[r.report_type] = (reportCounts[r.report_type] || 0) + 1;
    }
  });
  const reportsChartData = Object.keys(reportCounts).map((k) => ({
    name: k,
    count: reportCounts[k],
  }));

  return (
    <PageContainer>
      <PageHeader
        title="Dashboard Console"
        subtitle="Aggregated system status, metrics, and quality timelines"
        actions={
          <button
            onClick={() => navigate('/datasets/import')}
            className="flex items-center space-x-2 bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold px-4 py-2.5 rounded-xl transition duration-150 active:scale-95 shadow-lg shadow-cyan-950/20"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Import Dataset</span>
          </button>
        }
      />

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Metric 1 */}
        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-cyan-950 border border-cyan-500/30 rounded-xl flex items-center justify-center text-cyan-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Datasets</p>
            <h2 className="text-2xl font-black text-white">{metrics.total_datasets}</h2>
          </div>
        </Card>

        {/* Metric 2 */}
        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-blue-950 border border-blue-500/30 rounded-xl flex items-center justify-center text-blue-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Total Reports</p>
            <h2 className="text-2xl font-black text-white">{metrics.total_reports}</h2>
          </div>
        </Card>

        {/* Metric 3 */}
        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-emerald-950 border border-emerald-500/30 rounded-xl flex items-center justify-center text-emerald-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Avg Quality Score</p>
            <h2 className="text-2xl font-black text-white">
              {metrics.average_quality_score ? `${metrics.average_quality_score.toFixed(1)}%` : '0.0%'}
            </h2>
          </div>
        </Card>

        {/* Metric 4 */}
        <Card className="flex items-center space-x-4">
          <div className="w-12 h-12 bg-amber-950 border border-amber-500/30 rounded-xl flex items-center justify-center text-amber-400">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Active Pipeline Jobs</p>
            <h2 className="text-2xl font-black text-white">{metrics.active_jobs_count}</h2>
          </div>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QualityHistoryChart title="Quality Index History (Recent Uploads)" data={qualityHistoryData} />
        <ReportsDistributionChart title="Reports Compilation Output by Format" data={reportsChartData} />
      </div>

      {/* Bottom Lists split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Dataset list */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
            <h3 className="font-bold text-slate-100 text-sm tracking-tight">Recent Datasets Workspace</h3>
            <Link to="/datasets" className="text-xs font-semibold text-cyan-400 hover:text-cyan-300">
              View all
            </Link>
          </div>
          <div className="divide-y divide-slate-800/40">
            {(Array.isArray(recentDatasets) ? recentDatasets : []).slice(0, 5).map((dataset: RecentDataset) => {
              const datasetName = dataset.name ?? dataset.dataset_name ?? 'Unnamed Dataset';
              const quality = dataset.quality_score ?? dataset.profile?.quality_score;
              const statusText = dataset.status ?? 'UPLOADED';
              const versionNum = dataset.version ?? (dataset.versions?.length ?? 1);
              return (
                <div key={dataset.id} className="flex items-center justify-between py-3.5 first:pt-0 last:pb-0">
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-semibold text-slate-200 truncate">{datasetName}</p>
                    <p className="text-xs text-slate-500 truncate">{statusText} • Version {versionNum}</p>
                  </div>
                  <div className="flex items-center space-x-4 pl-4">
                    {quality !== undefined && (
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
                        quality > 80
                          ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                          : quality > 50
                          ? 'bg-amber-950/40 border-amber-500/30 text-amber-400'
                          : 'bg-red-950/40 border-red-500/30 text-red-400'
                      }`}>
                        Score {quality.toFixed(0)}%
                      </span>
                    )}
                    <button
                      onClick={() => navigate(`/datasets/${dataset.id}`)}
                      className="bg-slate-850 hover:bg-slate-800 border border-slate-800 text-slate-300 text-xs px-3 py-1.5 rounded-lg transition"
                    >
                      Workspace
                    </button>
                  </div>
                </div>
              );
            })}
            {(Array.isArray(recentDatasets) ? recentDatasets : []).length === 0 && (
              <p className="text-xs text-slate-500 py-6 text-center">No datasets uploaded yet.</p>
            )}
          </div>
        </div>

        {/* Activity Timeline logs */}
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-800/60 pb-3">
            <h3 className="font-bold text-slate-100 text-sm tracking-tight">Active Activity Feed</h3>
          </div>
          <div className="space-y-4 max-h-[300px] overflow-y-auto pr-1">
            {(Array.isArray(activityTimeline) ? activityTimeline : []).slice(0, 10).map((event: RecentActivity, idx: number) => {
              const eventType = event.title ?? event.event_type ?? event.type ?? 'Activity';
              const description = event.description ?? '';
              const timeString = event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '';
              return (
                <div key={idx} className="flex space-x-3 text-xs">
                  <div className="mt-0.5">
                    <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full"></div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-semibold text-slate-300">{eventType}</p>
                    <p className="text-slate-500 truncate">{description}</p>
                    {timeString && <p className="text-[10px] text-slate-600 mt-0.5">{timeString}</p>}
                  </div>
                </div>
              );
            })}
            {(Array.isArray(activityTimeline) ? activityTimeline : []).length === 0 && (
              <p className="text-xs text-slate-500 py-6 text-center">No recent activities logged.</p>
            )}
          </div>
        </div>
      </div>
    </PageContainer>
  );
};

export default Dashboard;
