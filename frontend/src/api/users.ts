import { apiClient } from './client';
import {
  PersonalConsumptionHistoryResponse,
  ConsumptionHistoryQueryParams,
} from '../types';

/**
 * Fetch the authenticated user's personal snack consumption history.
 * Strictly scoped to the currently logged in user by backend JWT authentication.
 */
export const getPersonalConsumptionHistory = async (
  params: ConsumptionHistoryQueryParams = {}
): Promise<PersonalConsumptionHistoryResponse> => {
  const query = new URLSearchParams();
  if (params.page !== undefined) {
    query.append('page', params.page.toString());
  }
  if (params.limit !== undefined) {
    query.append('limit', params.limit.toString());
  }
  if (params.start_date) {
    query.append('start_date', params.start_date);
  }
  if (params.end_date) {
    query.append('end_date', params.end_date);
  }

  const endpoint = `/users/me/consumption-history${
    query.toString() ? `?${query.toString()}` : ''
  }`;
  const response = await apiClient.get<PersonalConsumptionHistoryResponse>(endpoint);
  return response.data;
};
