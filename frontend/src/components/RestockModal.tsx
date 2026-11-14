import React, { useState } from 'react';
import { X, Loader2, AlertCircle, PackagePlus, ArrowRight } from 'lucide-react';
import { Snack, RestockResponse } from '../types';
import { snackApi } from '../api/snacks';
import { getErrorMessage } from '../api/client';

interface RestockModalProps {
  isOpen: boolean;
  snack: Snack | null;
  onClose: () => void;
  onSuccess: (response: RestockResponse) => void;
}

export const RestockModal: React.FC<RestockModalProps> = ({
  isOpen,
  snack,
  onClose,
  onSuccess,
}) => {
  const [amount, setAmount] = useState<number>(10);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen || !snack) return null;

  const currentStock = snack.quantity;
  const projectedStock = currentStock + (amount > 0 ? amount : 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (amount <= 0) {
      setError('Restock amount must be a positive integer greater than zero.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await snackApi.restockSnack(snack.id, amount);
      onSuccess(response);
      onClose();
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const handleQuickAdd = (addQty: number) => {
    setAmount((prev) => Math.max(1, (prev || 0) + addQty));
    setError(null);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-emerald-500/15 text-emerald-700 flex items-center justify-center">
              <PackagePlus className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Restock Pantry Snack</h2>
              <p className="text-xs text-slate-500">{snack.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="mx-6 mt-4 p-3.5 rounded-xl bg-rose-50 border border-rose-200 flex items-start space-x-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 text-rose-500 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Inventory Preview Pill */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-center justify-around text-center">
            <div>
              <p className="text-[11px] font-semibold uppercase text-slate-400">Current Stock</p>
              <p className="text-xl font-black text-slate-700">{currentStock}</p>
            </div>
            <ArrowRight className="w-5 h-5 text-slate-300" />
            <div>
              <p className="text-[11px] font-semibold uppercase text-emerald-600">Projected Stock</p>
              <p className="text-xl font-black text-emerald-700">{projectedStock}</p>
            </div>
          </div>

          {/* Amount input */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
              Packets to Add
            </label>
            <input
              type="number"
              min="1"
              required
              value={amount}
              onChange={(e) => setAmount(Math.max(1, parseInt(e.target.value) || 0))}
              className="w-full px-3.5 py-2.5 rounded-xl text-base font-bold border border-slate-300 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-slate-900 transition-colors text-center"
            />
          </div>

          {/* Quick Buttons */}
          <div>
            <p className="text-[11px] font-semibold uppercase text-slate-400 mb-2">Quick Add</p>
            <div className="grid grid-cols-4 gap-2">
              {[5, 10, 20, 50].map((qty) => (
                <button
                  key={qty}
                  type="button"
                  onClick={() => handleQuickAdd(qty)}
                  className="py-1.5 text-xs font-bold rounded-lg border bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100 transition-colors"
                >
                  +{qty}
                </button>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="pt-4 flex items-center justify-end space-x-3 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>

            <button
              type="submit"
              disabled={loading || amount <= 0}
              className="inline-flex items-center space-x-1.5 px-5 py-2 rounded-xl text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 shadow-sm disabled:opacity-50 transition-colors"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Confirm Restock (+{amount})</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
