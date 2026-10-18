import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './components/layout/MainLayout';
import { HomePage } from './pages/HomePage';
import { DashboardPage } from './pages/DashboardPage';
import { LiveMonitoringPage } from './pages/LiveMonitoringPage';
import { PredictionsPage } from './pages/PredictionsPage';
import { OptimizationPage } from './pages/OptimizationPage';
import { AlertsPage } from './pages/AlertsPage';
import { SensorsPage } from './pages/SensorsPage';
import { ModelPage } from './pages/ModelPage';
import { DatasetsPage } from './pages/DatasetsPage';
import { ReportsPage } from './pages/ReportsPage';
import { UploadPage } from './pages/UploadPage';
import { MethodologyPage } from './pages/MethodologyPage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<HomePage />} />
          <Route path="dashboard" element={<DashboardPage />} />
          <Route path="live-monitoring" element={<LiveMonitoringPage />} />
          <Route path="predictions" element={<PredictionsPage />} />
          <Route path="optimization" element={<OptimizationPage />} />
          <Route path="alerts" element={<AlertsPage />} />
          <Route path="sensors" element={<SensorsPage />} />
          <Route path="model" element={<ModelPage />} />
          <Route path="datasets" element={<DatasetsPage />} />
          <Route path="reports" element={<ReportsPage />} />
          <Route path="upload" element={<UploadPage />} />
          <Route path="methodology" element={<MethodologyPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
