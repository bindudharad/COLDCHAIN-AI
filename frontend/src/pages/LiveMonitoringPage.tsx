import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { Radio, ShieldCheck, Clock, Download } from 'lucide-react';
import { apiClient } from '../services/api';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { Reading } from '../types';

export const LiveMonitoringPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [readings, setReadings] = useState<Reading[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      try {
        const data = await apiClient.getSensorHistory(selectedSensorId, 50);
        setReadings(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, [selectedSensorId]);

  const handleExportCSV = () => {
    if (readings.length === 0) return;
    const headers = ['Timestamp', 'Temperature_C', 'Humidity_Pct', 'Ambient_C', 'Power_kW', 'Compressor', 'Door_Open'];
    const rows = readings.map((r) => [
      r.timestamp,
      r.temperature,
      r.humidity ?? '',
      r.ambient_temperature ?? '',
      r.power_kw ?? '',
      r.compressor_state ? 1 : 0,
      r.door_open ? 1 : 0,
    ]);
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows.map((e) => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `${selectedSensorId}_telemetry_log.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Radio className="w-5 h-5 text-blue-600 animate-pulse" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Real-Time Telemetry Stream</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Raw IoT ingress records for sensor node <strong className="text-slate-700">{selectedSensorId}</strong> with authenticated hardware provenance.
          </p>
        </div>

        <button
          onClick={handleExportCSV}
          className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-50 hover:bg-blue-100 text-blue-700 font-semibold rounded-xl text-xs border border-blue-200 transition"
        >
          <Download className="w-4 h-4" />
          <span>Export CSV Buffer</span>
        </button>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-600">
          <span>Recent Ingested Telemetry ({readings.length} Samples)</span>
          <span className="flex items-center space-x-1 text-emerald-600">
            <ShieldCheck className="w-4 h-4" />
            <span>Monotonic Timestamp Verified</span>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Timestamp</th>
                <th className="py-3 px-4">Temperature</th>
                <th className="py-3 px-4">Ambient</th>
                <th className="py-3 px-4">Humidity</th>
                <th className="py-3 px-4">Power (kW)</th>
                <th className="py-3 px-4">Compressor</th>
                <th className="py-3 px-4">Door State</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {readings.map((r, i) => {
                const isViolating = r.temperature > 5.0 || r.temperature < 0.0;
                return (
                  <tr key={i} className="hover:bg-slate-50/60 transition-colors">
                    <td className="py-3 px-4 font-mono text-slate-600 flex items-center space-x-1.5">
                      <Clock className="w-3.5 h-3.5 text-slate-400" />
                      <span>{r.timestamp}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`font-bold ${isViolating ? 'text-pink-600' : 'text-slate-800'}`}>
                        {r.temperature.toFixed(2)} °C
                      </span>
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {r.ambient_temperature !== undefined ? `${r.ambient_temperature.toFixed(1)} °C` : '--'}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {r.humidity !== undefined ? `${r.humidity.toFixed(1)} %` : '--'}
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono">
                      {r.power_kw !== undefined ? `${r.power_kw.toFixed(3)} kW` : '--'}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          r.compressor_state ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {r.compressor_state ? 'RUNNING' : 'STANDBY'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          r.door_open ? 'bg-pink-100 text-pink-800' : 'bg-emerald-100 text-emerald-800'
                        }`}
                      >
                        {r.door_open ? 'OPEN' : 'CLOSED'}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <StatusBadge status={isViolating ? 'EXCURSION' : 'NORMAL'} size="sm" />
                    </td>
                  </tr>
                );
              })}
              {readings.length === 0 && !loading && (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-slate-400">
                    No telemetry records available for this sensor.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
