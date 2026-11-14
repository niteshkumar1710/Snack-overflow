import React from 'react';
import { Activity, CheckCircle2, AlertTriangle, Database, Server } from 'lucide-react';
import { BackendHealthResponse } from '../types';

interface HealthBadgeProps {
  health: BackendHealthResponse | null;
  loading: boolean;
  error: string | null;
  onRefresh: () => void;
}

export const HealthBadge: React.FC<HealthBadgeProps> = ({
  health,
  loading,
  error,
  onRefresh,
}) => {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
      <div className="flex items-center justify-between border-b pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-amber-50 rounded-lg text-amber-600">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 text-lg">System Health & Architecture</h3>
            <p className="text-xs text-gray-500">Live backend verification endpoint</p>
          </div>
        </div>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="text-xs px-3 py-1.5 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md transition font-medium disabled:opacity-50"
        >
          {loading ? 'Checking...' : 'Refresh Status'}
        </button>
      </div>

      {loading && !health && (
        <div className="flex items-center space-x-2 text-gray-500 py-4 justify-center">
          <div className="w-4 h-4 border-2 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm">Connecting to FastAPI backend...</span>
        </div>
      )}

      {error && (
        <div className="p-3 bg-red-50 border border-red-200 rounded-lg flex items-start space-x-3 text-red-700">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium">Backend Connection Error</p>
            <p className="text-xs mt-0.5 text-red-600">{error}</p>
            <p className="text-xs mt-2 text-gray-600">Ensure the FastAPI server is running at <code className="bg-gray-100 px-1 py-0.5 rounded">http://localhost:8000</code>.</p>
          </div>
        </div>
      )}

      {health && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* FastAPI Service Status */}
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-gray-700 font-medium text-sm">
                <Server className="w-4 h-4 text-indigo-600" />
                <span>FastAPI Service</span>
              </div>
              <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                <CheckCircle2 className="w-3 h-3 mr-1" />
                Online
              </span>
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <p>App: <span className="font-semibold text-gray-700">{health.app}</span></p>
              <p>Version: <span className="font-mono text-gray-700">{health.version}</span></p>
              <p>Environment: <span className="font-mono uppercase text-gray-700">{health.environment}</span></p>
            </div>
          </div>

          {/* Database Connection Status */}
          <div className="p-4 rounded-lg bg-gray-50 border border-gray-100 space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2 text-gray-700 font-medium text-sm">
                <Database className="w-4 h-4 text-emerald-600" />
                <span>PostgreSQL (Supabase)</span>
              </div>
              {health.database.connected ? (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                  <CheckCircle2 className="w-3 h-3 mr-1" />
                  Connected
                </span>
              ) : (
                <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-amber-100 text-amber-800">
                  <AlertTriangle className="w-3 h-3 mr-1" />
                  Awaiting Credentials
                </span>
              )}
            </div>
            <div className="text-xs text-gray-500 space-y-1">
              <p>Status: <span className={health.database.connected ? "text-emerald-700 font-medium" : "text-amber-700 font-medium"}>
                {health.database.connected ? 'Operational' : 'Disconnected / Unreachable'}
              </span></p>
              <p className="truncate text-gray-600" title={health.database.message}>
                {health.database.connected ? 'Connection pool active' : health.database.message}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
