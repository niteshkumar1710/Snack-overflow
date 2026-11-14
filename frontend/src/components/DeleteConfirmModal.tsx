import React, { useState } from 'react';
import { Loader2, AlertTriangle } from 'lucide-react';
import { Snack } from '../types';

interface DeleteConfirmModalProps {
  isOpen: boolean;
  snack: Snack | null;
  onClose: () => void;
  onConfirm: (snackId: number) => Promise<void>;
}

export const DeleteConfirmModal: React.FC<DeleteConfirmModalProps> = ({
  isOpen,
  snack,
  onClose,
  onConfirm,
}) => {
  const [loading, setLoading] = useState(false);

  if (!isOpen || !snack) return null;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm(snack.id);
      onClose();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl max-w-md w-full shadow-2xl border border-slate-100 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        <div className="p-6 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-rose-50 text-rose-600 mx-auto flex items-center justify-center">
            <AlertTriangle className="w-8 h-8" />
          </div>

          <div>
            <h2 className="text-lg font-bold text-slate-900">Delete '{snack.name}'?</h2>
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              Are you sure you want to permanently remove this snack from the pantry?
              Associated votes and activity logs will be cascade-deleted in compliance with database relational integrity rules.
            </p>
          </div>

          <div className="p-3 bg-amber-50 rounded-xl border border-amber-200 text-left text-xs text-amber-900">
            <span className="font-bold">Notice:</span> This action is permanent and cannot be undone.
          </div>

          <div className="pt-2 flex items-center justify-end space-x-3">
            <button
              type="button"
              disabled={loading}
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>

            <button
              type="button"
              disabled={loading}
              onClick={handleConfirm}
              className="inline-flex items-center space-x-1.5 px-5 py-2 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-sm disabled:opacity-50 transition-colors"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              <span>Delete Snack</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
