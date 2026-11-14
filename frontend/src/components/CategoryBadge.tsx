import React from 'react';
import { SnackCategory } from '../types';
import { getCategoryConfig } from '../utils/snackUtils';

interface CategoryBadgeProps {
  category: SnackCategory;
  className?: string;
}

export const CategoryBadge: React.FC<CategoryBadgeProps> = ({ category, className = '' }) => {
  const config = getCategoryConfig(category);

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border ${config.badgeClasses} ${className}`}
    >
      {config.label}
    </span>
  );
};
