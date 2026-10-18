import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Activity,
  LineChart,
  Sliders,
  AlertTriangle,
  Cpu,
  Radio,
  FileText,
  Upload,
  BookOpen,
  Database,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
}

const navItems = [
  { path: '/', label: 'Overview', icon: LayoutDashboard },
  { path: '/dashboard', label: 'Live Dashboard', icon: Activity },
  { path: '/live-monitoring', label: 'Telemetry Stream', icon: Radio },
  { path: '/predictions', label: 'MAD-TCN Forecast', icon: LineChart },
  { path: '/optimization', label: 'NSGA-II Control', icon: Sliders },
  { path: '/alerts', label: 'Risk & Alerts', icon: AlertTriangle },
  { path: '/sensors', label: 'Sensor Network', icon: ShieldCheck },
  { path: '/model', label: 'Neural Architecture', icon: Cpu },
  { path: '/datasets', label: 'Scientific Data', icon: Database },
  { path: '/reports', label: 'Audit & Reports', icon: FileText },
  { path: '/upload', label: 'Telemetry Ingest', icon: Upload },
  { path: '/methodology', label: 'Research Paper', icon: BookOpen },
];

export const Sidebar: React.FC<SidebarProps> = ({ isOpen }) => {
  return (
    <aside
      className={`fixed top-0 left-0 z-40 h-screen transition-all duration-300 bg-slate-900 text-slate-300 flex flex-col border-r border-slate-800 ${
        isOpen ? 'w-64' : 'w-20'
      }`}
    >
      {/* Brand Header */}
      <div className="h-16 flex items-center px-4 border-b border-slate-800/80 bg-slate-950/40">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-pink-500 flex items-center justify-center font-black text-white text-xl shadow-lg shadow-blue-500/20 shrink-0">
          CC
        </div>
        {isOpen && (
          <div className="ml-3 overflow-hidden">
            <h1 className="font-bold text-white text-base leading-tight tracking-tight">ColdChain AI</h1>
            <p className="text-[11px] font-medium text-pink-400 uppercase tracking-wider">IoT & Energy Platform</p>
          </div>
        )}
      </div>

      {/* Navigation Links */}
      <div className="flex-1 py-4 px-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `flex items-center px-3 py-2.5 rounded-lg text-sm font-medium transition-colors group relative ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-600/30'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`
              }
            >
              <Icon className="w-5 h-5 shrink-0 transition-transform group-hover:scale-110" />
              {isOpen && <span className="ml-3 truncate">{item.label}</span>}
              {!isOpen && (
                <div className="absolute left-full ml-2 px-2 py-1 bg-slate-800 text-white text-xs rounded shadow-lg whitespace-nowrap opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity z-50">
                  {item.label}
                </div>
              )}
            </NavLink>
          );
        })}
      </div>

      {/* Footer Info */}
      {isOpen && (
        <div className="p-4 border-t border-slate-800/80 bg-slate-950/20 text-xs text-slate-400">
          <div className="flex items-center space-x-2 text-pink-400 font-semibold mb-1">
            <span className="w-2 h-2 rounded-full bg-pink-500 animate-pulse"></span>
            <span>Real-Data MAD-TCN</span>
          </div>
          <p className="text-[11px] text-slate-400">NSGA-II Trajectory Safe</p>
          <p className="text-[10px] text-slate-400 mt-1">v2.4 Scientific Release</p>
        </div>
      )}
    </aside>
  );
};
