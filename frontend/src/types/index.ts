export type UserRole = 'admin' | 'member';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export type SnackCategory = 'sweet' | 'savoury' | 'drink' | 'healthy-ish';

export type SnackStatus = 'stocked' | 'running_low' | 'gone';

export interface Snack {
  id: number;
  name: string;
  category: SnackCategory;
  quantity: number;
  low_stock_threshold: number;
  status: SnackStatus;
  votes_count: number;
  created_at: string;
  updated_at: string;
}

export interface PaginatedSnacks {
  items: Snack[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface PantrySummary {
  stocked_count: number;
  running_low_count: number;
  gone_count: number;
  total_snacks: number;
  snack_of_the_week: Snack | null;
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
  };
}

export interface BackendHealthResponse {
  status: 'healthy' | 'degraded';
  app: string;
  version: string;
  environment: string;
  database: {
    connected: boolean;
    message: string;
  };
}
