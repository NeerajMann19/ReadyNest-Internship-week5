import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { useDatasetDetail } from '../../hooks/useDataset';
import { PageContainer, PageHeader } from '../../components/layout/PageContainer';
import Loader from '../../components/common/Loader';
import Button from '../../components/common/Button';

// Import Sub Panels
import PreviewPanel from './PreviewPanel';
import ProfilingPanel from './ProfilingPanel';
import CleaningPanel from './CleaningPanel';
import EdaPanel from './EdaPanel';
import InsightsPanel from './InsightsPanel';
import ReportsPanel from './ReportsPanel';
import MlPanel from './MlPanel';

export const DatasetDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const location = useLocation();
  const { data: dataset, loading, error, refresh } = useDatasetDetail(id);

  // Sync active tab state from URL sub-paths
  const [activeTab, setActiveTab] = useState('preview');

  useEffect(() => {
    const pathParts = location.pathname.split('/');
    const lastPart = pathParts[pathParts.length - 1];
    if (['preview', 'profile', 'clean', 'eda', 'insights', 'reports', 'ml'].includes(lastPart)) {
      setActiveTab(lastPart);
    } else {
      setActiveTab('preview');
    }
  }, [location]);

  const handleTabChange = (tabName: string) => {
    setActiveTab(tabName);
    navigate(`/datasets/${id}/${tabName}`);
  };

  if (loading) {
    return <Loader type="spinner" text="Mounting dataset workspace environment..." />;
  }

  if (error || !dataset) {
    return (
      <div className="bg-red-950/40 border border-red-500/30 text-red-400 p-6 rounded-2xl flex flex-col space-y-3 max-w-xl mx-auto mt-12">
        <h3 className="font-bold text-lg">Workspace Error</h3>
        <p className="text-sm">{error || 'Dataset workspace not found.'}</p>
        <Button onClick={() => navigate('/datasets')} className="w-fit">
          Back to Workspaces
        </Button>
      </div>
    );
  }

  // Retrieve current active version number
  const currentVersion = dataset.versions.find((v) => v.is_current);
  const versionNum = currentVersion?.version_number || 1;

  // Retrieve column names from profile (or fall back to empty array)
  const columnsList = dataset.profile?.column_summary?.map((col) => col.name) || [];

  const tabItems = [
    { id: 'preview', label: 'Preview & Schema' },
    { id: 'profile', label: 'Profiling Stats' },
    { id: 'clean', label: 'Smart Cleaning' },
    { id: 'eda', label: 'Exploratory EDA' },
    { id: 'insights', label: 'AI Insights' },
    { id: 'reports', label: 'Reports Export' },
    { id: 'ml', label: 'Predictive ML' },
  ];

  return (
    <PageContainer>
      {/* Detail header */}
      <PageHeader
        title={dataset.dataset_name}
        subtitle={`${dataset.original_filename} • Active Version ${versionNum} (${dataset.source_type})`}
        actions={
          <div className="flex items-center space-x-2">
            {dataset.versions.length > 1 && (
              <Button
                variant="secondary"
                onClick={() => navigate(`/datasets/${id}/compare?v1=1&v2=${dataset.versions.length}`)}
                className="text-xs py-2 px-3 font-semibold"
              >
                Compare Versions
              </Button>
            )}
            <Button
              variant="ghost"
              onClick={() => navigate('/datasets')}
              className="text-xs py-2 px-3 font-semibold"
            >
              Back to Workspaces
            </Button>
          </div>
        }
      />

      {/* Tabs navigation bar */}
      <div className="border-b border-slate-800 flex space-x-6 overflow-x-auto pb-px">
        {tabItems.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => handleTabChange(tab.id)}
              className={`text-sm font-semibold py-3 border-b-2 transition outline-none whitespace-nowrap ${
                isActive
                  ? 'border-cyan-500 text-cyan-400 font-bold'
                  : 'border-transparent text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Active Tab Panel */}
      <div className="pt-4">
        {activeTab === 'preview' && (
          <PreviewPanel datasetId={dataset.id} versionNumber={versionNum} />
        )}
        {activeTab === 'profile' && <ProfilingPanel datasetId={dataset.id} />}
        {activeTab === 'clean' && (
          <CleaningPanel
            datasetId={dataset.id}
            onCleaningSuccess={() => {
              refresh();
              handleTabChange('profile');
            }}
            availableColumns={columnsList}
          />
        )}
        {activeTab === 'eda' && <EdaPanel datasetId={dataset.id} />}
        {activeTab === 'insights' && <InsightsPanel datasetId={dataset.id} />}
        {activeTab === 'reports' && <ReportsPanel datasetId={dataset.id} />}
        {activeTab === 'ml' && <MlPanel datasetId={dataset.id} />}
      </div>
    </PageContainer>
  );
};

export default DatasetDetail;
