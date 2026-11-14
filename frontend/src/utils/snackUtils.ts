import { SnackCategory, SnackStatus } from '../types';

/**
 * Calculate derived snack status matching the backend domain rules:
 * - 'stocked': quantity > low_stock_threshold
 * - 'running_low': quantity > 0 and quantity <= low_stock_threshold
 * - 'gone': quantity == 0
 */
export function calculateSnackStatus(quantity: number, threshold: number): SnackStatus {
  if (quantity === 0) {
    return 'gone';
  }
  if (quantity <= threshold) {
    return 'running_low';
  }
  return 'stocked';
}

/**
 * Returns human-readable label and Tailwind styling classes for snack status.
 */
export function getStatusConfig(status: SnackStatus): {
  label: string;
  badgeClasses: string;
  dotColor: string;
} {
  switch (status) {
    case 'stocked':
      return {
        label: 'Stocked',
        badgeClasses: 'bg-emerald-50 text-emerald-700 border-emerald-200',
        dotColor: 'bg-emerald-500',
      };
    case 'running_low':
      return {
        label: 'Running Low',
        badgeClasses: 'bg-amber-50 text-amber-700 border-amber-200',
        dotColor: 'bg-amber-500',
      };
    case 'gone':
      return {
        label: 'Out of Stock',
        badgeClasses: 'bg-rose-50 text-rose-700 border-rose-200',
        dotColor: 'bg-rose-500',
      };
  }
}

/**
 * Returns Tailwind styling classes for snack categories.
 */
export function getCategoryConfig(category: SnackCategory): {
  label: string;
  badgeClasses: string;
} {
  switch (category) {
    case 'sweet':
      return {
        label: 'Sweet',
        badgeClasses: 'bg-fuchsia-50 text-fuchsia-700 border-fuchsia-200',
      };
    case 'savoury':
      return {
        label: 'Savoury',
        badgeClasses: 'bg-orange-50 text-orange-700 border-orange-200',
      };
    case 'drink':
      return {
        label: 'Drink',
        badgeClasses: 'bg-sky-50 text-sky-700 border-sky-200',
      };
    case 'healthy-ish':
      return {
        label: 'Healthy-ish',
        badgeClasses: 'bg-teal-50 text-teal-700 border-teal-200',
      };
  }
}
