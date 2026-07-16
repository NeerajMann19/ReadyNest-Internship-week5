import React, { useState } from 'react';
import useReports from '../../hooks/useReports';
import { reportsService } from '../../services/reports';
import { PageContainer, PageHeader, EmptyState } from '../../components/layout/PageContainer';
import { Loader } from '../../components/common/Loader';
import { Table } from '../../components/common/Table';
import Button from '../../components/common/Button';

export const ReportsList: React.FC = () => {
  const { data: reports, loading, deleteReport, params, setParams } = useReports({
    page: 1,
    limit: 20,
  });

  const [searchInput, setSearchInput] = useState(params.search || '');
  const [isDeleting, setIsDeleting] = useState(false);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setParams((prev) => ({ ...prev, search: searchInput || undefined }));
  };

  const handleFormatChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setParams((prev) => ({ ...prev, format: e.target.value || undefined }));
  };

  const handleStatusChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setParams((prev) => ({ ...prev, status: e.target.value || undefined }));
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this report file permanently?')) return;
    setIsDeleting(true);
    try {
      await deleteReport(id);
    } catch (err) {
      alert('Failed to delete report.');
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDownload = async (id: string) => {
    const report = reports.find((r: any) => r.id === id) as any;
    const ext = report?.report_type === 'EXCEL' ? 'xlsx' : (report?.report_type?.toLowerCase() || 'pdf');
    const filename = `${report?.dataset_name || 'dataset'}_report_${id.slice(0, 8)}.${ext}`;
    try {
      await reportsService.download(id, filename);
    } catch (err) {
      console.error('Failed to trigger report download', err);
    }
  };

  if (loading && reports.length === 0) {
    return <Loader type="spinner" text="Resolving global compiled files..." />;
  }

  const columns = [
    {
      header: 'Report Format',
      render: (row: any) => (
        <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md border uppercase tracking-wider ${
          row.report_type === 'PDF'
            ? 'bg-red-950/40 border-red-500/30 text-red-400'
            : row.report_type === 'EXCEL'
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
            : row.report_type === 'HTML'
            ? 'bg-blue-950/40 border-blue-500/30 text-blue-400'
            : 'bg-yellow-950/40 border-yellow-500/30 text-yellow-400'
        }`}>
          {row.report_type}
        </span>
      ),
    },
    {
      header: 'Version Generated From',
      render: (row: any) => (
        <span className="text-xs text-slate-300 font-semibold">
          Version {row.generated_from_version} (Schema {row.report_schema_version})
        </span>
      ),
    },
    {
      header: 'File Size',
      render: (row: any) => (
        <span className="text-xs text-slate-400 font-semibold">
          {row.file_size ? `${(row.file_size / 1024).toFixed(1)} KB` : '0 KB'}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (row: any) => (
        <span className={`text-xs px-2 py-0.5 rounded-full font-bold border ${
          row.status === 'COMPLETED'
            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
            : row.status === 'FAILED'
            ? 'bg-red-950/40 border-red-500/30 text-red-400'
            : 'bg-amber-950/40 border-amber-500/30 text-amber-400 animate-pulse'
        }`}>
          {row.status}
        </span>
      ),
    },
    {
      header: 'Telemetry Timing',
      render: (row: any) => (
        <span className="text-xs text-slate-400 font-medium">
          {row.duration_ms ? `${(row.duration_ms / 1000).toFixed(2)}s` : '0.00s'}
        </span>
      ),
    },
    {
      header: 'Checksum (SHA-256)',
      render: (row: any) => (
        <span className="text-[10px] text-slate-500 font-mono block max-w-[120px] truncate" title={row.checksum || ''}>
          {row.checksum || 'N/A'}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row: any) => (
        <div className="flex items-center space-x-2">
          {row.status === 'COMPLETED' && (
            <Button
              variant="secondary"
              onClick={() => handleDownload(row.id)}
              className="py-1 px-3 text-xs"
            >
              Download
            </Button>
          )}
          <Button
            variant="danger"
            onClick={() => handleDelete(row.id)}
            disabled={isDeleting}
            className="py-1 px-3 text-xs"
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <PageContainer>
      <PageHeader
        title="Reports Control Console"
        subtitle="Manage compiled HTML, PDF, Excel sheets, and JSON schemas across all workspaces"
      />

      {/* Filter and Search controls */}
      <div className="flex flex-col md:flex-row md:items-center gap-4 bg-slate-900 border border-slate-800 rounded-2xl p-4">
        {/* Search */}
        <form onSubmit={handleSearchSubmit} className="flex items-center flex-1 max-w-sm w-full relative">
          <input
            type="text"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search reports by description or ID..."
            className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl pl-4 pr-10 py-2.5 text-xs text-slate-200 outline-none"
          />
          <button type="submit" className="absolute right-3 text-slate-400 hover:text-white">
            <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </button>
        </form>

        {/* Format Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500 font-semibold uppercase">Format</span>
          <select
            value={params.format || ''}
            onChange={handleFormatChange}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2 outline-none cursor-pointer"
          >
            <option value="">All Formats</option>
            <option value="PDF">PDF Summary</option>
            <option value="EXCEL">Excel Spreadsheets</option>
            <option value="HTML">HTML static pages</option>
            <option value="JSON">JSON schemas</option>
          </select>
        </div>

        {/* Status Filter */}
        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500 font-semibold uppercase">Status</span>
          <select
            value={params.status || ''}
            onChange={handleStatusChange}
            className="bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2 outline-none cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="COMPLETED">Completed</option>
            <option value="PENDING">Pending</option>
            <option value="GENERATING">Generating</option>
            <option value="FAILED">Failed</option>
            <option value="EXPIRED">Expired</option>
          </select>
        </div>
      </div>

      {/* Reports Table */}
      <Table
        data={reports}
        columns={columns}
        isLoading={loading && reports.length === 0}
        emptyState={
          <EmptyState
            title="No compiled reports found"
            description="Go to a specific dataset workspace to trigger formatted PDF, Excel sheet, or static HTML compilations."
          />
        }
      />
    </PageContainer>
  );
};

export default ReportsList;
