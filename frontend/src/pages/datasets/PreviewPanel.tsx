import React, { useState, useEffect, useCallback } from 'react';
import datasetService from '../../services/dataset';
import Loader from '../../components/common/Loader';

interface PreviewPanelProps {
  datasetId: string;
  versionNumber: number;
}

export const PreviewPanel = ({ datasetId, versionNumber }: PreviewPanelProps) => {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [filterInput, setFilterInput] = useState('');
  const [activeFilter, setActiveFilter] = useState('');

  const fetchPreview = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const previewData = await datasetService.preview(datasetId, {
        page,
        page_size: 15,
        filter: activeFilter || undefined,
      });
      setData(previewData);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to load dataset preview records');
    } finally {
      setLoading(false);
    }
  }, [datasetId, page, activeFilter]);

  useEffect(() => {
    fetchPreview();
  }, [fetchPreview]);

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    setActiveFilter(filterInput);
  };

  const handleClearFilter = () => {
    setFilterInput('');
    setActiveFilter('');
    setPage(1);
  };

  if (loading && !data) {
    return <Loader type="spinner" text="Streaming preview grid..." />;
  }

  if (error) {
    return <div className="text-red-400 text-xs p-4 bg-red-950/20 border border-red-500/30 rounded-xl">{error}</div>;
  }

  const columns = data?.columns || [];
  const records = data?.data || [];
  const totalRecords = data?.total_records || 0;
  const totalPages = Math.ceil(totalRecords / 15) || 1;

  return (
    <div className="space-y-4">
      {/* Search Filter Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between bg-slate-900 border border-slate-800 p-4 rounded-xl">
        <form onSubmit={handleFilterSubmit} className="flex items-center flex-1 max-w-md w-full relative">
          <input
            type="text"
            value={filterInput}
            onChange={(e) => setFilterInput(e.target.value)}
            placeholder="Filter rows by text query (e.g. Sales)..."
            className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl pl-4 pr-10 py-2 text-xs text-slate-200 outline-none"
          />
          {filterInput && (
            <button
              type="button"
              onClick={handleClearFilter}
              className="absolute right-3 text-slate-500 hover:text-slate-300"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          )}
        </form>

        <div className="text-xs text-slate-400 font-semibold uppercase">
          Showing {records.length} of {totalRecords} records (Version {versionNumber})
        </div>
      </div>

      {/* Grid container */}
      <div className="overflow-x-auto border border-slate-800 rounded-xl bg-slate-900/20">
        <table className="min-w-full divide-y divide-slate-800 text-left text-xs text-slate-300">
          <thead className="bg-slate-900 text-slate-200 uppercase font-semibold text-[10px] tracking-wider">
            <tr>
              {columns.map((col: string, idx: number) => (
                <th key={idx} scope="col" className="px-6 py-3 border-r border-slate-800/40 last:border-0 whitespace-nowrap">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50 bg-transparent font-medium">
            {records.map((row: any, rIdx: number) => (
              <tr key={rIdx} className="hover:bg-slate-800/20 transition">
                {columns.map((col: string, cIdx: number) => (
                  <td key={cIdx} className="px-6 py-3 border-r border-slate-800/30 last:border-0 whitespace-nowrap truncate max-w-[200px]">
                    {row[col] === null || row[col] === undefined ? (
                      <span className="text-slate-600 italic">null</span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
            {records.length === 0 && (
              <tr>
                <td colSpan={columns.length} className="px-6 py-12 text-center text-slate-500 font-medium italic">
                  No preview records matching filter query.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination controls */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between bg-slate-900 border border-slate-800 px-4 py-3 rounded-xl">
          <button
            disabled={page === 1}
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-3 py-1.5 rounded-lg disabled:opacity-40 transition"
          >
            Previous
          </button>
          <span className="text-xs text-slate-400 font-medium">
            Page {page} of {totalPages}
          </span>
          <button
            disabled={page === totalPages}
            onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold px-3 py-1.5 rounded-lg disabled:opacity-40 transition"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default PreviewPanel;
