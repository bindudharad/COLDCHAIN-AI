import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import {
  Thermometer,
  Zap,
  ShieldAlert,
  Play,
  Pause,
  RotateCcw,
  Sliders,
  CheckCircle,
  FileCheck
} from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { apiClient } from '../services/api';
import type { DecisionData } from '../types';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export const DashboardPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [data, setData] = useState<DecisionData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await apiClient.getDashboard(selectedSensorId);
      setData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedSensorId]);

  const handleSimAction = async (action: 'start' | 'pause' | 'reset') => {
    setActionLoading(true);
    try {
      await apiClient.controlSimulation(action);
      setNotification(`Simulation state: ${action.toUpperCase()}`);
      setTimeout(() => setNotification(null), 3000);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveAudit = async () => {
    try {
      const res = await apiClient.saveCaseAudit(selectedSensorId);
      setNotification(`Snapshot saved to audit cache: ${res.case_id}`);
      setTimeout(() => setNotification(null), 4000);
    } catch (e) {
      console.error(e);
    }
  };

  const chartData = data?.forecast?.map((temp, idx) => ({
    time: `+${idx + 1}m`,
    temp: Number(temp.toFixed(2)),
  })) || [];

  return (
    <div className="space-y-6 pb-12">
      {/* Header with quick actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Cold-Chain Operational Command</h1>
            {data && <StatusBadge status={data.data_provenance} />}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time thermal monitoring, autonomous MAD-TCN inference, and physics-constrained NSGA-II actuator recommendations.
          </p>
        </div>

        <div className="flex items-center space-x-2 flex-wrap">
          <button
            onClick={() => handleSimAction('start')}
            disabled={actionLoading}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition shadow-xs"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            <span>Sim Stream</span>
          </button>
          <button
            onClick={() => handleSimAction('pause')}
            disabled={actionLoading}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
          >
            <Pause className="w-3.5 h-3.5" />
            <span>Pause</span>
          </button>
          <button
            onClick={() => handleSimAction('reset')}
            disabled={actionLoading}
            className="flex items-center space-x-1.5 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold transition"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset</span>
          </button>
          <button
            onClick={handleSaveAudit}
            className="flex items-center space-x-1.5 px-3.5 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 rounded-lg text-xs font-bold transition"
          >
            <FileCheck className="w-3.5 h-3.5" />
            <span>Audit Case</span>
          </button>
        </div>
      </div>

      {notification && (
        <div className="p-3 bg-pink-50 border border-pink-200 text-pink-800 rounded-xl text-xs font-semibold flex items-center space-x-2 animate-fade-in">
          <CheckCircle className="w-4 h-4 text-pink-600 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Temperature"
          value={data ? data.current_temperature.toFixed(2) : '--'}
          unit="°C"
          subtitle={`Sensor: ${selectedSensorId}`}
          icon={Thermometer}
          variant={data && (data.current_temperature > 5 || data.current_temperature < 0) ? 'pink' : 'blue'}
          badge="Product: Food"
        />
        <MetricCard
          title="Forecast Horizon Max"
          value={data?.forecast ? Math.max(...data.forecast).toFixed(2) : '--'}
          unit="°C"
          subtitle={`Min: ${data?.forecast ? Math.min(...data.forecast).toFixed(2) : '--'} °C`}
          icon={Thermometer}
          variant="pink"
          badge="Next 15 Min"
        />
        <MetricCard
          title="Risk Level"
          value={data?.risk?.risk_level || '--'}
          subtitle={data?.risk?.risk_reason || 'Normal trajectory'}
          icon={ShieldAlert}
          variant={data?.risk?.risk_level === 'CRITICAL' || data?.risk?.risk_level === 'HIGH' ? 'pink' : 'emerald'}
          badge={`Prob: ${data?.risk ? (data.risk.excursion_probability * 100).toFixed(0) : 0}%`}
        />
        <MetricCard
          title="NSGA-II Power / Energy"
          value={data?.recommended_solution ? data.recommended_solution.estimated_energy_kwh.toFixed(3) : '--'}
          unit="kWh"
          subtitle={`Cooling: ${data?.recommended_solution ? (data.recommended_solution.cooling_intensity * 100).toFixed(0) : '--'}% | Duty: ${data?.recommended_solution ? (data.recommended_solution.compressor_duty_cycle * 100).toFixed(0) : '--'}%`}
          icon={Zap}
          variant="slate"
          badge="15-min Interval"
        />
      </div>

      {/* Trajectory Graph & Control Recommendation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Predictive Trajectory with Dynamic Safe Corridor</h2>
              <p className="text-xs text-slate-500">Autonomous forecast across 15 discrete one-minute intervals</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Safe Limits: 0.0 °C to 5.0 °C
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#EC4899" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="time" stroke="#94A3B8" fontSize={11} />
                <YAxis domain={[-1, 7]} stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <ReferenceLine y={5.0} stroke="#EC4899" strokeWidth={1.5} strokeDasharray="4 4" label={{ value: 'Upper Limit (5.0°C)', fill: '#EC4899', fontSize: 10 }} />
                <ReferenceLine y={0.0} stroke="#3B82F6" strokeWidth={1.5} strokeDasharray="4 4" label={{ value: 'Lower Limit (0.0°C)', fill: '#3B82F6', fontSize: 10 }} />
                <Area
                  type="monotone"
                  dataKey="temp"
                  stroke="#2563EB"
                  strokeWidth={2.5}
                  fillOpacity={1}
                  fill="url(#colorTemp)"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-3 flex items-center justify-between text-xs text-slate-500">
            <span>Lookback: 60 Minutes Sensor Context</span>
            <span>Forecast Architecture: Dilated Causal Convolutional Network</span>
          </div>
        </div>

        {/* NSGA-II Recommended Actuator Setpoints */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-pink-600 font-bold text-sm mb-4">
              <Sliders className="w-4 h-4" />
              <span>Recommended Actuator Setpoints</span>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Compressor Duty Cycle (d)</span>
                  <span className="text-blue-600 font-bold">
                    {data?.recommended_solution ? `${(data.recommended_solution.compressor_duty_cycle * 100).toFixed(1)}%` : '--'}
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all duration-500"
                    style={{
                      width: `${data?.recommended_solution ? Math.min(data.recommended_solution.compressor_duty_cycle * 100, 100) : 0}%`,
                    }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between text-xs font-semibold text-slate-700 mb-1">
                  <span>Cooling Intensity (u)</span>
                  <span className="text-pink-600 font-bold">
                    {data?.recommended_solution ? `${(data.recommended_solution.cooling_intensity * 100).toFixed(1)}%` : '--'}
                  </span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-pink-500 h-2.5 rounded-full transition-all duration-500"
                    style={{
                      width: `${data?.recommended_solution ? Math.min(data.recommended_solution.cooling_intensity * 100, 100) : 0}%`,
                    }}
                  ></div>
                </div>
              </div>

              <div className="p-3.5 bg-slate-50 rounded-xl border border-slate-200/80 space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-slate-500">Predicted Interval Energy:</span>
                  <span className="font-bold text-slate-800">
                    {data?.recommended_solution?.estimated_energy_kwh !== undefined ? `${data.recommended_solution.estimated_energy_kwh.toFixed(4)} kWh` : '--'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Predicted Endpoint Temp:</span>
                  <span className="font-bold text-slate-800">
                    {data?.recommended_solution?.expected_temperature !== undefined ? `${data.recommended_solution.expected_temperature.toFixed(2)} °C` : '--'}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Trajectory Excursion Min:</span>
                  <span className="font-bold text-pink-600">
                    {data?.recommended_solution?.predicted_excursion_duration_min !== undefined ? `${data.recommended_solution.predicted_excursion_duration_min.toFixed(1)} min` : '0.0 min'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-600">Notice:</span> Physical temperature constraints are validated across all 15 intermediate trajectory timesteps.
          </div>
        </div>
      </div>
    </div>
  );
};
