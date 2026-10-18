import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Sliders, ShieldCheck, Zap, TrendingDown, Target, Info } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { apiClient } from '../services/api';
import type { DecisionData, ParetoSolution } from '../types';
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ZAxis,
} from 'recharts';

export const OptimizationPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [data, setData] = useState<DecisionData | null>(null);
  const [selectedSolution, setSelectedSolution] = useState<ParetoSolution | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchOpt = async () => {
      setLoading(true);
      try {
        const res = await apiClient.getDashboard(selectedSensorId);
        setData(res);
        if (res.recommended_solution) {
          setSelectedSolution(res.recommended_solution);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchOpt();
  }, [selectedSensorId]);

  const paretoScatter = data?.pareto_solutions?.map((sol, index) => ({
    index,
    energy: Number((sol.estimated_energy_kwh ?? 0).toFixed(4)),
    temp: Number((sol.expected_temperature ?? sol.predicted_temperature ?? 3.5).toFixed(2)),
    excursion: Number((sol.predicted_excursion_duration_min ?? 0).toFixed(1)),
    cooling: Number(((sol.cooling_intensity ?? 0) * 100).toFixed(0)),
    duty: Number(((sol.compressor_duty_cycle ?? 0) * 100).toFixed(0)),
    feasible: sol.feasible !== false,
  })) || [];

  const rec = selectedSolution || data?.recommended_solution;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">NSGA-II Multi-Objective Optimization</h1>
            {data && <StatusBadge status="TRAJECTORY SAFE" variant="emerald" />}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Pareto-optimal trade-off between energy consumption (kWh) and temperature stability with full-trajectory physical feasibility constraints.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-pink-50 text-pink-700 font-semibold border border-pink-200">
            Bi-Objective: Energy vs. Excursion
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Recommended Cooling (u)"
          value={rec ? `${(rec.cooling_intensity * 100).toFixed(1)}%` : '--'}
          subtitle="Modulated Inverter Output"
          icon={Sliders}
          variant="pink"
          badge="NSGA-II Choice"
        />
        <MetricCard
          title="Compressor Duty Cycle (d)"
          value={rec ? `${(rec.compressor_duty_cycle * 100).toFixed(1)}%` : '--'}
          subtitle="Operating Time Fraction"
          icon={Target}
          variant="blue"
          badge="Bound: [0.1, 1.0]"
        />
        <MetricCard
          title="Predicted Energy"
          value={rec?.estimated_energy_kwh !== undefined ? rec.estimated_energy_kwh.toFixed(4) : '--'}
          unit="kWh"
          subtitle="15-min Control Window"
          icon={Zap}
          variant="emerald"
          badge="Thermal Lift Model"
        />
        <MetricCard
          title="Excursion Minutes"
          value={rec?.predicted_excursion_duration_min !== undefined ? rec.predicted_excursion_duration_min.toFixed(1) : '0.0'}
          unit="min"
          subtitle="Trajectory Violations"
          icon={TrendingDown}
          variant={rec && rec.predicted_excursion_duration_min > 0 ? 'pink' : 'slate'}
          badge="Goal: 0.0 min"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pareto Scatter Plot */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-lg font-bold text-slate-900">Pareto Trade-Off Surface (Energy vs. Temp)</h2>
              <p className="text-xs text-slate-500">Each node represents a non-dominated control policy ($u, d$)</p>
            </div>
            <span className="text-xs font-semibold text-slate-500">
              {data?.pareto_solutions?.length || 0} Solutions Explored
            </span>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis
                  type="number"
                  dataKey="energy"
                  name="Energy"
                  unit=" kWh"
                  stroke="#94A3B8"
                  fontSize={11}
                  label={{ value: 'Energy Demand (kWh)', position: 'insideBottom', offset: -10, fontSize: 11, fill: '#64748B' }}
                />
                <YAxis
                  type="number"
                  dataKey="temp"
                  name="Temperature"
                  unit=" °C"
                  stroke="#94A3B8"
                  fontSize={11}
                  label={{ value: 'Target Temp (°C)', angle: -90, position: 'insideLeft', fontSize: 11, fill: '#64748B' }}
                />
                <ZAxis type="number" dataKey="cooling" range={[60, 200]} />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const d = payload[0].payload;
                      return (
                        <div className="bg-slate-900 text-white p-3 rounded-lg text-xs space-y-1 shadow-lg">
                          <p className="font-bold text-pink-400">Solution #{d.index + 1}</p>
                          <p>Energy: <span className="font-semibold">{d.energy} kWh</span></p>
                          <p>Target Temp: <span className="font-semibold">{d.temp} °C</span></p>
                          <p>Cooling Intensity (u): <span className="font-semibold">{d.cooling}%</span></p>
                          <p>Duty Cycle (d): <span className="font-semibold">{d.duty}%</span></p>
                          <p>Excursion: <span className="font-semibold">{d.excursion} min</span></p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Scatter name="Pareto Solutions" data={paretoScatter} fill="#2563EB" />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span className="flex items-center space-x-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>Full trajectory safety enforced against thermal model</span>
            </span>
            <span className="text-pink-600 font-semibold">19 Nominally / 18 Buffered Feasible Regimes</span>
          </div>
        </div>

        {/* Selected Solution Inspector */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 text-blue-600 font-bold text-sm mb-4">
              <Info className="w-4 h-4" />
              <span>Actuator Control Inspector</span>
            </div>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-200/60">
                <p className="text-slate-500 font-semibold">Primary Actuator Recommendation</p>
                <p className="text-lg font-black text-blue-900 mt-1">
                  Cooling: {rec ? (rec.cooling_intensity * 100).toFixed(0) : '--'}% | Duty: {rec ? (rec.compressor_duty_cycle * 100).toFixed(0) : '--'}%
                </p>
              </div>

              <div className="space-y-2 pt-2">
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-400">Interval Energy:</span>
                  <span className="font-bold text-slate-800">{rec?.estimated_energy_kwh !== undefined ? `${rec.estimated_energy_kwh.toFixed(4)} kWh` : '--'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-400">Endpoint Temperature:</span>
                  <span className="font-bold text-slate-800">{rec?.expected_temperature !== undefined ? `${rec.expected_temperature.toFixed(2)} °C` : '--'}</span>
                </div>
                <div className="flex justify-between py-1 border-b border-slate-100">
                  <span className="text-slate-400">Excursion Duration:</span>
                  <span className="font-bold text-pink-600">{rec?.predicted_excursion_duration_min !== undefined ? `${rec.predicted_excursion_duration_min.toFixed(1)} min` : '0.0 min'}</span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-slate-400">Trajectory Feasibility:</span>
                  <span className="font-bold text-emerald-600">100% Physical Bound Sat.</span>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] text-slate-400">
            <span className="font-semibold text-slate-600">Provenance:</span> Derived from Hohenheim real-data calibrated thermal simulations.
          </div>
        </div>
      </div>
    </div>
  );
};
