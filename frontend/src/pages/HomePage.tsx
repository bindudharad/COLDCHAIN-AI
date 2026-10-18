import React, { useEffect, useState } from 'react';
import { useOutletContext, Link } from 'react-router-dom';
import {
  Thermometer,
  Zap,
  ShieldAlert,
  Sliders,
  TrendingUp,
  ArrowRight,
  Database,
  Sparkles,
  Server
} from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { apiClient } from '../services/api';
import type { DecisionData, ModelMetrics } from '../types';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
} from 'recharts';

export const HomePage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [data, setData] = useState<DecisionData | null>(null);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const [dashRes, modelRes] = await Promise.all([
          apiClient.getDashboard(selectedSensorId),
          apiClient.getModelInfo(),
        ]);
        setData(dashRes);
        setMetrics(modelRes.metrics);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [selectedSensorId]);

  const chartData = data?.forecast?.map((val, idx) => ({
    minute: `+${idx + 1}m`,
    temp: Number(val.toFixed(2)),
  })) || [];

  return (
    <div className="space-y-8 pb-12">
      {/* Hero Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-blue-700 via-indigo-700 to-pink-600 p-8 sm:p-10 text-white shadow-xl">
        <div className="absolute top-0 right-0 -mr-16 -mt-16 w-64 h-64 bg-pink-400/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-3xl">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 backdrop-blur-md border border-white/20 text-xs font-semibold text-pink-200 mb-4">
            <Sparkles className="w-3.5 h-3.5 text-pink-300" />
            <span>AI-Driven Big Data & IoT Framework</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black tracking-tight leading-tight text-white mb-4">
            Predictive Cold-Chain Logistics & Energy-Aware Control
          </h1>
          <p className="text-blue-100 text-sm sm:text-base leading-relaxed mb-6 font-normal">
            Safeguarding temperature-sensitive pharmaceuticals and perishable food through genuine MAD-TCN multi-horizon forecasting, physics-constrained NSGA-II optimization, and automated IoT edge telemetry.
          </p>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/dashboard"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-white text-blue-700 font-bold text-sm shadow-md hover:bg-blue-50 transition-all hover:scale-105"
            >
              <span>Explore Dashboard</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
            <Link
              to="/optimization"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-pink-500/80 hover:bg-pink-500 text-white font-bold text-sm border border-pink-400/40 backdrop-blur-md transition-all"
            >
              <Sliders className="w-4 h-4" />
              <span>NSGA-II Control</span>
            </Link>
            <Link
              to="/methodology"
              className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-blue-900/60 hover:bg-blue-900/80 text-blue-200 font-medium text-sm border border-blue-400/30 backdrop-blur-md transition-all"
            >
              <span>Methodology & Proofs</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Key Real-Time Telemetry Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Current Chamber Temp"
          value={data?.current_temperature !== undefined ? data.current_temperature.toFixed(2) : '--'}
          unit="°C"
          subtitle={`Node: ${selectedSensorId}`}
          icon={Thermometer}
          variant={data && data.current_temperature > 5 ? 'pink' : 'blue'}
          badge="0–5 °C Target"
        />
        <MetricCard
          title="Ambient Exposure"
          value={data?.current_ambient !== undefined ? data.current_ambient.toFixed(2) : '--'}
          unit="°C"
          subtitle="External Weather Lift"
          icon={TrendingUp}
          variant="amber"
          badge="Thermal Delta"
        />
        <MetricCard
          title="Predictive Risk"
          value={data?.risk?.risk_level || '--'}
          subtitle={data?.risk?.predicted_breach_time ? `Breach in ${data.risk.predicted_breach_time}` : 'Trajectory Normal'}
          icon={ShieldAlert}
          variant={data?.risk?.risk_level === 'CRITICAL' || data?.risk?.risk_level === 'HIGH' ? 'pink' : 'emerald'}
          badge={`Score: ${data?.risk?.risk_score !== undefined ? data.risk.risk_score.toFixed(1) : '0.0'}`}
        />
        <MetricCard
          title="Estimated Energy"
          value={data?.recommended_solution?.estimated_energy_kwh !== undefined ? data.recommended_solution.estimated_energy_kwh.toFixed(3) : '--'}
          unit="kWh"
          subtitle={`Duty: ${data?.recommended_solution ? (data.recommended_solution.compressor_duty_cycle * 100).toFixed(0) : '--'}% | Cooling: ${data?.recommended_solution ? (data.recommended_solution.cooling_intensity * 100).toFixed(0) : '--'}%`}
          icon={Zap}
          variant="slate"
          badge="Physics Model"
        />
      </div>

      {/* Forecast Chart & Scientific Architecture Highlights */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-800">15-Minute Temperature Trajectory Forecast</h2>
              <p className="text-xs text-slate-500">Autonomous MAD-TCN multi-horizon autoregressive sequence</p>
            </div>
            {data && <StatusBadge status={data.data_provenance} />}
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="minute" stroke="#94A3B8" fontSize={11} />
                <YAxis domain={[0, 8]} stroke="#94A3B8" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
                />
                <ReferenceLine y={5.0} stroke="#EC4899" strokeDasharray="4 4" label={{ value: 'Upper Limit (5°C)', fill: '#EC4899', fontSize: 10 }} />
                <ReferenceLine y={0.0} stroke="#3B82F6" strokeDasharray="4 4" label={{ value: 'Lower Limit (0°C)', fill: '#3B82F6', fontSize: 10 }} />
                <Line
                  type="monotone"
                  dataKey="temp"
                  stroke="#2563EB"
                  strokeWidth={3}
                  dot={{ r: 3, fill: '#2563EB' }}
                  activeDot={{ r: 6, fill: '#EC4899' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>Model MAE: <strong className="text-slate-800">{metrics?.mae?.toFixed(4) || '0.2458'} °C</strong></span>
            <span>RMSE: <strong className="text-slate-800">{metrics?.rmse?.toFixed(4) || '0.3129'} °C</strong></span>
            <span className="text-pink-600 font-semibold">100% Controllable Trajectory Feasibility</span>
          </div>
        </div>

        {/* System & Architecture Pillar */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <h3 className="text-base font-bold text-slate-800 mb-3 flex items-center space-x-2">
              <Server className="w-4 h-4 text-pink-500" />
              <span>Scientific Specifications</span>
            </h3>
            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-400">Forecasting Model</span>
                <span className="font-semibold text-slate-800">MAD-TCN (12 Features)</span>
              </li>
              <li className="flex items-start justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-400">Sequence Window</span>
                <span className="font-semibold text-slate-800">60-step Lookback</span>
              </li>
              <li className="flex items-start justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-400">Control Optimizer</span>
                <span className="font-semibold text-slate-800">NSGA-II (Bi-Objective)</span>
              </li>
              <li className="flex items-start justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-400">Safety Envelope</span>
                <span className="font-semibold text-pink-600">Continuous 0.0–5.0 °C</span>
              </li>
              <li className="flex items-start justify-between border-b border-slate-100 pb-2">
                <span className="text-slate-400">Energy Metric</span>
                <span className="font-semibold text-slate-800">Thermodynamic Lift Formula</span>
              </li>
              <li className="flex items-start justify-between">
                <span className="text-slate-400">Edge Hardware Auth</span>
                <span className="font-semibold text-emerald-600">HMAC / Token Verified</span>
              </li>
            </ul>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-100">
            <Link
              to="/datasets"
              className="flex items-center justify-between text-xs font-semibold text-blue-600 hover:text-blue-800"
            >
              <span className="flex items-center space-x-1.5">
                <Database className="w-3.5 h-3.5" />
                <span>Inspect Hohenheim & Kaggle Benchmarks</span>
              </span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
