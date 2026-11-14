import { apiClient } from './client';
import {
  PaginatedSnacks,
  Snack,
  ConsumptionResponse,
  RestockResponse,
  VoteResponse,
  SnackQueryParams,
  SnackCreateInput,
  SnackUpdateInput,
} from '../types';

export const snackApi = {
  /**
   * Fetch paginated list of snacks with server-side search, category filter, and status filter.
   */
  async getSnacks(params?: SnackQueryParams): Promise<PaginatedSnacks> {
    const cleanParams: Record<string, string | number> = {};

    if (params?.search && params.search.trim()) {
      cleanParams.search = params.search.trim();
    }
    if (params?.category && params.category.trim()) {
      cleanParams.category = params.category.trim();
    }
    if (params?.status && params.status.trim()) {
      cleanParams.status = params.status.trim();
    }
    if (params?.page) {
      cleanParams.page = params.page;
    }
    if (params?.page_size) {
      cleanParams.page_size = params.page_size;
    }

    const response = await apiClient.get<PaginatedSnacks>('/snacks', {
      params: cleanParams,
    });
    return response.data;
  },

  /**
   * Fetch a single snack by its ID.
   */
  async getSnackById(snackId: number): Promise<Snack> {
    const response = await apiClient.get<Snack>(`/snacks/${snackId}`);
    return response.data;
  },

  /**
   * Atomically consume a snack packet.
   * Decrements stock and logs a consumed activity record in one database transaction.
   * Rejection with HTTP 409 Conflict triggers "Someone beat you to the last packet!".
   */
  async consumeSnack(snackId: number, amount: number = 1): Promise<ConsumptionResponse> {
    const response = await apiClient.post<ConsumptionResponse>(`/snacks/${snackId}/consume`, {
      amount,
    });
    return response.data;
  },

  /**
   * Cast a vote for a pantry snack.
   * Enforces database-level unique constraint (user_id, snack_id).
   */
  async voteSnack(snackId: number): Promise<VoteResponse> {
    const response = await apiClient.post<VoteResponse>(`/snacks/${snackId}/vote`);
    return response.data;
  },

  /**
   * Remove the authenticated user's vote for a snack.
   */
  async unvoteSnack(snackId: number): Promise<VoteResponse> {
    const response = await apiClient.delete<VoteResponse>(`/snacks/${snackId}/vote`);
    return response.data;
  },

  /**
   * Create a new snack (Administrator only).
   */
  async createSnack(data: SnackCreateInput): Promise<Snack> {
    const response = await apiClient.post<Snack>('/snacks', data);
    return response.data;
  },

  /**
   * Update an existing snack's details (Administrator only).
   */
  async updateSnack(snackId: number, data: SnackUpdateInput): Promise<Snack> {
    const response = await apiClient.patch<Snack>(`/snacks/${snackId}`, data);
    return response.data;
  },

  /**
   * Delete a snack and associated records (Administrator only).
   */
  async deleteSnack(snackId: number): Promise<{ message: string; id: number }> {
    const response = await apiClient.delete<{ message: string; id: number }>(`/snacks/${snackId}`);
    return response.data;
  },

  /**
   * Restock a snack with positive amount and log restocked activity (Administrator only).
   */
  async restockSnack(snackId: number, amount: number): Promise<RestockResponse> {
    const response = await apiClient.post<RestockResponse>(`/snacks/${snackId}/restock`, {
      amount,
    });
    return response.data;
  },
};
