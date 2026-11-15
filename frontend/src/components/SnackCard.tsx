import React, { useState } from 'react';
import { Heart, Utensils, Loader2, AlertCircle, Image as ImageIcon } from 'lucide-react';
import { Snack } from '../types';
import { StatusBadge } from './StatusBadge';
import { CategoryBadge } from './CategoryBadge';

interface SnackCardProps {
  snack: Snack;
  isConsuming?: boolean;
  isVoting?: boolean;
  onConsume: (snackId: number) => void;
  onVoteToggle: (snackId: number, currentlyVoted: boolean) => void;
}

export const SnackCard: React.FC<SnackCardProps> = ({
  snack,
  isConsuming = false,
  isVoting = false,
  onConsume,
  onVoteToggle,
}) => {
  const [imageError, setImageError] = useState(false);
  const isOutOfStock = snack.quantity === 0;
  const isRunningLow = snack.quantity > 0 && snack.quantity <= snack.low_stock_threshold;
  const hasVoted = !!snack.user_has_voted;

  return (
    <div
      className={`bg-white rounded-2xl border transition-all duration-200 shadow-sm hover:shadow-md flex flex-col justify-between overflow-hidden ${
        isOutOfStock
          ? 'border-slate-200 opacity-90'
          : isRunningLow
          ? 'border-amber-200 ring-1 ring-amber-100'
          : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      {/* Snack Image Header or Elegant Fallback Banner */}
      <div className="relative w-full h-40 bg-slate-100 overflow-hidden group">
        {snack.image_url && !imageError ? (
          <img
            src={snack.image_url}
            alt={snack.name}
            onError={() => setImageError(true)}
            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            loading="lazy"
          />
        ) : (
          <div className="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-amber-50 to-slate-100 text-slate-400">
            <div className="w-12 h-12 rounded-xl bg-amber-100/70 text-amber-600 flex items-center justify-center shadow-inner mb-1">
              <ImageIcon className="w-6 h-6" />
            </div>
            <span className="text-[11px] font-medium text-slate-400">Pantry Snack</span>
          </div>
        )}

        {/* Floating Category & Status Overlay Badges */}
        <div className="absolute top-3 left-3 right-3 flex items-center justify-between gap-2 pointer-events-none">
          <div className="drop-shadow-sm">
            <CategoryBadge category={snack.category} />
          </div>
          <div className="drop-shadow-sm">
            <StatusBadge status={snack.status} />
          </div>
        </div>
      </div>

      {/* Top Details */}
      <div className="p-5 space-y-3">
        {/* Snack Name */}
        <div>
          <h3 className="text-lg font-bold text-slate-900 tracking-tight leading-snug line-clamp-1">
            {snack.name}
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Low-stock alert threshold: <span className="font-semibold">{snack.low_stock_threshold}</span>
          </p>
        </div>

        {/* Stock Level Indicator */}
        <div className="pt-2">
          <div className="flex items-baseline justify-between mb-1.5">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Available Inventory
            </span>
            <span
              className={`text-sm font-black ${
                isOutOfStock
                  ? 'text-rose-600'
                  : isRunningLow
                  ? 'text-amber-600'
                  : 'text-emerald-700'
              }`}
            >
              {isOutOfStock ? '0 packets' : `${snack.quantity} ${snack.quantity === 1 ? 'packet' : 'packets'}`}
            </span>
          </div>

          {/* Visual Stock Meter */}
          <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
            <div
              style={{
                width: `${Math.min(
                  100,
                  Math.round((snack.quantity / Math.max(snack.low_stock_threshold * 2, 10)) * 100)
                )}%`,
              }}
              className={`h-full rounded-full transition-all duration-300 ${
                isOutOfStock
                  ? 'bg-rose-500 w-0'
                  : isRunningLow
                  ? 'bg-amber-500'
                  : 'bg-emerald-500'
              }`}
            />
          </div>

          {isRunningLow && !isOutOfStock && (
            <div className="mt-2 flex items-center space-x-1.5 text-[11px] font-medium text-amber-700 bg-amber-50 px-2.5 py-1 rounded-lg border border-amber-200/60">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-amber-600" />
              <span>Running low — grab one before it is gone!</span>
            </div>
          )}

          {isOutOfStock && (
            <div className="mt-2 flex items-center space-x-1.5 text-[11px] font-medium text-rose-700 bg-rose-50 px-2.5 py-1 rounded-lg border border-rose-200/60">
              <AlertCircle className="w-3.5 h-3.5 flex-shrink-0 text-rose-600" />
              <span>Out of stock — awaiting restock by pantry admin.</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Footer */}
      <div className="p-4 bg-slate-50/80 border-t border-slate-100 flex items-center justify-between gap-3">
        {/* Vote Button */}
        <button
          type="button"
          onClick={() => onVoteToggle(snack.id, hasVoted)}
          disabled={isVoting}
          title={hasVoted ? 'Click to remove your vote' : 'Vote for this snack'}
          className={`inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold transition-all ${
            hasVoted
              ? 'bg-rose-100 text-rose-700 border border-rose-300 shadow-sm hover:bg-rose-200'
              : 'bg-white text-slate-700 border border-slate-200 hover:border-slate-300 hover:bg-slate-100'
          } disabled:opacity-50`}
        >
          {isVoting ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-500" />
          ) : (
            <Heart
              className={`w-3.5 h-3.5 transition-colors ${
                hasVoted ? 'fill-rose-500 text-rose-500' : 'text-slate-400'
              }`}
            />
          )}
          <span>{snack.votes_count}</span>
          <span className="hidden sm:inline">{hasVoted ? 'Voted' : 'Vote'}</span>
        </button>

        {/* Consume Button */}
        <button
          type="button"
          onClick={() => onConsume(snack.id)}
          disabled={isOutOfStock || isConsuming}
          className={`flex-1 inline-flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-sm ${
            isOutOfStock
              ? 'bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-200'
              : 'bg-amber-600 hover:bg-amber-700 text-white active:scale-[0.98]'
          } disabled:opacity-50`}
        >
          {isConsuming ? (
            <>
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              <span>Consuming...</span>
            </>
          ) : (
            <>
              <Utensils className="w-3.5 h-3.5" />
              <span>{isOutOfStock ? 'Depleted' : 'Grab 1 Packet'}</span>
            </>
          )}
        </button>
      </div>
    </div>
  );
};
