/**
 * Machine Learning Predictive Analytics Control Panel TSX Component.
 */
import { useState, useEffect, useRef } from 'react';
import useProfile from '../../hooks/useProfile';
import mlService, { MLModelResponse, PredictionLogResponse } from '../../services/ml';
import Loader from '../../components/common/Loader';
import Card from '../../components/common/Card';
import Table from '../../components/common/Table';
import Button from '../../components/common/Button';

interface MlPanelProps {
  datasetId: string;
}

export const MlPanel = ({ datasetId }: MlPanelProps) => {
  const { data: profile, loading: profileLoading, error: profileError } = useProfile(datasetId);

  // States
  const [models, setModels] = useState<MLModelResponse[]>([]);
  const [activeModel, setActiveModel] = useState<MLModelResponse | null>(null);
  const [activeStep, setActiveStep] = useState<'config' | 'training' | 'results' | 'sandbox'>('config');

  // Config Step parameters
  const [targetCol, setTargetCol] = useState<string>('');
  const [problemType, setProblemType] = useState<'auto' | 'classification' | 'regression'>('auto');
  const [selectedFeatures, setSelectedFeatures] = useState<string[]>([]);
  const [selectedAlgos, setSelectedAlgos] = useState<string[]>(['random_forest', 'logistic_regression', 'linear_regression', 'gradient_boosting']);
  const [crossVal, setCrossVal] = useState<boolean>(false);
  const [randomState, setRandomState] = useState<number>(42);

  // Training Step parameters
  const [trainingLogs, setTrainingLogs] = useState<{ timestamp: string; message: string }[]>([]);
  const [isPolling, setIsPolling] = useState<boolean>(false);
  const [pollingError, setPollingError] = useState<string>('');

  // Sandbox Step parameters
  const [sandboxInputs, setSandboxInputs] = useState<Record<string, string>>({});
  const [sandboxPrediction, setSandboxPrediction] = useState<any>(null);
  const [sandboxConfidence, setSandboxConfidence] = useState<number | null>(null);
  const [predictionHistory, setPredictionHistory] = useState<PredictionLogResponse[]>([]);
  const [isPredicting, setIsPredicting] = useState<boolean>(false);

  const logsEndRef = useRef<HTMLDivElement>(null);
  const pollingInterval = useRef<any>(null);

  // Fetch trained models for this dataset workspace
  const fetchModels = async () => {
    try {
      const data = await mlService.listModels(datasetId);
      setModels(data);
      if (data.length > 0 && !activeModel) {
        // Automatically default to the latest completed champion model
        const latestCompleted = data.find((m) => m.status === 'COMPLETED');
        if (latestCompleted) {
          setActiveModel(latestCompleted);
          setActiveStep('results');
        }
      }
    } catch (err) {
      console.error('Failed to load models list', err);
    }
  };

  useEffect(() => {
    fetchModels();
  }, [datasetId]);

  // Helper to determine if a column is suitable as a default model feature
  const isFeatureSuitable = (col: any, target: string): boolean => {
    if (col.name === target) return false;
    
    const nameLower = col.name.toLowerCase();
    // Exclude obvious key/ID pattern columns
    if (
      nameLower === 'id' ||
      nameLower === 'uuid' ||
      nameLower === 'index' ||
      nameLower === 'email' ||
      nameLower === 'customerid' ||
      nameLower === 'invoiceno' ||
      nameLower === 'customername' ||
      nameLower.endsWith('_id') ||
      nameLower.endsWith('id')
    ) {
      return false;
    }
    
    // Exclude high cardinality categorical columns (> 50 unique values)
    const isCategorical = !col.dtype?.toLowerCase()?.includes('int') && 
                          !col.dtype?.toLowerCase()?.includes('float') &&
                          !col.dtype?.toLowerCase()?.includes('double') &&
                          !col.dtype?.toLowerCase()?.includes('number') &&
                          !col.dtype?.toLowerCase()?.includes('numeric');
                          
    if (isCategorical && col.unique_count > 50) {
      return false;
    }
    
    return true;
  };

  // Set default target and features when profile is resolved
  useEffect(() => {
    if (profile && profile.column_summary && profile.column_summary.length > 0) {
      const columns = profile.column_summary.map((c) => c.name);
      if (!targetCol) {
        // Default to last column
        const defaultTarget = columns[columns.length - 1];
        setTargetCol(defaultTarget);
        // Default features: everything except target that is suitable
        setSelectedFeatures(
          profile.column_summary
            .filter((c) => isFeatureSuitable(c, defaultTarget))
            .map((c) => c.name)
        );
      } else {
        // Re-validate existing selection on load/render to filter out unsuitable features
        setSelectedFeatures((prev) => 
          prev.filter((featName) => {
            const colObj = profile.column_summary.find((c) => c.name === featName);
            return colObj ? isFeatureSuitable(colObj, targetCol) : false;
          })
        );
      }
    }
  }, [profile, targetCol]);

  // Auto-scroll logs terminal
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [trainingLogs]);

  // Handle target change -> exclude target from features list
  const handleTargetChange = (newTarget: string) => {
    setTargetCol(newTarget);
    if (profile && profile.column_summary) {
      setSelectedFeatures(
        profile.column_summary
          .filter((c) => isFeatureSuitable(c, newTarget))
          .map((c) => c.name)
      );
    }
  };

  // Select all / Clear features helpers
  const handleSelectAllFeatures = () => {
    if (profile && profile.column_summary) {
      setSelectedFeatures(
        profile.column_summary
          .filter((c) => isFeatureSuitable(c, targetCol))
          .map((c) => c.name)
      );
    }
  };

  const handleClearFeatures = () => {
    setSelectedFeatures([]);
  };

  // Toggle Feature helper
  const handleToggleFeature = (colName: string) => {
    if (selectedFeatures.includes(colName)) {
      setSelectedFeatures(selectedFeatures.filter((f) => f !== colName));
    } else {
      setSelectedFeatures([...selectedFeatures, colName]);
    }
  };

  // Start champion model fit search
  const handleTriggerTraining = async () => {
    if (!targetCol) {
      alert('Please specify a target column.');
      return;
    }
    if (selectedFeatures.length === 0) {
      alert('Please select at least one feature column for training.');
      return;
    }

    try {
      setPollingError('');
      setTrainingLogs([{ timestamp: new Date().toISOString(), message: 'Submitting training task to background workers...' }]);
      setActiveStep('training');
      
      const payload = {
        target_column: targetCol,
        problem_type: problemType,
        features: selectedFeatures,
        candidate_algorithms: selectedAlgos,
        cross_validation: crossVal,
        random_state: randomState,
      };

      const res = await mlService.trainModel(datasetId, payload);
      const model = res.data;
      setActiveModel(model);
      setTrainingLogs(model.training_log || []);
      
      // Start polling status
      setIsPolling(true);
      startPolling(model.id);
    } catch (err: any) {
      setActiveStep('config');
      alert(`Failed to launch training: ${err?.response?.data?.message || err.message}`);
    }
  };

  // Polling helper
  const startPolling = (modelId: string) => {
    if (pollingInterval.current) clearInterval(pollingInterval.current);
    
    pollingInterval.current = setInterval(async () => {
      try {
        const model = await mlService.getModelDetails(modelId);
        setActiveModel(model);
        setTrainingLogs(model.training_log || []);

        if (model.status === 'COMPLETED') {
          clearInterval(pollingInterval.current);
          setIsPolling(false);
          await fetchModels();
          setActiveStep('results');
        } else if (model.status === 'FAILED') {
          clearInterval(pollingInterval.current);
          setIsPolling(false);
          setPollingError(model.error_message || 'Training failed due to server exceptions.');
        }
      } catch (err) {
        console.error('Polling error', err);
      }
    }, 2000);
  };

  // Clean polling on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval.current) clearInterval(pollingInterval.current);
    };
  }, []);

  // Sandbox inference solver
  const handleRunPrediction = async () => {
    if (!activeModel) return;
    setIsPredicting(true);
    try {
      const payload: Record<string, any> = {};
      Object.entries(sandboxInputs).forEach(([k, v]) => {
        // Parse float if numerical column
        const isNum = profile?.column_summary?.find((col) => col.name === k)?.dtype?.toLowerCase()?.includes('int') || 
                      profile?.column_summary?.find((col) => col.name === k)?.dtype?.toLowerCase()?.includes('float');
        payload[k] = isNum && v !== '' ? parseFloat(v) : v;
      });

      const res = await mlService.makePrediction(activeModel.id, payload);
      setSandboxPrediction(res.prediction);
      setSandboxConfidence(res.confidence !== undefined ? res.confidence : null);
      
      // Refresh prediction history
      const history = await mlService.getPredictionHistory(activeModel.id);
      setPredictionHistory(history);
    } catch (err: any) {
      alert(`Prediction calculation failed: ${err?.response?.data?.message || err.message}`);
    } finally {
      setIsPredicting(false);
    }
  };

  // Transition to prediction sandbox step
  const handleTransitionToSandbox = async (model: MLModelResponse) => {
    setActiveModel(model);
    setSandboxPrediction(null);
    setSandboxConfidence(null);
    
    // Set default empty inputs
    const defaults: Record<string, string> = {};
    model.features.forEach((feat) => {
      defaults[feat] = '';
    });
    setSandboxInputs(defaults);
    
    try {
      const history = await mlService.getPredictionHistory(model.id);
      setPredictionHistory(history);
    } catch (err) {
      console.error(err);
    }
    
    setActiveStep('sandbox');
  };

  // Delete model handler
  const handleDeleteModel = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this model and binary files?')) return;
    try {
      await mlService.deleteModel(id);
      await fetchModels();
      if (activeModel?.id === id) {
        setActiveModel(null);
        setActiveStep('config');
      }
    } catch (err) {
      alert('Failed to delete model.');
    }
  };

  if (profileLoading) {
    return <Loader type="spinner" text="Aligning model training wizard dimensions..." />;
  }

  if (profileError || !profile) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center flex flex-col items-center justify-center space-y-4">
        <div className="w-12 h-12 bg-amber-950/50 border border-amber-500/30 text-amber-400 rounded-xl flex items-center justify-center">
          ⚠️
        </div>
        <div>
          <h3 className="font-bold text-slate-200 tracking-tight">Active Data Profile Required</h3>
          <p className="text-xs text-slate-400 max-w-sm font-medium mt-1">
            Data profile diagnostics must be completed before launching machine learning pipelines.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Step Indicator Header */}
      <div className="bg-slate-950/50 backdrop-blur-md border border-slate-800/80 rounded-2xl p-4 flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center space-x-2">
          <span className="text-lg font-extrabold text-slate-200">Predictive Engine:</span>
          {activeModel && (
            <span className="text-xs font-bold px-2.5 py-0.5 rounded-md bg-cyan-950/40 border border-cyan-500/30 text-cyan-400">
              Active: {activeModel.model_type} (v{activeModel.model_version})
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setActiveStep('config')}
            disabled={isPolling}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition ${
              activeStep === 'config'
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                : 'bg-transparent border-slate-800 text-slate-400 hover:text-slate-200 disabled:opacity-40'
            }`}
          >
            1. Configure
          </button>
          
          <button
            onClick={() => setActiveStep('training')}
            disabled={!activeModel || activeModel.status !== 'TRAINING'}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition ${
              activeStep === 'training'
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                : 'bg-transparent border-slate-800 text-slate-400 hover:text-slate-200 disabled:opacity-40'
            }`}
          >
            2. Train Logs
          </button>
          
          <button
            onClick={() => setActiveStep('results')}
            disabled={!activeModel || activeModel.status !== 'COMPLETED'}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition ${
              activeStep === 'results'
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                : 'bg-transparent border-slate-800 text-slate-400 hover:text-slate-200 disabled:opacity-40'
            }`}
          >
            3. Evaluation Champion
          </button>
          
          <button
            onClick={() => handleTransitionToSandbox(activeModel!)}
            disabled={!activeModel || activeModel.status !== 'COMPLETED'}
            className={`text-xs font-bold px-3 py-1.5 rounded-lg border transition ${
              activeStep === 'sandbox'
                ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                : 'bg-transparent border-slate-800 text-slate-400 hover:text-slate-200 disabled:opacity-40'
            }`}
          >
            4. Inference Sandbox
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* LEFT COLUMN: ACTIVE WORKSPACE STEP RENDERING */}
        <div className="lg:col-span-2 space-y-6">

          {/* STEP 1: CONFIGURATION */}
          {activeStep === 'config' && (
            <Card title="Configure Predictive Model Workspace" subtitle="Setup variables and select model candidates">
              <div className="space-y-6">
                
                {/* Target Column Selection */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Target Variable (Y-Axis)</label>
                    <select
                      value={targetCol}
                      onChange={(e) => handleTargetChange(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 text-slate-200 text-xs rounded-xl px-3 py-2.5 outline-none focus:border-cyan-500 cursor-pointer font-bold"
                    >
                      {profile.column_summary.map((col) => (
                        <option key={col.name} value={col.name}>
                          {col.name} ({col.dtype})
                        </option>
                      ))}
                    </select>
                    <p className="text-[10px] text-slate-500">The column you want the champion model to predict.</p>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Problem Objective</label>
                    <div className="grid grid-cols-3 gap-2">
                      {(['auto', 'classification', 'regression'] as const).map((type) => (
                        <button
                          key={type}
                          onClick={() => setProblemType(type)}
                          className={`text-xs py-2 px-3 rounded-xl border text-center font-bold capitalize transition ${
                            problemType === type
                              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                              : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-300'
                          }`}
                        >
                          {type}
                        </button>
                      ))}
                    </div>
                    <p className="text-[10px] text-slate-500">Auto infers target characteristics dynamically.</p>
                  </div>
                </div>

                {/* Features Selection Checkboxes */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Feature Inputs (X-Axis)</label>
                    <div className="flex space-x-2">
                      <button onClick={handleSelectAllFeatures} className="text-[10px] text-cyan-400 hover:underline font-bold">Select All</button>
                      <span className="text-slate-600 text-[10px]">•</span>
                      <button onClick={handleClearFeatures} className="text-[10px] text-slate-500 hover:underline font-bold">Clear All</button>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 bg-slate-950/80 border border-slate-800/80 rounded-xl">
                    {profile.column_summary
                      .filter((col) => col.name !== targetCol)
                      .map((col) => {
                        const isChecked = selectedFeatures.includes(col.name);
                        return (
                          <button
                            key={col.name}
                            onClick={() => handleToggleFeature(col.name)}
                            className={`flex items-center space-x-2 p-2 rounded-lg text-left transition text-xs border ${
                              isChecked
                                ? 'bg-cyan-950/20 border-cyan-500/20 text-slate-200'
                                : 'bg-transparent border-transparent text-slate-500 hover:text-slate-400'
                            }`}
                          >
                            <span className={`w-3.5 h-3.5 rounded flex items-center justify-center text-[10px] border ${
                              isChecked ? 'bg-cyan-500 border-cyan-500 text-slate-950 font-bold' : 'border-slate-800'
                            }`}>
                              {isChecked && '✓'}
                            </span>
                            <span className="truncate font-semibold">{col.name}</span>
                          </button>
                        );
                      })}
                  </div>
                </div>

                {/* Algorithms selection */}
                <div className="space-y-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Candidate Model Estimators</label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                    {[
                      { id: 'random_forest', label: 'Random Forest' },
                      { id: 'logistic_regression', label: 'Logistic Regression (Classifier)' },
                      { id: 'linear_regression', label: 'Linear Regression (Regressor)' },
                      { id: 'gradient_boosting', label: 'Gradient Boosting' },
                    ].map((algo) => {
                      const isSelected = selectedAlgos.includes(algo.id);
                      const handleToggle = () => {
                        if (isSelected) {
                          setSelectedAlgos(selectedAlgos.filter((a) => a !== algo.id));
                        } else {
                          setSelectedAlgos([...selectedAlgos, algo.id]);
                        }
                      };
                      return (
                        <button
                          key={algo.id}
                          onClick={handleToggle}
                          className={`text-[11px] p-2.5 border rounded-xl font-bold transition text-center ${
                            isSelected
                              ? 'bg-cyan-500/10 border-cyan-500/30 text-cyan-400'
                              : 'bg-slate-950 border-slate-800 text-slate-500 hover:text-slate-350'
                          }`}
                        >
                          {algo.label}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {/* Advanced parameters panel */}
                <div className="p-3 bg-slate-950/40 border border-slate-800/80 rounded-xl space-y-3">
                  <div className="text-[11px] font-bold text-slate-350 uppercase tracking-wider">Hyperparameter Setup</div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="flex items-center space-x-2.5 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={crossVal}
                        onChange={(e) => setCrossVal(e.target.checked)}
                        className="rounded border-slate-800 bg-slate-950 text-cyan-500 focus:ring-0 cursor-pointer"
                      />
                      <div>
                        <span className="text-xs font-bold text-slate-300">Run 3-Fold Cross Validation</span>
                        <p className="text-[10px] text-slate-500">Evaluates reliability across folds.</p>
                      </div>
                    </label>

                    <div className="flex items-center justify-between bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800">
                      <span className="text-xs font-bold text-slate-400">Random State</span>
                      <input
                        type="number"
                        value={randomState}
                        onChange={(e) => setRandomState(parseInt(e.target.value) || 42)}
                        className="bg-transparent text-right outline-none text-xs font-bold text-cyan-400 w-16"
                      />
                    </div>
                  </div>
                </div>

                {/* Action Trigger */}
                <Button onClick={handleTriggerTraining} className="w-full font-extrabold py-3 text-sm">
                  Launch Champion Estimator Training
                </Button>

              </div>
            </Card>
          )}

          {/* STEP 2: TRAINING LOGS & STATUS */}
          {activeStep === 'training' && (
            <Card title="Fitting Selected Candidates" subtitle="Streaming live engine output from background workers">
              <div className="space-y-4">
                
                {/* Live log animation */}
                <div className="flex items-center justify-between p-4 bg-slate-950 border border-slate-800 rounded-xl">
                  <div className="flex items-center space-x-3">
                    <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-ping" />
                    <div>
                      <span className="text-xs font-bold text-slate-200">Fitting Model Iterations...</span>
                      <p className="text-[10px] text-slate-500">Selected target: {activeModel?.target_column}</p>
                    </div>
                  </div>
                  <span className="text-xs font-mono font-bold text-cyan-400 bg-slate-900 border border-slate-800 px-2.5 py-1 rounded">
                    {activeModel?.status || 'TRAINING'}
                  </span>
                </div>

                {/* Polling Error Alert */}
                {pollingError && (
                  <div className="p-3 bg-red-950/30 border border-red-500/30 rounded-xl text-xs text-red-400 font-bold">
                    {pollingError}
                  </div>
                )}

                {/* Log Terminal Screen */}
                <div className="bg-slate-950 border border-slate-900 font-mono text-[11px] text-slate-300 p-4 rounded-xl h-64 overflow-y-auto space-y-1.5 shadow-inner">
                  {trainingLogs.map((log, idx) => (
                    <div key={idx} className="flex space-x-2">
                      <span className="text-slate-600">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
                      <span className={log.message.includes('successfully') ? 'text-emerald-400 font-bold' : log.message.includes('failed') ? 'text-red-400 font-bold' : 'text-slate-350'}>
                        {log.message}
                      </span>
                    </div>
                  ))}
                  <div ref={logsEndRef} />
                </div>

                {pollingError && (
                  <Button onClick={() => setActiveStep('config')} variant="secondary" className="w-full font-bold">
                    Adjust Configuration Parameters
                  </Button>
                )}
              </div>
            </Card>
          )}

          {/* STEP 3: RESULTS & METRICS */}
          {activeStep === 'results' && activeModel && (
            <div className="space-y-6">
              
              {/* Champion summary card */}
              <Card title="Champion Model Found" subtitle={`Version v${activeModel.model_version} • Generated ${new Date(activeModel.created_at).toLocaleDateString()}`}>
                
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                  
                  <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Best Score</span>
                    <h3 className="text-xl font-black text-cyan-400 mt-1">{(activeModel.best_score || 0).toFixed(4)}</h3>
                  </div>

                  <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Estimator Type</span>
                    <h3 className="text-xs font-bold text-slate-200 mt-2 truncate capitalize">{activeModel.model_type.replace('_', ' ')}</h3>
                  </div>

                  <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Target Variable</span>
                    <h3 className="text-xs font-mono font-bold text-slate-200 mt-2 truncate"><code>{activeModel.target_column}</code></h3>
                  </div>

                  <div className="bg-slate-950 border border-slate-800/80 rounded-xl p-3 text-center">
                    <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Training Samples</span>
                    <h3 className="text-xl font-black text-slate-200 mt-1">{activeModel.training_rows || 0}</h3>
                  </div>

                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  
                  {/* Validation metrics list */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider border-b border-slate-900 pb-1.5">Validation Metrics</h4>
                    <div className="space-y-2">
                      {activeModel.evaluation_metrics && Object.entries(activeModel.evaluation_metrics)
                        .filter(([k]) => typeof activeModel.evaluation_metrics?.[k] === 'number')
                        .map(([k, v]: [string, any]) => (
                          <div key={k} className="flex justify-between items-center text-xs bg-slate-950 px-3 py-2 rounded-lg border border-slate-900">
                            <span className="font-semibold text-slate-400 uppercase tracking-tight">{k}</span>
                            <span className="font-mono font-bold text-slate-200">{v.toFixed(4)}</span>
                          </div>
                        ))}
                    </div>
                  </div>

                  {/* Explainability / Importances list */}
                  <div className="space-y-3">
                    <h4 className="text-xs font-extrabold text-slate-400 uppercase tracking-wider border-b border-slate-900 pb-1.5">Top Feature Importances</h4>
                    <div className="space-y-2.5">
                      {activeModel.feature_importances && Object.entries(activeModel.feature_importances).map(([feat, imp]) => (
                        <div key={feat} className="space-y-1">
                          <div className="flex justify-between items-center text-[11px] font-bold">
                            <code className="text-cyan-400 font-bold">X: {feat}</code>
                            <span className="text-slate-400">{(imp * 100).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-slate-950 border border-slate-900 rounded-full h-2">
                            <div className="bg-cyan-500 h-1.5 rounded-full" style={{ width: `${imp * 100}%` }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                </div>

                {/* Footer Operations */}
                <div className="flex items-center space-x-3 mt-8 pt-4 border-t border-slate-900">
                  <Button onClick={() => handleTransitionToSandbox(activeModel)} className="font-bold flex-1 py-2.5">
                    Launch Inference Sandbox
                  </Button>
                  <Button onClick={() => setActiveStep('config')} variant="secondary" className="font-bold py-2.5">
                    Train Alternate Version
                  </Button>
                </div>

              </Card>

            </div>
          )}

          {/* STEP 4: PREDICTION SANDBOX */}
          {activeStep === 'sandbox' && activeModel && (
            <div className="space-y-6">
              
              <Card title="Audited Inference Sandbox" subtitle="Execute row calculations and log outputs to history">
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                  {activeModel.features.map((feat) => {
                    const colInfo = profile.column_summary.find((c) => c.name === feat);
                    const isNumeric = colInfo?.dtype?.toLowerCase()?.includes('int') || colInfo?.dtype?.toLowerCase()?.includes('float');
                    
                    return (
                      <div key={feat} className="space-y-1.5">
                        <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                          {feat} <span className="text-[10px] text-slate-650 font-normal">({colInfo?.dtype || 'any'})</span>
                        </label>
                        <input
                          type={isNumeric ? 'number' : 'text'}
                          step="any"
                          value={sandboxInputs[feat] || ''}
                          onChange={(e) => setSandboxInputs({ ...sandboxInputs, [feat]: e.target.value })}
                          placeholder={`Enter value...`}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-semibold text-slate-200 outline-none focus:border-cyan-500"
                        />
                      </div>
                    );
                  })}
                </div>

                {/* Calculation trigger */}
                <Button onClick={handleRunPrediction} isLoading={isPredicting} className="w-full font-extrabold py-3 text-sm mb-6">
                  Calculate Prediction Output
                </Button>

                {/* Real-time result visualizer */}
                {sandboxPrediction !== null && (
                  <div className="p-4 bg-cyan-950/20 border border-cyan-500/25 rounded-2xl flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Prediction Outcome</span>
                      <h2 className="text-2xl font-black text-cyan-400 mt-1">{sandboxPrediction}</h2>
                    </div>
                    {sandboxConfidence !== null && (
                      <div className="text-right">
                        <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Inference Confidence</span>
                        <h2 className="text-xl font-bold text-cyan-300 mt-1">{(sandboxConfidence * 100).toFixed(1)}%</h2>
                      </div>
                    )}
                  </div>
                )}

              </Card>

              {/* Prediction history log */}
              <div className="space-y-3">
                <h3 className="text-sm font-extrabold text-slate-200 tracking-tight border-b border-slate-800 pb-1.5">Sandbox Calculation Audits</h3>
                <Table
                  data={predictionHistory}
                  columns={[
                    {
                      header: 'Timestamp',
                      render: (row) => <span className="text-[11px] text-slate-400 font-medium">{new Date(row.created_at).toLocaleString()}</span>,
                    },
                    {
                      header: 'Input Payload',
                      render: (row) => <pre className="text-[10px] text-slate-500 truncate max-w-[250px] font-mono">{JSON.stringify(row.input_payload)}</pre>,
                    },
                    {
                      header: 'Prediction Result',
                      render: (row) => <span className="text-xs font-bold text-slate-200">{row.prediction}</span>,
                    },
                    {
                      header: 'Confidence Score',
                      render: (row) => <span className="text-xs text-slate-400">{row.confidence !== null && row.confidence !== undefined ? `${(row.confidence * 100).toFixed(1)}%` : 'N/A'}</span>,
                    },
                  ]}
                  emptyState={<div className="p-4 text-center text-slate-500 italic text-xs font-medium">No sandbox records run for this model yet.</div>}
                />
              </div>

            </div>
          )}

        </div>

        {/* RIGHT COLUMN: TRAINING RUNS LEADERBOARD */}
        <div className="space-y-4">
          <h3 className="text-sm font-extrabold text-slate-200 tracking-tight border-b border-slate-800 pb-1.5 flex items-center justify-between">
            <span>Trained Model Registry</span>
            <span className="text-[10px] px-2 py-0.5 bg-slate-900 border border-slate-800 rounded text-slate-400 font-bold">{models.length} Total</span>
          </h3>

          <div className="space-y-3 max-h-[500px] overflow-y-auto">
            {models.length === 0 ? (
              <div className="p-8 text-center text-slate-500 italic text-xs font-semibold bg-slate-950/20 border border-dashed border-slate-800 rounded-xl">
                No model versions trained yet.
              </div>
            ) : (
              models.map((model) => {
                const isActive = activeModel?.id === model.id;
                return (
                  <div
                    key={model.id}
                    className={`p-3.5 border rounded-2xl cursor-pointer transition relative group ${
                      isActive
                        ? 'bg-cyan-950/20 border-cyan-500/40'
                        : 'bg-slate-950/50 border-slate-800/80 hover:bg-slate-900/40 hover:border-slate-750'
                    }`}
                    onClick={() => {
                      setActiveModel(model);
                      if (model.status === 'COMPLETED') {
                        setActiveStep('results');
                      } else if (model.status === 'FAILED') {
                        setActiveStep('training');
                        setPollingError(model.error_message || 'This run failed.');
                        setTrainingLogs(model.training_log || []);
                      } else {
                        setActiveStep('training');
                        setTrainingLogs(model.training_log || []);
                        setIsPolling(true);
                        startPolling(model.id);
                      }
                    }}
                  >
                    
                    {/* Delete Icon */}
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDeleteModel(model.id);
                      }}
                      className="absolute top-2 right-2 p-1 text-slate-650 hover:text-red-400 opacity-0 group-hover:opacity-100 transition rounded-md bg-slate-950 border border-slate-900"
                      title="Delete model binary"
                    >
                      🗑️
                    </button>

                    <div className="space-y-1">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-black text-slate-200">v{model.model_version} • {model.model_type.replace('_', ' ').toUpperCase()}</span>
                      </div>
                      
                      <div className="flex justify-between items-center text-[10px] text-slate-400 font-semibold pt-1">
                        <span>Target: <code>{model.target_column}</code></span>
                        <span>{new Date(model.created_at).toLocaleDateString()}</span>
                      </div>

                      <div className="flex items-center justify-between pt-2 border-t border-slate-900 mt-2">
                        <span className={`text-[9px] font-bold px-2 py-0.5 border rounded ${
                          model.status === 'COMPLETED'
                            ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                            : model.status === 'FAILED'
                            ? 'bg-red-950/40 border-red-500/30 text-red-400'
                            : 'bg-amber-950/40 border-amber-500/30 text-amber-400 animate-pulse'
                        }`}>
                          {model.status}
                        </span>

                        {model.status === 'COMPLETED' && model.best_score !== null && model.best_score !== undefined && (
                          <span className="text-[10px] font-mono text-cyan-400 font-bold bg-slate-900 border border-slate-800/80 px-1.5 py-0.5 rounded">
                            Score: {model.best_score.toFixed(4)}
                          </span>
                        )}
                      </div>
                    </div>

                  </div>
                );
              })
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default MlPanel;
