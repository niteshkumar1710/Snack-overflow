import React, { useEffect, useState, useCallback } from 'react';
import {
  History,
  ArrowDownLeft,
  ArrowUpRight,
  RefreshCw,
  AlertCircle,
  Clock,
  User,
  Cookie,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { getActivities } from '../api/activities';
import { ActivityItem, ActivityPaginationMeta } from '../types';

export const ActivityPage: React.FC = () => {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [pagination, setPagination] = useState<ActivityPaginationMeta>({
    page: 1,
    limit: 10,
    total: 0,
    total_pages: 0,
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivitiesList = useCallback(async (page: number, limit: number) => {
    try {
      setLoading(true);
      setError(null);
      const data = await getActivities({ page, limit });
      setActivities(data.items);
      setPagination(data.pagination);
    } catch (err: unknown) {
      const axiosError = err as { response?: { data?: { error?: { message?: string } } } };
      const message =
        axiosError.response?.data?.error?.message ||
        'Failed to fetch pantry activity records. Please check your admin privileges.';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchActivitiesList(pagination.page, pagination.limit);
  }, [fetchActivitiesList, pagination.page, pagination.limit]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setPagination((prev) => ({ ...prev, page: newPage }));
    }
  };

  const handleLimitChange = (newLimit: number) => {
    setPagination((prev) => ({ ...prev, limit: newLimit, page: 1 }));
  };

  const formatTimestamp = (isoString: string) => {
    try {
      const date = new Date(isoString);
      return new Intl.DateTimeFormat('en-US', {
        dateStyle: 'medium',
        timeStyle: 'short',
      }).format(date);
    } catch {
      return isoString;
    }
  };

  const startItem = pagination.total === 0 ? 0 : (pagination.page - 1) * pagination.limit + 1;
  const endItem = Math.min(pagination.page * pagination.limit, pagination.total);

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-2 border-b border-slate-200">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-purple-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-purple-500/20">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black tracking-tight text-slate-900 sm:text-3xl">
              Activity History
            </h1>
            <p className="text-sm font-medium text-slate-500">
              Admin audit log of all pantry snack consumption and restocking events
            </p>
          </div>
        </div>

        <button
          onClick={() => fetchActivitiesList(pagination.page, pagination.limit)}
          disabled={loading}
          className="inline-flex items-center justify-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-xs hover:border-slate-300 disabled:opacity-50 transition-colors"
          title="Refresh activity logs"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-purple-600' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Error state */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-sm font-bold text-rose-900">Activity Error</h3>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
          <button
            onClick={() => fetchActivitiesList(pagination.page, pagination.limit)}
            className="text-xs font-bold text-rose-700 hover:text-rose-900 underline underline-offset-2"
          >
            Retry
          </button>
        </div>
      )}

      {/* Main Activity Table Card */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">
        {loading && activities.length === 0 ? (
          /* Initial loading state */
          <div className="py-20 flex flex-col items-center justify-center space-y-3">
            <RefreshCw className="w-8 h-8 text-purple-600 animate-spin" />
            <p className="text-sm font-medium text-slate-500">Loading activity records...</p>
          </div>
        ) : activities.length === 0 ? (
          /* Empty state */
          <div className="py-20 px-4 text-center space-y-4">
            <div className="w-16 h-16 mx-auto rounded-3xl bg-slate-100 flex items-center justify-center text-slate-400">
              <History className="w-8 h-8" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">No activity recorded yet</h3>
              <p className="text-sm text-slate-500 max-w-md mx-auto mt-1">
                When pantry members consume snacks or administrators restock inventory, logs will appear here.
              </p>
            </div>
          </div>
        ) : (
          /* Activity Table */
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50/70 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-4 px-6">User</th>
                  <th className="py-4 px-6">Snack</th>
                  <th className="py-4 px-6">Action</th>
                  <th className="py-4 px-6 text-center">Amount</th>
                  <th className="py-4 px-6 text-right">Date & Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {activities.map((item) => (
                  <tr
                    key={item.id}
                    className="hover:bg-slate-50/80 transition-colors group"
                  >
                    {/* User */}
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-600 shrink-0 font-bold text-xs">
                          {item.user?.name ? item.user.name.charAt(0).toUpperCase() : <User className="w-4 h-4" />}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 leading-snug">
                            {item.user?.name || `User #${item.user?.id || 'Unknown'}`}
                          </div>
                          <div className="text-xs text-slate-400">ID: {item.user?.id}</div>
                        </div>
                      </div>
                    </td>

                    {/* Snack */}
                    <td className="py-4 px-6">
                      <div className="flex items-center space-x-2.5">
                        <Cookie className="w-4 h-4 text-amber-500 shrink-0" />
                        <span className="font-semibold text-slate-800">
                          {item.snack?.name || `Snack #${item.snack?.id || 'Unknown'}`}
                        </span>
                      </div>
                    </td>

                    {/* Action Badge */}
                    <td className="py-4 px-6">
                      {item.action === 'restocked' ? (
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <ArrowUpRight className="w-3.5 h-3.5" />
                          <span className="capitalize">Restocked</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200">
                          <ArrowDownLeft className="w-3.5 h-3.5" />
                          <span className="capitalize">Consumed</span>
                        </span>
                      )}
                    </td>

                    {/* Amount */}
                    <td className="py-4 px-6 text-center">
                      <span className="inline-block px-2.5 py-0.5 rounded-lg text-xs font-bold bg-slate-100 text-slate-700">
                        {item.amount > 0 ? `+${item.amount}` : item.amount}
                      </span>
                    </td>

                    {/* Timestamp */}
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{formatTimestamp(item.created_at)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {pagination.total > 0 && (
          <div className="border-t border-slate-200 px-6 py-4 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="text-xs text-slate-500 font-medium">
              Showing <span className="font-bold text-slate-800">{startItem}</span> to{' '}
              <span className="font-bold text-slate-800">{endItem}</span> of{' '}
              <span className="font-bold text-slate-800">{pagination.total}</span> activity records
            </div>

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                <span>Per page:</span>
                <select
                  value={pagination.limit}
                  onChange={(e) => handleLimitChange(Number(e.target.value))}
                  className="py-1 px-2 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-purple-500 font-semibold text-slate-700"
                >
                  <option value="10">10</option>
                  <option value="25">25</option>
                  <option value="50">50</option>
                </select>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page <= 1 || loading}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <ChevronLeft className="w-3.5 h-3.5" />
                  <span>Previous</span>
                </button>

                <span className="px-3 py-1.5 rounded-xl text-xs font-bold bg-purple-50 border border-purple-200 text-purple-900">
                  Page {pagination.page} of {pagination.total_pages || 1}
                </span>

                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.total_pages || loading}
                  className="inline-flex items-center space-x-1 px-3 py-1.5 rounded-xl text-xs font-semibold border border-slate-200 text-slate-700 hover:bg-white disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                >
                  <span>Next</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
