import { apiClient } from './client';
import { PantrySummary } from '../types';

export const summaryApi = {
  /**
   * Fetch current inventory metrics and top-voted Snack of the Week.
   */
  async getSummary(): Promise<PantrySummary> {
    const response = await apiClient.get<PantrySummary>('/snacks/summary');
    return response.data;
  },
};
