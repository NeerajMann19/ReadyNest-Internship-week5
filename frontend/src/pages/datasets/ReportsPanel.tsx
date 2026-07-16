import { useState } from 'react';
import useReports from '../../hooks/useReports';
import { reportsService } from '../../services/reports';
import Loader from '../../components/common/Loader';
import Card from '../../components/common/Card';
import Table from '../../components/common/Table';
import Button from '../../components/common/Button';

interface ReportsPanelProps {
  datasetId: string;
}

export const ReportsPanel = ({ datasetId }: ReportsPanelProps) => {
  const { data: reports, loading, error, refresh, generateReport, deleteReport } = useReports({
    dataset_id: datasetId,
  });

  const [format, setFormat] = useState<'PDF' | 'EXCEL' | 'HTML' | 'JSON'>('PDF');
  const [isCompiling, setIsCompiling] = useState(false);

  const handleCompileReport = async () => {
    setIsCompiling(true);
    try {
      await generateReport(datasetId, format);
      await refresh();
    } catch (err) {
      alert('Report generation failed. Please verify dataset is profiled.');
    } finally {
      setIsCompiling(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this report?')) return;
    try {
      await deleteReport(id);
    } catch (err) {
      alert('Failed to delete report.');
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
    return <Loader type="spinner" text="Resolving compiled files log..." />;
  }

  const columns = [
    {
      header: 'Format',
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
      header: 'Size',
      render: (row: any) => (
        <span className="text-xs text-slate-350 font-medium">
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
      header: 'Compile Duration',
      render: (row: any) => (
        <span className="text-xs text-slate-400 font-medium">
          {row.duration_ms ? `${(row.duration_ms / 1000).toFixed(2)}s` : '0.00s'}
        </span>
      ),
    },
    {
      header: 'Created At',
      render: (row: any) => (
        <span className="text-xs text-slate-400 font-medium">
          {new Date(row.created_at).toLocaleString()}
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
            className="py-1 px-3 text-xs"
          >
            Delete
          </Button>
        </div>
      ),
    },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-fade-in">
      {/* Generate Card */}
      <Card title="Compile Analysis Report" subtitle="Generate fully formatted summary files of dataset diagnostics">
        {error && (
          <div className="bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-xs font-semibold mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-slate-400">Select Export Format</label>
            <select
              value={format}
              onChange={(e) => setFormat(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2.5 outline-none focus:border-cyan-500 cursor-pointer"
            >
              <option value="PDF">PDF Summary (Formatted Print Layout)</option>
              <option value="EXCEL">Excel Spreadsheet (Multi-Sheet Data Quality)</option>
              <option value="HTML">HTML Static Web Page (Responsive Layout)</option>
              <option value="JSON">JSON Document (Raw Schemas Layout)</option>
            </select>
          </div>

          <Button
            onClick={handleCompileReport}
            isLoading={isCompiling}
            className="w-full font-bold py-2.5"
          >
            Compile Report Export
          </Button>
        </div>
      </Card>

      {/* Reports history table */}
      <div className="lg:col-span-2 space-y-4">
        <h3 className="font-bold text-slate-100 text-sm tracking-tight border-b border-slate-800 pb-2">
          Workspace Compiled Export History
        </h3>
        
        <Table
          data={reports}
          columns={columns}
          isLoading={loading && reports.length === 0}
          emptyState={
            <div className="p-8 text-center text-slate-500 font-medium italic">
              No reports compiled for this dataset workspace yet.
            </div>
          }
        />
      </div>
    </div>
  );
};

export default ReportsPanel;
