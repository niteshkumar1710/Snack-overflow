import React, { useEffect, useRef } from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle, Info, X } from 'lucide-react';

export type NotificationType = 'success' | 'error' | 'warning' | 'info';

export interface NotificationModalProps {
  isOpen: boolean;
  type?: NotificationType;
  title?: string;
  message: string;
  onClose: () => void;
}

export const NotificationModal: React.FC<NotificationModalProps> = ({
  isOpen,
  type = 'info',
  title,
  message,
  onClose,
}) => {
  const dialogRef = useRef<HTMLDivElement | null>(null);

  // Keyboard accessibility: Escape to close
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  // Focus trap / auto-focus modal for screen reader accessibility
  useEffect(() => {
    if (isOpen && dialogRef.current) {
      dialogRef.current.focus();
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const isSuccess = type === 'success';
  const isError = type === 'error';
  const isWarning = type === 'warning';

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="notification-modal-title"
      aria-describedby="notification-modal-message"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-slate-900/60 backdrop-blur-xs animate-in fade-in duration-200"
      onClick={(e) => {
        // Close when clicking directly on the backdrop overlay
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div
        ref={dialogRef}
        tabIndex={-1}
        className="relative w-full max-w-sm sm:max-w-md bg-white rounded-3xl shadow-2xl border border-slate-100 p-6 sm:p-7 text-center focus:outline-none animate-in zoom-in-95 duration-200"
      >
        {/* Top-right close button */}
        <button
          type="button"
          onClick={onClose}
          aria-label="Close message"
          className="absolute top-4 right-4 p-1.5 rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Icon with theme accent */}
        <div className="flex justify-center mb-4">
          {isSuccess && (
            <div className="w-14 h-14 rounded-2xl bg-emerald-100/80 text-emerald-600 flex items-center justify-center shadow-inner">
              <CheckCircle2 className="w-8 h-8" />
            </div>
          )}
          {isError && (
            <div className="w-14 h-14 rounded-2xl bg-rose-100/80 text-rose-600 flex items-center justify-center shadow-inner">
              <AlertCircle className="w-8 h-8" />
            </div>
          )}
          {isWarning && (
            <div className="w-14 h-14 rounded-2xl bg-amber-100/80 text-amber-600 flex items-center justify-center shadow-inner">
              <AlertTriangle className="w-8 h-8" />
            </div>
          )}
          {!isSuccess && !isError && !isWarning && (
            <div className="w-14 h-14 rounded-2xl bg-blue-100/80 text-blue-600 flex items-center justify-center shadow-inner">
              <Info className="w-8 h-8" />
            </div>
          )}
        </div>

        {/* Title */}
        <h3
          id="notification-modal-title"
          className={`text-base sm:text-lg font-bold tracking-tight mb-2 ${
            isSuccess
              ? 'text-emerald-900'
              : isError
              ? 'text-rose-900'
              : isWarning
              ? 'text-amber-900'
              : 'text-slate-900'
          }`}
        >
          {title || (isSuccess ? 'Success' : isError ? 'Error' : isWarning ? 'Notice' : 'Information')}
        </h3>

        {/* Message */}
        <p
          id="notification-modal-message"
          className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed mb-6"
        >
          {message}
        </p>

        {/* Dismiss Button */}
        <div className="flex justify-center">
          <button
            type="button"
            onClick={onClose}
            className={`w-full sm:w-auto min-w-[120px] px-6 py-2.5 rounded-xl font-bold text-xs sm:text-sm shadow-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 ${
              isSuccess
                ? 'bg-emerald-600 hover:bg-emerald-700 text-white focus:ring-emerald-500'
                : isError
                ? 'bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500'
                : isWarning
                ? 'bg-amber-600 hover:bg-amber-700 text-white focus:ring-amber-500'
                : 'bg-slate-900 hover:bg-slate-800 text-white focus:ring-slate-500'
            }`}
          >
            Got it
          </button>
        </div>
      </div>
    </div>
  );
};
