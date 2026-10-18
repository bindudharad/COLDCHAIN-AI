import React from 'react';

interface StatusBadgeProps {
  status: string;
  variant?: 'blue' | 'pink' | 'emerald' | 'amber' | 'rose' | 'slate';
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  variant,
  size = 'md',
}) => {
  // Determine variant automatically if not provided
  let computedVariant = variant;
  if (!computedVariant) {
    const s = status.toUpperCase();
    if (s.includes('REAL') || s.includes('LOW') || s.includes('PASS') || s.includes('STABLE')) {
      computedVariant = 'emerald';
    } else if (s.includes('CRITICAL') || s.includes('FAIL') || s.includes('BREACH')) {
      computedVariant = 'rose';
    } else if (s.includes('MEDIUM') || s.includes('WARN') || s.includes('RISING')) {
      computedVariant = 'amber';
    } else if (s.includes('SIM') || s.includes('HIGH')) {
      computedVariant = 'pink';
    } else {
      computedVariant = 'blue';
    }
  }

  const styles = {
    blue: 'bg-blue-50 text-blue-700 border-blue-200/80',
    pink: 'bg-pink-50 text-pink-700 border-pink-200/80',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200/80',
    amber: 'bg-amber-50 text-amber-700 border-amber-200/80',
    rose: 'bg-rose-50 text-rose-700 border-rose-200/80',
    slate: 'bg-slate-100 text-slate-700 border-slate-200/80',
  }[computedVariant];

  const sizeStyles = size === 'sm' ? 'px-2 py-0.5 text-[11px]' : 'px-2.5 py-1 text-xs';

  return (
    <span className={`inline-flex items-center font-semibold rounded-full border shadow-2xs ${styles} ${sizeStyles}`}>
      {status}
    </span>
  );
};
