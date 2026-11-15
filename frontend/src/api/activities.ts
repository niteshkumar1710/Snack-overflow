import { apiClient } from './client';
import { PaginatedActivities } from '../types';

export interface ActivityQueryParams {
  page?: number;
  limit?: number;
}

/**
 * Fetch paginated activity history from the backend.
 * Protected by admin authentication.
 */
export const getActivities = async (
  params: ActivityQueryParams = {}
): Promise<PaginatedActivities> => {
  const query = new URLSearchParams();
  if (params.page !== undefined) {
    query.append('page', params.page.toString());
  }
  if (params.limit !== undefined) {
    query.append('limit', params.limit.toString());
  }

  const endpoint = `/activities${query.toString() ? `?${query.toString()}` : ''}`;
  const response = await apiClient.get<PaginatedActivities>(endpoint);
  return response.data;
};
