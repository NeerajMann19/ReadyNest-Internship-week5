import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { datasetService } from '../../services/dataset';
import { PageContainer, PageHeader } from '../../components/layout/PageContainer';
import Button from '../../components/common/Button';
import Card from '../../components/common/Card';

export const DatasetImport: React.FC = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [file, setFile] = useState<File | null>(null);
  const [datasetName, setDatasetName] = useState('');
  const [description, setDescription] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [isDragActive, setIsDragActive] = useState(false);

  const handleFileChange = (selectedFile: File) => {
    // Validate file extensions
    const ext = selectedFile.name.split('.').pop()?.toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx' && ext !== 'xls') {
      setError('Unsupported file type. Please upload a CSV or Excel spreadsheet.');
      setFile(null);
      return;
    }
    setError(null);
    setFile(selectedFile);
    
    // Auto-fill dataset name if empty
    if (!datasetName) {
      const baseName = selectedFile.name.replace(/\.[^/.]+$/, "");
      setDatasetName(baseName.replace(/[_-]/g, ' '));
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !datasetName) {
      setError('Please select a file and enter a dataset name.');
      return;
    }

    setIsUploading(true);
    setError(null);

    try {
      const newDataset = await datasetService.upload(file, datasetName, description || undefined);
      navigate(`/datasets/${newDataset.id}`);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Upload failed. The file structure might be invalid.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <PageContainer>
      <PageHeader
        title="Import Dataset"
        subtitle="Ingest raw tabular data files (CSV, Excel) to begin pipeline diagnostics"
      />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Wizard Form */}
        <Card className="lg:col-span-2 space-y-6">
          <h3 className="font-bold text-slate-100 text-sm tracking-tight border-b border-slate-800 pb-3">
            1. Select Data Source File
          </h3>

          {error && (
            <div className="bg-red-950/40 border border-red-500/30 text-red-400 px-4 py-3 rounded-xl text-xs font-semibold flex items-center space-x-2 animate-pulse">
              <svg xmlns="http://www.w3.org/2000/svg" className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span>{error}</span>
            </div>
          )}

          {/* Drag and Drop Container */}
          <div
            onDragEnter={handleDrag}
            onDragOver={handleDrag}
            onDragLeave={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-3 cursor-pointer transition ${
              isDragActive
                ? 'border-cyan-500 bg-cyan-950/10'
                : file
                ? 'border-emerald-500/40 bg-emerald-950/5'
                : 'border-slate-800 bg-slate-950/30 hover:border-slate-700'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={(e) => e.target.files?.[0] && handleFileChange(e.target.files[0])}
              accept=".csv, .xlsx, .xls"
              className="hidden"
            />
            {file ? (
              <>
                <div className="w-12 h-12 bg-emerald-950/50 border border-emerald-500/30 text-emerald-400 rounded-xl flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-200">{file.name}</p>
                  <p className="text-xs text-slate-400 mt-0.5">{(file.size / 1024).toFixed(1)} KB • Click to swap file</p>
                </div>
              </>
            ) : (
              <>
                <div className="w-12 h-12 bg-slate-900 border border-slate-800 text-slate-400 rounded-xl flex items-center justify-center">
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-200">Drag and drop file here</p>
                  <p className="text-xs text-slate-400 mt-0.5">Supports CSV or Excel tables up to 50MB</p>
                </div>
              </>
            )}
          </div>

          {/* Form details */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <h3 className="font-bold text-slate-100 text-sm tracking-tight border-b border-slate-800 pb-3">
              2. Describe Workspace
            </h3>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400">Workspace Name</label>
              <input
                type="text"
                value={datasetName}
                onChange={(e) => setDatasetName(e.target.value)}
                placeholder="e.g. Sales Q3 Audit"
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none transition"
                required
              />
            </div>

            <div className="space-y-1">
              <label className="text-xs font-semibold text-slate-400">Description (Optional)</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe variables, parameters, or intent of analysis..."
                rows={3}
                className="w-full bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500 rounded-xl px-4 py-2.5 text-sm text-slate-200 outline-none transition resize-none"
              />
            </div>

            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-800">
              <Button
                type="button"
                variant="secondary"
                onClick={() => navigate('/datasets')}
                className="font-bold"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                isLoading={isUploading}
                disabled={!file || !datasetName}
                className="font-bold px-6"
              >
                Upload & Ingest
              </Button>
            </div>
          </form>
        </Card>

        {/* Info panel cards */}
        <div className="space-y-6">
          <Card className="space-y-4 bg-cyan-950/10 border-cyan-500/20 text-cyan-400">
            <h4 className="font-bold text-xs uppercase tracking-wider">Quality Guarantees</h4>
            <ul className="text-xs space-y-2 list-disc pl-4 font-medium leading-relaxed">
              <li>Automatic schema inference checks data types for booleans, numerics, and date columns.</li>
              <li>Calculates duplicate counts and missing cell percentages immediately.</li>
              <li>Persists raw version 1 securely on the storage node.</li>
            </ul>
          </Card>

          <Card className="space-y-3">
            <h4 className="font-bold text-xs uppercase tracking-wider text-slate-200">Security & Privacy</h4>
            <p className="text-xs text-slate-400 leading-relaxed font-medium">
              PrismIQ processes all tabular assets locally. File storage vectors, database logs, and model analysis inferences execute natively without paid external API boundaries.
            </p>
          </Card>
        </div>
      </div>
    </PageContainer>
  );
};

export default DatasetImport;
