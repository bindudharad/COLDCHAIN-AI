import React from 'react';
import { Menu, RefreshCw, Cpu, ShieldCheck } from 'lucide-react';
import type { Sensor } from '../../types';

interface TopbarProps {
  sensors: Sensor[];
  selectedSensorId: string;
  onSelectSensor: (sensorId: string) => void;
  onToggleSidebar: () => void;
  onRefresh: () => void;
  isLoading?: boolean;
}

export const Topbar: React.FC<TopbarProps> = ({
  sensors,
  selectedSensorId,
  onSelectSensor,
  onToggleSidebar,
  onRefresh,
  isLoading = false,
}) => {
  const currentSensor = sensors.find((s) => s.sensor_id === selectedSensorId);

  return (
    <header className="h-16 bg-white/95 backdrop-blur-md border-b border-slate-200 sticky top-0 z-30 flex items-center justify-between px-6 shadow-xs">
      <div className="flex items-center space-x-4">
        <button
          onClick={onToggleSidebar}
          className="p-2 rounded-lg text-slate-500 hover:text-slate-800 hover:bg-slate-100 transition-colors"
          title="Toggle Sidebar"
        >
          <Menu className="w-5 h-5" />
        </button>

        <div className="flex items-center space-x-2">
          <label htmlFor="sensor-select" className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            Node:
          </label>
          <select
            id="sensor-select"
            value={selectedSensorId}
            onChange={(e) => onSelectSensor(e.target.value)}
            className="text-sm font-semibold text-slate-800 bg-slate-50 border border-slate-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all shadow-xs"
          >
            {sensors.map((s) => (
              <option key={s.sensor_id} value={s.sensor_id}>
                {s.sensor_id} ({s.location || s.product_type})
              </option>
            ))}
          </select>
        </div>

        {currentSensor && (
          <div className="hidden md:flex items-center space-x-2 text-xs">
            <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-blue-700 font-medium border border-blue-200/60">
              {currentSensor.product_type || 'Cold Storage'}
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-pink-50 text-pink-700 font-medium border border-pink-200/60">
              Safe 0–5 °C
            </span>
          </div>
        )}
      </div>

      <div className="flex items-center space-x-3">
        <div className="hidden sm:flex items-center space-x-2 px-3 py-1 bg-slate-100 rounded-full text-xs font-medium text-slate-600">
          <ShieldCheck className="w-4 h-4 text-emerald-500" />
          <span>Active Ingestion</span>
        </div>

        <button
          onClick={onRefresh}
          disabled={isLoading}
          className={`flex items-center space-x-1 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 rounded-lg text-xs font-semibold border border-blue-200 transition-all ${
            isLoading ? 'opacity-50 cursor-not-allowed' : ''
          }`}
          title="Refresh Data"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Sync</span>
        </button>

        <div className="flex items-center space-x-2 border-l border-slate-200 pl-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-pink-500 to-rose-400 flex items-center justify-center text-white text-xs font-bold shadow-xs">
            <Cpu className="w-4 h-4" />
          </div>
        </div>
      </div>
    </header>
  );
};
