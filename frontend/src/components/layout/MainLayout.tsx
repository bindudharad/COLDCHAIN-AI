import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Topbar } from './Topbar';
import { apiClient } from '../../services/api';
import type { Sensor } from '../../types';

export const MainLayout: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [selectedSensorId, setSelectedSensorId] = useState<string>('CC-01');
  const [isLoading, setIsLoading] = useState(false);

  const fetchSensors = async () => {
    setIsLoading(true);
    try {
      const data = await apiClient.getSensors();
      setSensors(data);
      if (data.length > 0 && !data.find((s) => s.sensor_id === selectedSensorId)) {
        setSelectedSensorId(data[0].sensor_id);
      }
    } catch (err) {
      console.error('Failed to load sensors', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchSensors();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Sidebar isOpen={sidebarOpen} onToggle={() => setSidebarOpen(!sidebarOpen)} />
      
      <div
        className={`flex-1 flex flex-col transition-all duration-300 ${
          sidebarOpen ? 'ml-64' : 'ml-20'
        }`}
      >
        <Topbar
          sensors={sensors}
          selectedSensorId={selectedSensorId}
          onSelectSensor={setSelectedSensorId}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          onRefresh={fetchSensors}
          isLoading={isLoading}
        />

        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          <Outlet context={{ selectedSensorId, sensors, refreshSensors: fetchSensors }} />
        </main>

        <footer className="py-4 px-6 border-t border-slate-200 bg-white text-xs text-slate-500 flex flex-col sm:flex-row items-center justify-between">
          <span>ColdChain AI — Safe Trajectory NSGA-II & Real-Data MAD-TCN Forecasting</span>
          <span className="mt-1 sm:mt-0 text-pink-600 font-medium">Hohenheim & Kaggle Benchmarks Verified</span>
        </footer>
      </div>
    </div>
  );
};
