import { useState } from 'react';
import { cleaningService, CleaningOperation } from '../../services/cleaning';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';
import Loader from '../../components/common/Loader';

interface Change {
  type: string;
  column: string | null;
  affected: number;
  description: string;
}

interface CleaningPreviewResponse {
  before: {
    rows_count: number;
    columns_count: number;
    missing_values: number;
    duplicate_rows: number;
  };
  after: {
    rows_count: number;
    columns_count: number;
    missing_values: number;
    duplicate_rows: number;
  };
  changes: Change[];
  warnings: string[];
  original_sample: Record<string, unknown>[];
  cleaned_sample: Record<string, unknown>[];
}

interface CleaningPanelProps {
  datasetId: string;
  onCleaningSuccess: () => void;
  availableColumns: string[];
}

export const CleaningPanel = ({
  datasetId,
  onCleaningSuccess,
  availableColumns,
}: CleaningPanelProps) => {
  const [operations, setOperations] = useState<CleaningOperation[]>([]);
  const [previewResult, setPreviewResult] = useState<CleaningPreviewResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Extract preview stats safely
  const before = previewResult?.before;
  const after = previewResult?.after;
  const changes = Array.isArray(previewResult?.changes) ? previewResult.changes : [];
  
  const missingHandled = changes
    .filter((c) => c.type === 'fill_missing')
    .reduce((sum, c) => sum + (c.affected ?? 0), 0);
  
  const duplicatesRemoved = changes
    .filter((c) => c.type === 'drop_duplicates')
    .reduce((sum, c) => sum + (c.affected ?? 0), 0);

  // New operation state
  const [opType, setOpType] = useState('drop_duplicates');
  const [selectedCol, setSelectedCol] = useState(availableColumns[0] || '');
  const [fillMethod, setFillMethod] = useState('mean');
  const [customValue, setCustomValue] = useState('');

  const handleAddOperation = () => {
    let newOp: CleaningOperation = { type: opType };

    if (opType === 'drop_missing' || opType === 'fill_missing') {
      newOp.column = selectedCol;
    }

    if (opType === 'fill_missing') {
      newOp.parameters = {
        method: fillMethod,
        value: fillMethod === 'custom' ? customValue : undefined,
      };
    }

    setOperations((prev) => [...prev, newOp]);
    // Reset inputs
    setCustomValue('');
  };

  const handleRemoveOperation = (index: number) => {
    setOperations((prev) => prev.filter((_, idx) => idx !== index));
    setPreviewResult(null);
  };

  const handlePreview = async () => {
    if (operations.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      const data = await cleaningService.preview(datasetId, operations);
      setPreviewResult(data);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Cleaning preview calculation failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleApply = async () => {
    if (operations.length === 0) return;
    if (!window.confirm('Are you sure you want to apply these cleaning changes? This will construct Version 2.')) return;
    
    setLoading(true);
    setError(null);
    try {
      await cleaningService.apply(datasetId, operations);
      setOperations([]);
      setPreviewResult(null);
      onCleaningSuccess();
    } catch (err: any) {
      setError(err.response?.data?.message || 'Cleaning execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-fade-in">
      {/* Wizard controller */}
      <Card title="Add Cleaning Operations" subtitle="Select standard rules to build your cleaning pipeline">
        {error && (
          <div className="bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-xs font-semibold mb-4">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Op Selector */}
            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400">Operation Type</label>
              <select
                value={opType}
                onChange={(e) => setOpType(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2.5 outline-none focus:border-cyan-500 cursor-pointer"
              >
                <option value="drop_duplicates">Remove Duplicate Rows</option>
                <option value="drop_missing">Drop Rows with Nulls</option>
                <option value="fill_missing">Fill Missing Cell Values</option>
              </select>
            </div>

            {/* Column Selector */}
            {(opType === 'drop_missing' || opType === 'fill_missing') && (
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400">Target Column</label>
                <select
                  value={selectedCol}
                  onChange={(e) => setSelectedCol(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2.5 outline-none focus:border-cyan-500 cursor-pointer"
                >
                  {availableColumns.map((col) => (
                    <option key={col} value={col}>
                      {col}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {/* Fill Method params */}
          {opType === 'fill_missing' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-slate-950/50 p-4 border border-slate-800 rounded-xl">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-slate-400">Strategy</label>
                <select
                  value={fillMethod}
                  onChange={(e) => setFillMethod(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2 outline-none"
                >
                  <option value="mean">Mean Value</option>
                  <option value="median">Median Value</option>
                  <option value="mode">Mode Value</option>
                  <option value="custom">Custom Literal Value</option>
                </select>
              </div>

              {fillMethod === 'custom' && (
                <div className="space-y-1">
                  <label className="text-xs font-semibold text-slate-400">Custom Value</label>
                  <input
                    type="text"
                    value={customValue}
                    onChange={(e) => setCustomValue(e.target.value)}
                    placeholder="e.g. 0 or N/A"
                    className="w-full bg-slate-900 border border-slate-800 text-slate-200 text-xs font-medium rounded-xl px-3 py-2 outline-none"
                  />
                </div>
              )}
            </div>
          )}

          <Button onClick={handleAddOperation} variant="secondary" className="w-full font-bold">
            Add to Pipeline
          </Button>

          {/* Pipeline stages list */}
          <div className="space-y-2 border-t border-slate-800 pt-4">
            <h4 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Pipeline Stages</h4>
            {operations.map((op, idx) => (
              <div key={idx} className="flex items-center justify-between bg-slate-950 border border-slate-850 p-3 rounded-xl text-xs">
                <div>
                  <span className="font-bold text-cyan-400">{idx + 1}. {op.type.replace('_', ' ')}</span>
                  {op.column && <span className="text-slate-400 font-medium"> on column <code className="text-white font-bold">{op.column}</code></span>}
                  {op.parameters && <span className="text-slate-500 font-medium"> ({op.parameters.method})</span>}
                </div>
                <button
                  type="button"
                  onClick={() => handleRemoveOperation(idx)}
                  className="text-red-400 hover:text-red-300 font-semibold"
                >
                  Remove
                </button>
              </div>
            ))}
            {operations.length === 0 && (
              <p className="text-xs text-slate-500 py-4 text-center font-medium italic">No cleaning steps defined yet.</p>
            )}
          </div>

          {operations.length > 0 && (
            <div className="flex items-center space-x-3 pt-4 border-t border-slate-800">
              <Button onClick={handlePreview} isLoading={loading} variant="secondary" className="flex-1 font-bold">
                Preview Diagnostics
              </Button>
              <Button onClick={handleApply} isLoading={loading} className="flex-1 font-bold">
                Apply & Clean
              </Button>
            </div>
          )}
        </div>
      </Card>

      {/* Preview results log display */}
      <div className="space-y-6">
        {loading && <Loader type="spinner" text="Running preview simulation..." />}

        {previewResult && !loading && before && after && (
          <Card title="Cleaning Preview Summary" subtitle="Simulated results of operations before writing changes">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl text-center">
                  <p className="text-xs text-slate-500 font-semibold uppercase">Original Rows</p>
                  <p className="text-2xl font-black text-slate-200">
                    {before.rows_count}
                  </p>
                </div>
                <div className="bg-cyan-950/20 border border-cyan-500/30 p-4 rounded-xl text-center">
                  <p className="text-xs text-cyan-500 font-semibold uppercase">Cleaned Rows</p>
                  <p className="text-2xl font-black text-cyan-400">
                    {after.rows_count}
                  </p>
                </div>
              </div>

              {/* Operations detail logs */}
              <div className="bg-slate-950 border border-slate-850 p-4 rounded-xl space-y-2 text-xs leading-relaxed font-semibold">
                <h4 className="font-bold text-slate-300">Detailed Preview Metrics</h4>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Original Columns</span>
                  <span className="text-slate-200">{before.columns_count}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Cleaned Columns</span>
                  <span className="text-slate-200">{after.columns_count}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Original Missing Values</span>
                  <span className="text-slate-200">{before.missing_values}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Cleaned Missing Values</span>
                  <span className="text-slate-200">{after.missing_values}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Original Duplicate Rows</span>
                  <span className="text-slate-200">{before.duplicate_rows}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Cleaned Duplicate Rows</span>
                  <span className="text-slate-200">{after.duplicate_rows}</span>
                </div>
                <div className="flex justify-between border-b border-slate-800/40 py-1">
                  <span className="text-slate-400">Missing Handled</span>
                  <span className="text-emerald-400">+{missingHandled}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Duplicates Removed</span>
                  <span className="text-red-400">-{duplicatesRemoved}</span>
                </div>
              </div>
            </div>
          </Card>
        )}

        {!previewResult && !loading && (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center text-slate-500 font-medium italic h-full flex items-center justify-center">
            Configure pipeline and click "Preview Diagnostics" to audit changes.
          </div>
        )}
      </div>
    </div>
  );
};

export default CleaningPanel;
