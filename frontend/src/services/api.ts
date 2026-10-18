import axios from 'axios';
import type { Sensor, Reading, DecisionData, ModelMetrics, AlertItem, DatasetItem } from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const apiClient = {
  // Sensor listing
  getSensors: async (): Promise<Sensor[]> => {
    const res = await api.get('/api/sensors/');
    return res.data.results || [];
  },

  // Sensor telemetry history
  getSensorHistory: async (sensorId: string, limit = 50): Promise<Reading[]> => {
    const res = await api.get(`/api/sensors/${sensorId}/history/?limit=${limit}`);
    return res.data.data || [];
  },

  // Full pipeline decision for a sensor
  getPipeline: async (sensorId?: string): Promise<{ success: boolean; data: DecisionData }> => {
    const url = sensorId ? `/api/pipeline/?sensor=${sensorId}` : '/api/pipeline/';
    const res = await api.get(url);
    return res.data;
  },

  // Dashboard overview
  getDashboard: async (sensorId?: string): Promise<DecisionData> => {
    const url = sensorId ? `/api/dashboard/?sensor=${sensorId}` : '/api/dashboard/';
    const res = await api.get(url);
    return res.data;
  },

  // Model architecture & performance metrics
  getModelInfo: async (): Promise<{ model: string; input: string; output_steps: number; device: string; metrics: ModelMetrics }> => {
    const res = await api.get('/api/model/');
    return res.data.data;
  },

  // Derived endpoints
  getPredictions: async (sensorId?: string): Promise<number[]> => {
    const url = sensorId ? `/api/predictions/?sensor=${sensorId}` : '/api/predictions/';
    const res = await api.get(url);
    return res.data.data;
  },

  getRisk: async (sensorId?: string) => {
    const url = sensorId ? `/api/risk/?sensor=${sensorId}` : '/api/risk/';
    const res = await api.get(url);
    return res.data.data;
  },

  getOptimization: async (sensorId?: string) => {
    const url = sensorId ? `/api/optimization/?sensor=${sensorId}` : '/api/optimization/';
    const res = await api.get(url);
    return res.data.data;
  },

  getAlerts: async (sensorId?: string): Promise<AlertItem[]> => {
    const url = sensorId ? `/api/alerts/?sensor=${sensorId}` : '/api/alerts/';
    const res = await api.get(url);
    return res.data.data || [];
  },

  resolveAlert: async (alertId: string) => {
    const res = await api.post(`/api/alerts/${alertId}/resolve/`);
    return res.data;
  },

  // Simulation controls
  controlSimulation: async (action: 'start' | 'pause' | 'reset') => {
    const res = await api.post(`/api/simulation/${action}/`);
    return res.data;
  },

  // Reports
  getReportsList: async (): Promise<string[]> => {
    const res = await api.get('/api/reports/');
    return res.data.files || [];
  },

  getReportData: async (sensorId?: string) => {
    const url = sensorId ? `/api/report/?sensor=${sensorId}` : '/api/report/';
    const res = await api.get(url);
    return res.data.data;
  },

  generateReport: async (sensorId?: string) => {
    const url = sensorId ? `/api/reports/generate/?sensor=${sensorId}` : '/api/reports/generate/';
    const res = await api.post(url);
    return res.data;
  },

  getFileContent: async (filename: string): Promise<string> => {
    const res = await api.get(`/api/file_content/?name=${encodeURIComponent(filename)}`);
    return res.data.content;
  },

  saveCaseAudit: async (sensorId?: string) => {
    const url = sensorId ? `/api/save_case/?sensor=${sensorId}` : '/api/save_case/';
    const res = await api.post(url);
    return res.data;
  },

  // Upload CSV
  uploadCsv: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const res = await api.post('/api/upload/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return res.data;
  },

  // Ingest IoT telemetry
  ingestTelemetry: async (records: any | any[], apiKey?: string, hwToken?: string) => {
    const headers: Record<string, string> = {};
    if (apiKey) headers['X-IoT-API-Key'] = apiKey;
    if (hwToken) headers['X-Hardware-Key'] = hwToken;
    const res = await api.post('/api/iot/telemetry/', records, { headers });
    return res.data;
  },
};
