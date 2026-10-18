import React, { useEffect, useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import { FileText, Download, RefreshCw, Eye, CheckCircle, FileCode } from 'lucide-react';
import { apiClient } from '../services/api';

export const ReportsPage: React.FC = () => {
  const { selectedSensorId } = useOutletContext<{ selectedSensorId: string }>();
  const [files, setFiles] = useState<string[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [notification, setNotification] = useState<string | null>(null);

  const fetchReports = async () => {
    setLoading(true);
    try {
      const list = await apiClient.getReportsList();
      setFiles(list);
      if (list.length > 0 && !selectedFile) {
        handleViewFile(list[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleViewFile = async (name: string) => {
    setSelectedFile(name);
    try {
      const content = await apiClient.getFileContent(name);
      setFileContent(content);
    } catch (e) {
      setFileContent(`Failed to load content for ${name}: ${e}`);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const res = await apiClient.generateReport(selectedSensorId);
      setNotification(`Generated report suite for sensor ${selectedSensorId}: ${res.files.join(', ')}`);
      setTimeout(() => setNotification(null), 4000);
      await fetchReports();
    } catch (e) {
      console.error(e);
    } finally {
      setGenerating(false);
    }
  };

  const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

  return (
    <div className="space-y-6 pb-12">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-xs">
        <div>
          <div className="flex items-center space-x-2">
            <FileText className="w-5 h-5 text-blue-600" />
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">Audit Reports & Scientific Exports</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Downloadable audit reports, scenario evaluations, JSON artifacts, and markdown research summaries.
          </p>
        </div>

        <button
          onClick={handleGenerate}
          disabled={generating}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-600 to-pink-600 hover:from-blue-700 hover:to-pink-700 text-white font-bold rounded-xl text-xs shadow-md transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${generating ? 'animate-spin' : ''}`} />
          <span>Generate New Audit Report</span>
        </button>
      </div>

      {notification && (
        <div className="p-3 bg-pink-50 border border-pink-200 text-pink-800 rounded-xl text-xs font-semibold flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-pink-600 shrink-0" />
          <span>{notification}</span>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reports File List */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="p-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
            <span>Available Audit Artifacts ({files.length})</span>
            <span className="text-slate-400">/reports/</span>
          </div>

          <div className="divide-y divide-slate-100 max-h-[500px] overflow-y-auto">
            {files.map((f) => {
              const isSelected = f === selectedFile;
              return (
                <div
                  key={f}
                  className={`p-3.5 flex items-center justify-between transition-colors cursor-pointer ${
                    isSelected ? 'bg-blue-50/80 text-blue-900 font-bold' : 'hover:bg-slate-50 text-slate-700'
                  }`}
                  onClick={() => handleViewFile(f)}
                >
                  <div className="flex items-center space-x-2 truncate pr-2">
                    <FileCode className="w-4 h-4 text-slate-400 shrink-0" />
                    <span className="text-xs truncate">{f}</span>
                  </div>

                  <div className="flex items-center space-x-1 shrink-0">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleViewFile(f);
                      }}
                      className="p-1 rounded text-slate-400 hover:text-blue-600 transition"
                      title="Inspect"
                    >
                      <Eye className="w-3.5 h-3.5" />
                    </button>
                    <a
                      href={`${API_BASE}/reports/${f}/`}
                      download
                      onClick={(e) => e.stopPropagation()}
                      className="p-1 rounded text-slate-400 hover:text-pink-600 transition"
                      title="Download"
                    >
                      <Download className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* File Content Preview */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col overflow-hidden">
          <div className="p-4 bg-slate-50/80 border-b border-slate-200 flex items-center justify-between text-xs font-semibold text-slate-700">
            <span className="flex items-center space-x-2">
              <Eye className="w-4 h-4 text-blue-600" />
              <span>Preview: <code className="text-pink-600 font-mono">{selectedFile || 'Select a file'}</code></span>
            </span>
            {selectedFile && (
              <a
                href={`${API_BASE}/reports/${selectedFile}/`}
                download
                className="text-blue-600 hover:text-blue-800 flex items-center space-x-1"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download Raw</span>
              </a>
            )}
          </div>

          <div className="p-4 flex-1 bg-slate-950 text-slate-200 font-mono text-xs overflow-auto max-h-[500px]">
            <pre className="whitespace-pre-wrap">{fileContent || 'No file selected or loading...'}</pre>
          </div>
        </div>
      </div>
    </div>
  );
};
