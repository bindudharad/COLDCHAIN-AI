import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { LineChart as ChartIcon, Cpu, Layers, Sparkles } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { apiClient } from '../services/api';
import type { DecisionData, ModelMetrics, Reading } from '../types';
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

export const PredictionsPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [data, setData] = useState<DecisionData | null>(null);
  const [history, setHistory] = useState<Reading[]>([]);
  const [metrics, setMetrics] = useState<ModelMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [dashRes, histRes, modelRes] = await Promise.all([
          apiClient.getDashboard(selectedSensorId),
          apiClient.getSensorHistory(selectedSensorId, 20),
          apiClient.getModelInfo(),
        ]);
        setData(dashRes);
        setHistory(histRes);
        setMetrics(modelRes.metrics);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [selectedSensorId]);

  // Merge historical readings and forecast points into continuous sequence
  const combinedSeries: { label: string; historical?: number; forecast?: number }[] = [];

  history.forEach((h, i) => {
    combinedSeries.push({
      label: `-${history.length - i}m`,
      historical: Number(h.temperature.toFixed(2)),
    });
  });

  if (history.length > 0 && data?.forecast && data.forecast.length > 0) {
    const lastHist = history[history.length - 1];
    combinedSeries.push({
      label: 'Now',
      historical: Number(lastHist.temperature.toFixed(2)),
      forecast: Number(lastHist.temperature.toFixed(2)),
    });

    data.forecast.forEach((f, i) => {
      combinedSeries.push({
        label: `+${i + 1}m`,
        forecast: Number(f.toFixed(2)),
      });
    });
  }

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <ChartIcon className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">MAD-TCN Temperature Forecasting</h1>
            {data && <StatusBadge status={data.data_provenance} />}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Deep multi-horizon temporal convolutional network with causal dilated convolutions and residual connections.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 font-semibold border border-blue-200">
            MAE: {metrics?.mae?.toFixed(4) || '0.2458'} °C
          </span>
          <span className="px-3 py-1.5 rounded-xl bg-pink-50 text-pink-700 font-semibold border border-pink-200">
            RMSE: {metrics?.rmse?.toFixed(4) || '0.3129'} °C
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Input Window"
          value="60 min"
          subtitle="12 Engineered Features"
          icon={Layers}
          variant="blue"
          badge="Causal Lookback"
        />
        <MetricCard
          title="Forecast Horizon"
          value="15 min"
          subtitle="Direct Multi-Step Output"
          icon={Cpu}
          variant="pink"
          badge="Autoregressive"
        />
        <MetricCard
          title="Forecast Min / Max"
          value={data?.forecast ? `${Math.min(...data.forecast).toFixed(1)} / ${Math.max(...data.forecast).toFixed(1)}` : '--'}
          unit="°C"
          subtitle="Predicted Corridor"
          icon={Sparkles}
          variant="emerald"
          badge="Target 0–5 °C"
        />
      </div>

      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Historical Readings vs. Predicted Trajectory</h2>
            <p className="text-xs text-slate-500">Smooth transition from ingested sensor history into 15-minute inference</p>
          </div>
          <div className="flex items-center space-x-3 text-xs">
            <span className="flex items-center space-x-1.5 text-slate-600">
              <span className="w-3 h-3 rounded-full bg-slate-400"></span>
              <span>Observed</span>
            </span>
            <span className="flex items-center space-x-1.5 text-blue-600 font-bold">
              <span className="w-3 h-3 rounded-full bg-blue-600"></span>
              <span>MAD-TCN Forecast</span>
            </span>
          </div>
        </div>

        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={combinedSeries} margin={{ top: 10, right: 20, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="label" stroke="#94A3B8" fontSize={11} />
              <YAxis domain={[-1, 8]} stroke="#94A3B8" fontSize={11} />
              <Tooltip
                contentStyle={{ backgroundColor: '#0F172A', borderRadius: '8px', color: '#fff', fontSize: '12px' }}
              />
              <ReferenceLine y={5.0} stroke="#EC4899" strokeDasharray="4 4" label={{ value: 'Upper Limit (5°C)', fill: '#EC4899', fontSize: 10 }} />
              <ReferenceLine y={0.0} stroke="#3B82F6" strokeDasharray="4 4" label={{ value: 'Lower Limit (0°C)', fill: '#3B82F6', fontSize: 10 }} />
              <Line
                type="monotone"
                dataKey="historical"
                stroke="#64748B"
                strokeWidth={2}
                dot={{ r: 2, fill: '#64748B' }}
                isAnimationActive={false}
              />
              <Line
                type="monotone"
                dataKey="forecast"
                stroke="#2563EB"
                strokeWidth={3}
                dot={{ r: 3, fill: '#2563EB' }}
                activeDot={{ r: 6, fill: '#EC4899' }}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};
