import React from 'react';
import { Database, FileText, CheckCircle2, ShieldAlert } from 'lucide-react';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { DatasetItem } from '../types';

const DATASETS: DatasetItem[] = [
  {
    name: 'simulated_cold_chain.csv',
    path: 'data/raw/simulated_cold_chain.csv',
    domain: 'Cold-Chain Logistics (0–5 °C)',
    source: 'Calibrated Thermodynamic Physical Model',
    provenance: 'SIMULATION',
    records: 12000,
    features: 10,
    role: 'Baseline Demonstration Ground Truth',
  },
  {
    name: 'iot_temperature_readings.csv',
    path: 'Datasets/02_iot_temperature_readings/',
    domain: 'Ambient Living Space (21–51 °C)',
    source: 'ESP8266 Sensor Node (Kaggle)',
    provenance: 'PUBLIC_DATASET',
    records: 97606,
    features: 5,
    role: 'External Physical Hardware Validation',
  },
  {
    name: 'energy_consumption_prediction.csv',
    path: 'Datasets/03_energy_consumption/',
    domain: 'Building HVAC Energy Demand',
    source: 'Residential/Commercial Buildings (Kaggle)',
    provenance: 'PUBLIC_DATASET',
    records: 1000,
    features: 5,
    role: 'Thermal-Environmental Energy Modeling',
  },
  {
    name: 'eviot_predictive_maintenance.csv',
    path: 'Datasets/04_eviot_predictive_maintenance/',
    domain: 'Electric Vehicle Battery Telemetry',
    source: 'High-Frequency Thermal Stress (Kaggle)',
    provenance: 'PUBLIC_DATASET',
    records: 175393,
    features: 5,
    role: 'Big Data Scalability & Throughput Benchmark',
  },
  {
    name: 'journey_to_zero_electricity.csv',
    path: 'Datasets/05_electricity_forecasting/',
    domain: 'Municipal Electrical Grid Demand',
    source: 'Weather-Dependent Power Load (Kaggle)',
    provenance: 'PUBLIC_DATASET',
    records: 8592,
    features: 4,
    role: 'Macro Electricity Consumption Correlation',
  },
];

export const DatasetsPage: React.FC = () => {
  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Database className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Datasets Inventory & Scientific Provenance</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Complete data inventory classified by origin, provenance, and experimental purpose with zero simulated data obfuscation.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-pink-50 text-pink-700 font-semibold border border-pink-200">
            5 Registered Repositories
          </span>
        </div>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
          <span>Datasets Catalog & Provenance Classification</span>
          <span className="text-slate-400">Total Records: 294,591 Rows</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Dataset Name</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Source / Origin</th>
                <th className="py-3 px-4">Provenance</th>
                <th className="py-3 px-4">Records</th>
                <th className="py-3 px-4">Features</th>
                <th className="py-3 px-4">Scientific Role</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {DATASETS.map((ds, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                  <td className="py-3.5 px-4 font-mono font-bold text-slate-900 flex items-center space-x-2">
                    <FileText className="w-4 h-4 text-blue-500 shrink-0" />
                    <span>{ds.name}</span>
                  </td>
                  <td className="py-3.5 px-4 text-slate-700 font-medium">{ds.domain}</td>
                  <td className="py-3.5 px-4 text-slate-500">{ds.source}</td>
                  <td className="py-3.5 px-4">
                    <StatusBadge status={ds.provenance} size="sm" />
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-800 font-semibold">
                    {ds.records.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 font-mono text-slate-600">{ds.features}</td>
                  <td className="py-3.5 px-4 text-slate-600 font-medium">{ds.role}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Provenance Policy Box */}
      <div className="p-6 bg-gradient-to-r from-blue-50 via-slate-50 to-pink-50 rounded-2xl border border-blue-200/60 shadow-xs">
        <h3 className="text-sm font-bold text-slate-900 flex items-center space-x-2 mb-2">
          <ShieldAlert className="w-4 h-4 text-pink-600" />
          <span>Scientific Provenance Policy</span>
        </h3>
        <p className="text-xs text-slate-600 leading-relaxed">
          In strict accordance with scientific integrity standards, ColdChain AI maintains complete transparency across all data sources. Simulated data is explicitly labeled as <code>SIMULATION</code>. Public research benchmarks from Kaggle are categorized as <code>PUBLIC_DATASET</code>. Live hardware streams from authorized sensor nodes are stamped with <code>REAL_SENSOR</code> only upon passing server-side HMAC and token authentication.
        </p>
      </div>
    </div>
  );
};
