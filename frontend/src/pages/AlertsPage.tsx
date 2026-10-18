import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { AlertTriangle, CheckCircle, ShieldAlert, Clock, BellRing, Sparkles } from 'lucide-react';
import { MetricCard } from '../components/ui/MetricCard';
import { StatusBadge } from '../components/ui/StatusBadge';
import { apiClient } from '../services/api';
import type { DecisionData, AlertItem } from '../types';

export const AlertsPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [data, setData] = useState<DecisionData | null>(null);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [resolvedIds, setResolvedIds] = useState<string[]>([]);

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const [dashRes, alertRes] = await Promise.all([
        apiClient.getDashboard(selectedSensorId),
        apiClient.getAlerts(selectedSensorId),
      ]);
      setData(dashRes);
      setAlerts(alertRes);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [selectedSensorId]);

  const handleResolve = async (id: string) => {
    try {
      await apiClient.resolveAlert(id);
      setResolvedIds((prev) => [...prev, id]);
    } catch (e) {
      console.error(e);
    }
  };

  const risk = data?.risk;

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <BellRing className="w-5 h-5 text-pink-600 animate-bounce" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Predictive Risk & Anomaly Center</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Real-time thermal risk scoring, proactive breach warnings, and automated actuator escalation alarms.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <StatusBadge status={risk?.risk_level || 'LOW'} size="md" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <MetricCard
          title="Overall Risk Score"
          value={risk ? risk.risk_score.toFixed(1) : '--'}
          unit="/ 100"
          subtitle={risk?.risk_level || 'Normal'}
          icon={ShieldAlert}
          variant={risk && risk.risk_score > 60 ? 'pink' : 'emerald'}
          badge="Composite Index"
        />
        <MetricCard
          title="Excursion Probability"
          value={risk ? `${(risk.excursion_probability * 100).toFixed(0)}%` : '--'}
          subtitle="Within 15-Minute Horizon"
          icon={AlertTriangle}
          variant={risk && risk.excursion_probability > 0.5 ? 'pink' : 'blue'}
          badge="Predictive"
        />
        <MetricCard
          title="Time to Breach"
          value={risk?.predicted_breach_time || 'None'}
          subtitle={risk?.temperature_trend ? `Trend: ${risk.temperature_trend}` : 'Trajectory Stable'}
          icon={Clock}
          variant={risk?.predicted_breach_time ? 'pink' : 'slate'}
          badge="Early Warning"
        />
      </div>

      {/* Active Alerts List */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-4 h-4 text-pink-500" />
            <h2 className="text-base font-bold text-slate-900">Active Anomaly & Breach Notifications</h2>
          </div>
          <span className="text-xs font-semibold text-slate-400">
            Node: {selectedSensorId}
          </span>
        </div>

        <div className="p-5 space-y-3">
          {alerts.map((alert) => {
            const isResolved = alert.resolved || resolvedIds.includes(alert.id);
            return (
              <div
                key={alert.id}
                className={`p-4 rounded-xl border transition-all flex items-start justify-between ${
                  isResolved
                    ? 'bg-slate-50 border-slate-200 opacity-60'
                    : 'bg-pink-50/60 border-pink-200 shadow-xs'
                }`}
              >
                <div className="flex items-start space-x-3">
                  <div className={`p-2 rounded-lg ${isResolved ? 'bg-slate-200 text-slate-500' : 'bg-pink-100 text-pink-600'}`}>
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-sm text-slate-900">{alert.message}</span>
                      <StatusBadge status={alert.severity} size="sm" />
                    </div>
                    <p className="text-xs text-slate-500 mt-1">
                      Sensor: {alert.sensor} | Target bounds violated in future predicted trajectory.
                    </p>
                  </div>
                </div>

                <div>
                  {!isResolved ? (
                    <button
                      onClick={() => handleResolve(alert.id)}
                      className="px-3 py-1.5 bg-white hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-lg border border-slate-300 shadow-xs transition"
                    >
                      Acknowledge
                    </button>
                  ) : (
                    <span className="flex items-center space-x-1 text-emerald-600 text-xs font-semibold">
                      <CheckCircle className="w-4 h-4" />
                      <span>Acknowledged</span>
                    </span>
                  )}
                </div>
              </div>
            );
          })}

          {alerts.length === 0 && !loading && (
            <div className="py-12 text-center text-slate-400">
              <CheckCircle className="w-10 h-10 mx-auto text-emerald-400 mb-2" />
              <p className="font-medium text-slate-600">No active alerts or predicted excursions for {selectedSensorId}.</p>
              <p className="text-xs text-slate-400 mt-1">Temperature trajectory remains strictly within the 0.0–5.0 °C envelope.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
