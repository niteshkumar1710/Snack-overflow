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
