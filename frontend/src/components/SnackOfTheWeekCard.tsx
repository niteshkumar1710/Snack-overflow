import React from 'react';
import { Award, Heart, Package, Sparkles } from 'lucide-react';
import { Snack } from '../types';
import { StatusBadge } from './StatusBadge';
import { CategoryBadge } from './CategoryBadge';

interface SnackOfTheWeekCardProps {
  snack: Snack | null;
  loading?: boolean;
}

export const SnackOfTheWeekCard: React.FC<SnackOfTheWeekCardProps> = ({ snack, loading = false }) => {
  if (loading) {
    return (
      <div className="bg-gradient-to-r from-amber-500/10 via-amber-400/5 to-amber-500/10 border border-amber-200/60 rounded-2xl p-6 sm:p-8 animate-pulse">
        <div className="h-6 w-40 bg-amber-200 rounded mb-4" />
        <div className="h-8 w-64 bg-amber-200/70 rounded mb-3" />
        <div className="h-4 w-48 bg-amber-200/50 rounded" />
      </div>
    );
  }

  if (!snack) {
    return (
      <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-amber-50 text-amber-500 mx-auto flex items-center justify-center">
          <Award className="w-6 h-6" />
        </div>
        <h3 className="text-base font-semibold text-slate-800">No Snack of the Week Yet</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto">
          Vote for your favorite pantry snacks to crown the office champion!
        </p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden bg-gradient-to-br from-amber-50 via-white to-amber-100/40 border border-amber-200 rounded-2xl p-6 sm:p-8 shadow-sm">
      {/* Decorative background watermark */}
      <div className="absolute right-0 bottom-0 translate-x-8 translate-y-8 opacity-5 pointer-events-none">
        <Award className="w-64 h-64 text-amber-600" />
      </div>

      <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="space-y-3">
          {/* Badge & Title */}
          <div className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-500/15 border border-amber-500/30 text-amber-900 text-xs font-bold tracking-wide uppercase">
            <Sparkles className="w-3.5 h-3.5 text-amber-600" />
            <span>Snack of the Week</span>
          </div>

          <div>
            <h2 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
              {snack.name}
            </h2>
            <p className="text-xs text-slate-500 mt-1">
              Office top pick determined deterministically by highest vote count and inventory availability.
            </p>
          </div>

          {/* Badges & Meta */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            <CategoryBadge category={snack.category} />
            <StatusBadge status={snack.status} />

            <div className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
              <Heart className="w-3.5 h-3.5 fill-rose-500 text-rose-500" />
              <span>{snack.votes_count} {snack.votes_count === 1 ? 'vote' : 'votes'}</span>
            </div>
          </div>
        </div>

        {/* Stock Highlight Pill */}
        <div className="bg-white/90 backdrop-blur border border-amber-200/80 rounded-xl p-4 sm:p-5 flex items-center space-x-4 shadow-sm md:self-center">
          <div className="w-12 h-12 rounded-xl bg-amber-500 text-white flex items-center justify-center shadow-md shadow-amber-500/20">
            <Package className="w-6 h-6" />
          </div>
          <div>
            <div className="text-2xl font-black text-slate-900 leading-tight">
              {snack.quantity}
            </div>
            <div className="text-xs text-slate-500 font-medium">
              Packets remaining (Threshold: {snack.low_stock_threshold})
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
