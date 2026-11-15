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

export interface RegisterPayload {
  name: string;
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
  image_url?: string | null;
  votes_count: number;
  user_has_voted?: boolean;
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

export interface StockUpdatedEvent {
  type: 'STOCK_UPDATED';
  event: 'consumed' | 'restocked';
  snack_id: number;
  snack_name: string;
  quantity: number;
  low_stock_threshold: number;
  status: SnackStatus;
  amount: number;
  user_id: number;
}

export interface Activity {
  id: number;
  user_id: number;
  snack_id: number;
  action: 'consumed' | 'restocked';
  amount: number;
  created_at: string;
}

export interface ActivityUserSummary {
  id: number;
  name: string;
}

export interface ActivitySnackSummary {
  id: number;
  name: string;
}

export interface ActivityItem {
  id: number;
  user: ActivityUserSummary;
  snack: ActivitySnackSummary;
  action: 'consumed' | 'restocked';
  amount: number;
  created_at: string;
}

export interface ActivityPaginationMeta {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
}

export interface PaginatedActivities {
  items: ActivityItem[];
  pagination: ActivityPaginationMeta;
}

export interface ConsumptionResponse {
  message: string;
  snack: Snack;
  activity: Activity;
}

export interface RestockResponse {
  message: string;
  snack: Snack;
  activity: Activity;
}

export interface SnackCreateInput {
  name: string;
  category: SnackCategory;
  quantity: number;
  low_stock_threshold: number;
  image_url?: string | null;
}

export interface SnackUpdateInput {
  name?: string;
  category?: SnackCategory;
  quantity?: number;
  low_stock_threshold?: number;
  image_url?: string | null;
}

export interface PersonalConsumptionItem {
  id: number;
  activity_id: number;
  snack_id: number;
  snack_name: string;
  snack_image_url?: string | null;
  amount: number;
  action: string;
  consumed_at: string;
  created_at: string;
}

export interface PersonalConsumptionSummary {
  total_consumed_packets: number;
  unique_snacks_tried: number;
}

export interface PersonalConsumptionHistoryResponse {
  items: PersonalConsumptionItem[];
  pagination: ActivityPaginationMeta;
  summary: PersonalConsumptionSummary;
}

export interface ConsumptionHistoryQueryParams {
  page?: number;
  limit?: number;
  start_date?: string;
  end_date?: string;
}

export interface VoteResponse {
  message: string;
  snack_id: number;
  votes_count: number;
  has_voted: boolean;
}

export interface SnackQueryParams {
  search?: string;
  category?: string;
  status?: string;
  page?: number;
  page_size?: number;
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
