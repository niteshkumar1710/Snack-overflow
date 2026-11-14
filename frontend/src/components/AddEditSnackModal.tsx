import React, { useState, useEffect } from 'react';
import { X, Loader2, AlertCircle, PlusCircle, Edit3 } from 'lucide-react';
import { Snack, SnackCategory, SnackCreateInput, SnackUpdateInput } from '../types';
import { snackApi } from '../api/snacks';
import { getErrorMessage } from '../api/client';

interface AddEditSnackModalProps {
  isOpen: boolean;
  mode: 'add' | 'edit';
  snack?: Snack | null;
  onClose: () => void;
  onSuccess: (snack: Snack, mode: 'add' | 'edit') => void;
}

export const AddEditSnackModal: React.FC<AddEditSnackModalProps> = ({
  isOpen,
  mode,
  snack,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [category, setCategory] = useState<SnackCategory>('sweet');
  const [quantity, setQuantity] = useState<number>(10);
  const [threshold, setThreshold] = useState<number>(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Initialize form values when modal opens or snack changes
  useEffect(() => {
    if (isOpen) {
      if (mode === 'edit' && snack) {
        setName(snack.name);
        setCategory(snack.category);
        setQuantity(snack.quantity);
        setThreshold(snack.low_stock_threshold);
      } else {
        setName('');
        setCategory('sweet');
        setQuantity(10);
        setThreshold(5);
      }
      setError(null);
    }
  }, [isOpen, mode, snack]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Snack name cannot be empty.');
      return;
    }
    if (quantity < 0) {
      setError('Stock quantity must be a non-negative integer (0 or greater).');
      return;
    }
    if (threshold < 0) {
      setError('Low stock threshold must be a non-negative integer (0 or greater).');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      if (mode === 'add') {
        const payload: SnackCreateInput = {
          name: name.trim(),
          category,
          quantity: Number(quantity),
          low_stock_threshold: Number(threshold),
        };
        const created = await snackApi.createSnack(payload);
        onSuccess(created, 'add');
      } else if (mode === 'edit' && snack) {
        const payload: SnackUpdateInput = {
          name: name.trim(),
          category,
          quantity: Number(quantity),
          low_stock_threshold: Number(threshold),
        };
        const updated = await snackApi.updateSnack(snack.id, payload);
        onSuccess(updated, 'edit');
      }
      onClose();
    } catch (err: any) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-xl bg-amber-500/15 text-amber-700 flex items-center justify-center font-bold">
              {mode === 'add' ? <PlusCircle className="w-5 h-5" /> : <Edit3 className="w-5 h-5" />}
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">
                {mode === 'add' ? 'Add New Pantry Snack' : `Edit '${snack?.name}'`}
              </h2>
              <p className="text-xs text-slate-500">
                {mode === 'add' ? 'Register a new item into office pantry inventory' : 'Update details and threshold settings'}
              </p>
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Snack Name <span className="text-rose-500">*</span>
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Roasted Almonds, Oat Milk Latte"
              className="w-full px-3.5 py-2.5 rounded-xl text-sm border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-slate-900 transition-colors"
            />
          </div>

          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Category <span className="text-rose-500">*</span>
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as SnackCategory)}
              className="w-full px-3.5 py-2.5 rounded-xl text-sm border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-slate-900 bg-white transition-colors"
            >
              <option value="sweet">Sweet</option>
              <option value="savoury">Savoury</option>
              <option value="drink">Drink</option>
              <option value="healthy-ish">Healthy-ish</option>
            </select>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Quantity <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                min="0"
                required
                value={quantity}
                onChange={(e) => setQuantity(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-full px-3.5 py-2.5 rounded-xl text-sm border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-slate-900 transition-colors"
              />
              <span className="text-[10px] text-slate-400">Must be non-negative</span>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
                Low Stock Threshold <span className="text-rose-500">*</span>
              </label>
              <input
                type="number"
                min="0"
                required
                value={threshold}
                onChange={(e) => setThreshold(Math.max(0, parseInt(e.target.value) || 0))}
                className="w-full px-3.5 py-2.5 rounded-xl text-sm border border-slate-300 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-slate-900 transition-colors"
              />
              <span className="text-[10px] text-slate-400">Default: 5</span>
            </div>
          </div>

          {/* Footer Actions */}
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
              disabled={loading}
              className="inline-flex items-center space-x-1.5 px-5 py-2 rounded-xl text-xs font-bold text-white bg-amber-600 hover:bg-amber-700 shadow-sm disabled:opacity-50 transition-colors"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>{mode === 'add' ? 'Create Snack' : 'Save Changes'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
