import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDatasetList } from '../../hooks/useDataset';
import { datasetService } from '../../services/dataset';
import { PageContainer, PageHeader, EmptyState, ActionBar } from '../../components/layout/PageContainer';
import { Loader } from '../../components/common/Loader';
import { Table } from '../../components/common/Table';
import Button from '../../components/common/Button';

export const DatasetList: React.FC = () => {
  const navigate = useNavigate();
  const { data: datasets, loading, refresh, params, setParams } = useDatasetList({
    page: 1,
    page_size: 20,
  });

  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);

  // Search input state
  const [searchInput, setSearchInput] = useState(params.search || '');

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setParams((prev) => ({ ...prev, search: searchInput }));
  };

  const handleClearSearch = () => {
    setSearchInput('');
    setParams((prev) => ({ ...prev, search: undefined }));
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setParams((prev) => ({ ...prev, sort: e.target.value || undefined }));
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(datasets.map((d) => d.id));
    } else {
      setSelectedIds([]);
    }
  };

  const handleSelectOne = (id: string, checked: boolean) => {
    if (checked) {
      setSelectedIds((prev) => [...prev, id]);
    } else {
      setSelectedIds((prev) => prev.filter((i) => i !== id));
    }
  };

  const handleBulkDelete = async () => {
    if (selectedIds.length === 0) return;
    if (!window.confirm(`Are you sure you want to delete ${selectedIds.length} datasets?`)) return;

    setIsDeleting(true);
    try {
      await datasetService.bulkDelete(selectedIds);
      setSelectedIds([]);
      refresh();
    } catch (err) {
      alert('Failed to delete datasets. Please try again.');
    } finally {
      setIsDeleting(false);
    }
  };

  if (loading && datasets.length === 0) {
    return <Loader type="spinner" text="Resolving dataset workspaces..." />;
  }

  const columns = [
    {
      header: (
        <input
          type="checkbox"
          checked={datasets.length > 0 && selectedIds.length === datasets.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
          className="rounded bg-slate-950 border-slate-800 focus:ring-cyan-500 text-cyan-500 w-4 h-4 cursor-pointer"
        />
      ),
      render: (row: any) => (
        <input
          type="checkbox"
          checked={selectedIds.includes(row.id)}
          onChange={(e) => handleSelectOne(row.id, e.target.checked)}
          onClick={(e) => e.stopPropagation()}
          className="rounded bg-slate-950 border-slate-800 focus:ring-cyan-500 text-cyan-500 w-4 h-4 cursor-pointer"
        />
      ),
      className: 'w-10 px-4',
    },
    {
      header: 'Workspace Name',
      render: (row: any) => (
        <div className="flex flex-col min-w-[200px]">
          <span className="font-bold text-slate-100 text-sm hover:text-cyan-400 transition cursor-pointer" onClick={() => navigate(`/datasets/${row.id}`)}>
            {row.dataset_name}
          </span>
          <span className="text-xs text-slate-500 font-medium">{row.original_filename}</span>
        </div>
      ),
    },
    {
      header: 'Source',
      render: (row: any) => (
        <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-300 border border-slate-700/50 uppercase">
          {row.source_type}
        </span>
      ),
    },
    {
      header: 'Quality Score',
      render: (row: any) => {
        const score = row.profile?.quality_score;
        if (score === undefined || score === null) {
          return <span className="text-xs text-slate-500 font-medium italic">Unprofiled</span>;
        }
        return (
          <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
            score > 80
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
              : score > 50
              ? 'bg-amber-950/40 border-amber-500/30 text-amber-400'
              : 'bg-red-950/40 border-red-500/30 text-red-400'
          }`}>
            {score.toFixed(1)}%
          </span>
        );
      },
    },
    {
      header: 'Import Date',
      render: (row: any) => (
        <span className="text-xs text-slate-400 font-medium">
          {new Date(row.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row: any) => (
        <div className="flex items-center space-x-2">
          <Button
            variant="secondary"
            onClick={() => navigate(`/datasets/${row.id}`)}
            className="py-1 px-3 text-xs"
          >
            Workspace
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Datasets Workspaces"
        subtitle="Manage uploaded files, data profiles, and data quality metrics"
        actions={
          <Button
            onClick={() => navigate('/datasets/import')}
            className="flex items-center space-x-2 font-bold px-4 text-xs"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            <span>Import Dataset</span>
          </Button>
        }
      />

      {/* Filter and Search controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-4">
        {/* Search form */}
        <form onSubmit={handleSearchSubmit} className="flex items-center flex-1 max-w-md w-full relative">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search datasets by workspace name..."
            className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl pl-4 pr-10 py-2.5 text-xs text-slate-200 outline-none transition"
          />
          {searchInput ? (
            <button
              type="button"
              onClick={handleClearSearch}
              className="absolute right-10 text-slate-500 hover:text-slate-300"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          ) : null}
          <button
            type="submit"
            className="absolute right-3 text-slate-400 hover:text-white"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </form>

        {/* Sorting Dropdown */}
        <div className="flex items-center space-x-3 self-end md:self-auto">
          <span className="text-xs text-slate-500 font-semibold uppercase">Sort By</span>
          <select
            value={params.sort || ''}
            onChange={handleSortChange}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2 outline-none focus:border-cyan-500 cursor-pointer"
          >
            <option value="">Recent Uploads</option>
            <option value="dataset_name:asc">Name (A-Z)</option>
            <option value="dataset_name:desc">Name (Z-A)</option>
            <option value="created_at:asc">Oldest Uploads</option>
          </select>
        </div>
      </div>

      {/* Bulk actions banner */}
      {selectedIds.length > 0 && (
        <ActionBar className="bg-cyan-950/20 border-cyan-500/30 text-cyan-400 animate-slide-in">
          <div className="flex items-center space-x-2 text-xs font-semibold">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
            <span>{selectedIds.length} datasets selected for bulk operations</span>
          </div>
          <Button
            variant="danger"
            onClick={handleBulkDelete}
            isLoading={isDeleting}
            className="py-1.5 px-3 text-xs font-bold"
          >
            Delete Selected
          </Button>
        </ActionBar>
      )}

      {/* Datasets Table */}
      <Table
        data={datasets}
        columns={columns}
        isLoading={loading && datasets.length === 0}
        emptyState={
          <EmptyState
            title="No datasets imported yet"
            description="Upload CSV or Excel spreadsheets to profile, clean, analyze, and generate professional reports."
            action={
              <Button onClick={() => navigate('/datasets/import')} className="font-bold">
                Import First Dataset
              </Button>
            }
          />
        }
      />
    </PageContainer>
  );
};

export default DatasetList;
