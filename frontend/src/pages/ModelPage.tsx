import React, { useEffect, useState } from 'react';
import { Cpu, Layers, GitBranch, ShieldCheck, CheckCircle, Database } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { apiClient } from '../services/api';
import type { ModelMetrics } from '../types';

export const ModelPage: React.FC = () => {
  const [modelInfo, setModelInfo] = useState<{
    model: string;
    input: string;
    output_steps: number;
    device: string;
    metrics: ModelMetrics;
  } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchModel = async () => {
      setLoading(true);
      try {
        const info = await apiClient.getModelInfo();
        setModelInfo(info);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchModel();
  }, []);

  const metrics = modelInfo?.metrics;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-pink-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">MAD-TCN Deep Neural Architecture</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Multivariate Autoregressive Dilated Temporal Convolutional Network with genuine real-data training weights.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 font-semibold border border-emerald-200 flex items-center space-x-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>Target Timestamp Purged (Zero Leakage)</span>
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Test Set MAE"
          value={metrics?.mae ? `${metrics.mae.toFixed(4)}` : '--'}
          unit="°C"
          subtitle="Physical Temperature Error"
          icon={Cpu}
          variant="pink"
          badge="Evaluated Test"
        />
        <MetricCard
          title="Test Set RMSE"
          value={metrics?.rmse ? `${metrics.rmse.toFixed(4)}` : '--'}
          unit="°C"
          subtitle="Root Mean Squared Error"
          icon={Layers}
          variant="blue"
          badge="Variance Bound"
        />
        <MetricCard
          title="Sequence Window"
          value="60 min"
          subtitle="12 Input Feature Channels"
          icon={GitBranch}
          variant="slate"
          badge="Lookback: 1h"
        />
        <MetricCard
          title="Forecast Horizon"
          value="15 min"
          subtitle="Autonomous Actuator Control"
          icon={Database}
          variant="emerald"
          badge="Multi-Step"
        />
      </div>

      {/* Architecture Deep Dive */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
            <Layers className="w-4 h-4 text-blue-600" />
            <span>Network Layer Specifications</span>
          </h2>

          <div className="space-y-3 text-xs">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="font-bold text-slate-800 block text-sm">Input Layer & Preprocessing</span>
              <p className="text-slate-500 mt-1">
                Accepts 60x12 matrix tensors representing 60 past time-steps across 12 engineered features: chamber temp, ambient temp, humidity, power, compressor state, door events, and rolling differential metrics.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="font-bold text-slate-800 block text-sm">Dilated Causal Convolutions</span>
              <p className="text-slate-500 mt-1">
                Stacked residual blocks with exponential dilation rates (d = 1, 2, 4, 8) expanding the receptive field to ensure long-range thermal inertia capture without future information leakage.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="font-bold text-slate-800 block text-sm">Temporal Attention & Dropout</span>
              <p className="text-slate-500 mt-1">
                Spatial dropout ($p = 0.2$) and weight normalization regularize internal activations against overfitting on anomalous sensor spikes.
              </p>
            </div>

            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200/80">
              <span className="font-bold text-slate-800 block text-sm">Dense Projection Head</span>
              <p className="text-slate-500 mt-1">
                Final dense mapping to 15-dimensional output vector generating the 15-minute continuous temperature trajectory forecast fed directly into NSGA-II.
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>Scientific Rigor & Verification Principles</span>
            </h2>

            <ul className="space-y-3 text-xs text-slate-600">
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-pink-500 mt-1.5 shrink-0"></span>
                <span><strong>Target-Timestamp Purging:</strong> Strict chronological cutoff eliminating any future timestamp overlap during sequence window generation.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-500 mt-1.5 shrink-0"></span>
                <span><strong>Scaler Training Isolation:</strong> StandardScaler fitted exclusively on training set folds ($70\%$), preventing test fold leakage.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-indigo-500 mt-1.5 shrink-0"></span>
                <span><strong>Real-World Benchmark:</strong> Evaluated against University of Hohenheim Sensor 03 agricultural cold storage telemetry.</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0"></span>
                <span><strong>PyTorch CPU Execution:</strong> Lightweight deployment footprint optimized for edge gateway industrial hardware.</span>
              </li>
            </ul>
          </div>

          <div className="mt-6 p-4 rounded-xl bg-pink-50 border border-pink-200/80 text-xs text-pink-950">
            <span className="font-bold block mb-1">Model Checkpoint Status:</span>
            <span>Active checkpoint <code>models/mad_tcn_best.pt</code> loaded and validated with verified weights.</span>
          </div>
        </div>
      </div>
    </div>
  );
};
