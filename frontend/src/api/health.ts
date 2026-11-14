import { apiClient } from './client';
import { BackendHealthResponse } from '../types';

export async function fetchHealth(): Promise<BackendHealthResponse> {
  const response = await apiClient.get<BackendHealthResponse>('/health');
  return response.data;
}
