import React from 'react';
import { LucideIcon } from 'lucide-react';

interface SummaryCardProps {
  title: string;
  value: number;
  subtitle: string;
  icon: LucideIcon;
  colorScheme: 'blue' | 'emerald' | 'amber' | 'rose';
  loading?: boolean;
}

export const SummaryCard: React.FC<SummaryCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  colorScheme,
  loading = false,
}) => {
  const schemeClasses = {
    blue: {
      bg: 'bg-blue-50 text-blue-600',
      border: 'border-blue-100',
      textAccent: 'text-blue-600',
    },
    emerald: {
      bg: 'bg-emerald-50 text-emerald-600',
      border: 'border-emerald-100',
      textAccent: 'text-emerald-600',
    },
    amber: {
      bg: 'bg-amber-50 text-amber-600',
      border: 'border-amber-100',
      textAccent: 'text-amber-600',
    },
    rose: {
      bg: 'bg-rose-50 text-rose-600',
      border: 'border-rose-100',
      textAccent: 'text-rose-600',
    },
  }[colorScheme];

  return (
    <div
      className={`bg-white rounded-xl border ${schemeClasses.border} p-6 shadow-sm hover:shadow transition-shadow flex items-start justify-between`}
    >
      <div className="space-y-1">
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</p>
        {loading ? (
          <div className="h-9 w-16 bg-slate-200 animate-pulse rounded my-1" />
        ) : (
          <p className="text-3xl font-extrabold text-slate-900 tracking-tight">{value}</p>
        )}
        <p className="text-xs text-slate-500">{subtitle}</p>
      </div>

      <div className={`p-3 rounded-xl ${schemeClasses.bg}`}>
        <Icon className="w-6 h-6" />
      </div>
    </div>
  );
};
