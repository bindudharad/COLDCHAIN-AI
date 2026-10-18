import React, { useState } from 'react';
import { Upload, FileUp, CheckCircle2, AlertCircle, ShieldCheck } from 'lucide-react';
import { apiClient } from '../services/api';

export const UploadPage: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setError(null);
      setResult(null);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a valid CSV file.');
      return;
    }
    setUploading(true);
    setError(null);
    try {
      const res = await apiClient.uploadCsv(file);
      setResult(res);
    } catch (err: any) {
      setError(err?.response?.data?.errors?.join(', ') || 'Failed to upload CSV file.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <Upload className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Upload Telemetry Data</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Ingest cold-chain sensor streams for evaluation, validation, and offline exploratory analysis.
          </p>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="px-3 py-1.5 rounded-xl bg-blue-50 text-blue-700 font-semibold border border-blue-200">
            Max 5 MB (.csv)
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upload Form */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
          <h2 className="text-base font-bold text-slate-900 mb-4 flex items-center space-x-2">
            <FileUp className="w-4 h-4 text-pink-500" />
            <span>Select CSV Telemetry File</span>
          </h2>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="border-2 border-dashed border-slate-300 hover:border-blue-500 rounded-xl p-6 text-center cursor-pointer transition">
              <input
                type="file"
                accept=".csv"
                id="csv-file-input"
                className="hidden"
                onChange={handleFileChange}
              />
              <label htmlFor="csv-file-input" className="cursor-pointer block">
                <Upload className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                <span className="text-xs font-semibold text-blue-600 hover:underline block">
                  {file ? file.name : 'Choose CSV file to upload'}
                </span>
                <span className="text-[11px] text-slate-400 mt-1 block">
                  Required: timestamp, sensor_id, temperature
                </span>
              </label>
            </div>

            <button
              type="submit"
              disabled={!file || uploading}
              className={`w-full py-2.5 px-4 rounded-xl font-bold text-xs text-white bg-blue-600 hover:bg-blue-700 transition shadow-xs ${
                !file || uploading ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              {uploading ? 'Validating & Ingesting...' : 'Upload & Process CSV'}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-3 bg-pink-50 border border-pink-200 rounded-xl text-xs text-pink-700 flex items-start space-x-2">
              <AlertCircle className="w-4 h-4 text-pink-600 shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="mt-4 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 space-y-1">
              <div className="flex items-center space-x-1.5 font-bold">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Upload Succeeded</span>
              </div>
              <p>Received: <strong>{result.rows_received}</strong> rows</p>
              <p>Valid: <strong>{result.rows_valid}</strong> rows</p>
              <p>Persisted: <strong>{result.rows_persisted}</strong> new records</p>
            </div>
          )}
        </div>

        {/* Format Guidelines */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-6 border border-slate-200 shadow-xs flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-3 flex items-center space-x-2">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>CSV Ingestion Contract & Safeguards</span>
            </h2>

            <div className="space-y-3 text-xs text-slate-600">
              <p>Uploaded CSV files undergo strict data validation checks before persistence:</p>
              <ul className="list-disc pl-5 space-y-1.5">
                <li><strong>Required Schema:</strong> <code>timestamp</code> (ISO-8601), <code>sensor_id</code> (string), <code>temperature</code> (numeric, physical bounds -60 to 70 °C).</li>
                <li><strong>Optional Telemetry:</strong> <code>ambient_temperature</code>, <code>humidity</code>, <code>power_kw</code>, <code>compressor_state</code>, <code>door_open</code>.</li>
                <li><strong>Provenance Stamping:</strong> Ingested user uploads are tagged as <code>Uploaded data</code> without overwriting authoritative research benchmarks.</li>
                <li><strong>Zero Model Corruption:</strong> Model weights and production inferences are isolated from ad-hoc unauthenticated uploads.</li>
              </ul>
            </div>
          </div>

          <div className="mt-6 p-4 rounded-xl bg-slate-50 border border-slate-200 text-xs font-mono text-slate-700">
            <span className="text-slate-400 font-semibold block mb-1">Example Header:</span>
            timestamp,sensor_id,temperature,ambient_temperature,humidity,power_kw,compressor_state,door_open
          </div>
        </div>
      </div>
    </div>
  );
};
