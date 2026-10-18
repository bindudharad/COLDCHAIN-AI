import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { ShieldCheck, MapPin, Activity, Thermometer, Zap } from 'lucide-react';
import { apiClient } from '../services/api';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import type { Sensor } from '../types';

export const SensorsPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [sensors, setSensors] = useState<Sensor[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSensors = async () => {
      setLoading(true);
      try {
        const data = await apiClient.getSensors();
        setSensors(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchSensors();
  }, []);

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Industrial IoT Sensor Network</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Registered edge nodes across mobile refrigerated transport vehicles and stationary cold storage chambers.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 font-semibold border border-blue-200">
            {sensors.length} Connected Nodes
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {sensors.map((s) => {
          const isSelected = s.sensor_id === selectedSensorId;
          const isTempWarning = s.latest_temperature && (s.latest_temperature > 5 || s.latest_temperature < 0);
          return (
            <div
              key={s.sensor_id}
              className={`bg-white rounded-2xl p-6 border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'border-blue-500 ring-2 ring-blue-500/20 shadow-md'
                  : 'border-slate-200 hover:border-slate-300 shadow-xs'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center space-x-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 font-bold text-xs">
                      {s.sensor_id.slice(-2)}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm">{s.sensor_id}</h3>
                      <p className="text-[11px] text-slate-400 flex items-center space-x-1">
                        <MapPin className="w-3 h-3" />
                        <span>{s.location || 'Mobile Unit'}</span>
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={s.active ? 'ACTIVE' : 'OFFLINE'} size="sm" />
                </div>

                <div className="grid grid-cols-2 gap-3 my-4 p-3 bg-slate-50 rounded-xl text-xs">
                  <div>
                    <span className="text-slate-400 block mb-0.5">Latest Temp</span>
                    <span className={`text-base font-bold ${isTempWarning ? 'text-pink-600' : 'text-slate-900'}`}>
                      {s.latest_temperature !== undefined && s.latest_temperature !== null ? `${Number(s.latest_temperature).toFixed(2)} °C` : '--'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-0.5">Power Load</span>
                    <span className="text-base font-bold text-slate-900">
                      {s.latest_power_kw !== undefined && s.latest_power_kw !== null ? `${Number(s.latest_power_kw).toFixed(2)} kW` : '--'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-0.5">Humidity</span>
                    <span className="text-slate-700 font-semibold">
                      {s.latest_humidity !== undefined && s.latest_humidity !== null ? `${Number(s.latest_humidity).toFixed(0)} %` : '--'}
                    </span>
                  </div>
                  <div>
                    <span className="text-slate-400 block mb-0.5">Samples</span>
                    <span className="text-slate-700 font-semibold">
                      {s.reading_count || 0}
                    </span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-slate-500 font-medium">Product: {s.product_type}</span>
                <span className="font-semibold text-pink-600">Safe: 0–5 °C</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
