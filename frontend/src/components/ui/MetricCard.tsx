import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  subtitle?: string;
  icon?: LucideIcon;
  variant?: 'blue' | 'pink' | 'emerald' | 'amber' | 'slate';
  badge?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  unit,
  subtitle,
  icon: Icon,
  variant = 'blue',
  badge,
}) => {
  const variantStyles = {
    blue: {
      border: 'border-blue-100 hover:border-blue-300',
      iconBg: 'bg-blue-50 text-blue-600',
      badgeBg: 'bg-blue-50 text-blue-700 border-blue-200',
    },
    pink: {
      border: 'border-pink-100 hover:border-pink-300',
      iconBg: 'bg-pink-50 text-pink-600',
      badgeBg: 'bg-pink-50 text-pink-700 border-pink-200',
    },
    emerald: {
      border: 'border-emerald-100 hover:border-emerald-300',
      iconBg: 'bg-emerald-50 text-emerald-600',
      badgeBg: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    },
    amber: {
      border: 'border-amber-100 hover:border-amber-300',
      iconBg: 'bg-amber-50 text-amber-600',
      badgeBg: 'bg-amber-50 text-amber-700 border-amber-200',
    },
    slate: {
      border: 'border-slate-200 hover:border-slate-300',
      iconBg: 'bg-slate-100 text-slate-700',
      badgeBg: 'bg-slate-100 text-slate-700 border-slate-200',
    },
  };

  const style = variantStyles[variant];

  return (
    <div
      className={`bg-white rounded-xl p-5 border ${style.border} shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between`}
    >
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${style.iconBg}`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>

      <div className="flex items-baseline space-x-1.5 my-1">
        <span className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">{value}</span>
        {unit && <span className="text-sm font-semibold text-slate-500">{unit}</span>}
      </div>

      <div className="mt-2 flex items-center justify-between text-xs">
        {subtitle && <span className="text-slate-500 font-medium truncate">{subtitle}</span>}
        {badge && (
          <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${style.badgeBg}`}>
            {badge}
          </span>
        )}
      </div>
    </div>
  );
};
