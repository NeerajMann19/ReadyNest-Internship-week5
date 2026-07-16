import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ErrorBoundary } from './components/layout/ErrorBoundary';
import { ProtectedLayout } from './layouts/ProtectedLayout';

// Import Pages
import { Login } from './pages/auth/Login';
import { Register } from './pages/auth/Register';
import { Dashboard } from './pages/dashboard/Dashboard';
import { DatasetList } from './pages/datasets/DatasetList';
import { DatasetImport } from './pages/datasets/DatasetImport';
import { DatasetDetail } from './pages/datasets/DatasetDetail';
import { DatasetCompare } from './pages/datasets/DatasetCompare';
import { ReportsList } from './pages/reports/ReportsList';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ErrorBoundary>
          <Routes>
            {/* Public Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Protected Workspace Routes */}
            <Route element={<ProtectedLayout />}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              
              {/* Dataset Management Slices */}
              <Route path="/datasets" element={<DatasetList />} />
              <Route path="/datasets/import" element={<DatasetImport />} />
              <Route path="/datasets/:id" element={<DatasetDetail />} />
              
              {/* Nested paths for deep links are handled within DatasetDetail tabs */}
              <Route path="/datasets/:id/preview" element={<DatasetDetail />} />
              <Route path="/datasets/:id/profile" element={<DatasetDetail />} />
              <Route path="/datasets/:id/clean" element={<DatasetDetail />} />
              <Route path="/datasets/:id/eda" element={<DatasetDetail />} />
              <Route path="/datasets/:id/insights" element={<DatasetDetail />} />
              <Route path="/datasets/:id/reports" element={<DatasetDetail />} />
              <Route path="/datasets/:id/ml" element={<DatasetDetail />} />
              
              {/* Version Comparison */}
              <Route path="/datasets/:id/compare" element={<DatasetCompare />} />

              {/* Reports Management */}
              <Route path="/reports" element={<ReportsList />} />
            </Route>

            {/* Catch-all Redirect */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </ErrorBoundary>
      </AuthProvider>
    </BrowserRouter>
  );
}
