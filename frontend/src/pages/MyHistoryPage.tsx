import React, { useEffect, useState, useCallback } from 'react';
import {
  History,
  ShoppingBag,
  Sparkles,
  Calendar,
  Filter,
  RefreshCw,
  AlertCircle,
  Clock,
  ChevronLeft,
  ChevronRight,
  Image as ImageIcon,
} from 'lucide-react';
import { getPersonalConsumptionHistory } from '../api/users';
import {
  PersonalConsumptionItem,
  PersonalConsumptionSummary,
  ActivityPaginationMeta,
} from '../types';

export const MyHistoryPage: React.FC = () => {
  const [items, setItems] = useState<PersonalConsumptionItem[]>([]);
  const [summary, setSummary] = useState<PersonalConsumptionSummary>({
    total_consumed_packets: 0,
    unique_snacks_tried: 0,
  });
  const [pagination, setPagination] = useState<ActivityPaginationMeta>({
    page: 1,
    limit: 10,
    total: 0,
    total_pages: 0,
  });
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHistory = useCallback(
    async (page: number, limit: number, start?: string, end?: string) => {
      try {
        setLoading(true);
        setError(null);
        const data = await getPersonalConsumptionHistory({
          page,
          limit,
          start_date: start || undefined,
          end_date: end || undefined,
        });
        setItems(data.items);
        setPagination(data.pagination);
        setSummary(data.summary);
      } catch (err: unknown) {
        const axiosError = err as { response?: { data?: { error?: { message?: string } } } };
        const message =
          axiosError.response?.data?.error?.message ||
          'Failed to fetch your personal consumption history. Please try again.';
        setError(message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    fetchHistory(pagination.page, pagination.limit, startDate, endDate);
  }, [fetchHistory, pagination.page, pagination.limit, startDate, endDate]);

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= pagination.total_pages) {
      setPagination((prev) => ({ ...prev, page: newPage }));
    }
  };

  const handleLimitChange = (newLimit: number) => {
    setPagination((prev) => ({ ...prev, limit: newLimit, page: 1 }));
  };

  const handleResetFilters = () => {
    setStartDate('');
    setEndDate('');
    setPagination((prev) => ({ ...prev, page: 1 }));
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
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-lg shadow-amber-500/20">
            <History className="w-6 h-6" />
          </div>
          <div>
            <h1 className="text-2xl font-black text-slate-900 tracking-tight">
              My Consumption History
            </h1>
            <p className="text-xs text-slate-500 mt-0.5">
              Review your personal snack consumption records, quantities, and dates.
            </p>
          </div>
        </div>

        {/* Refresh Button */}
        <button
          onClick={() => fetchHistory(pagination.page, pagination.limit, startDate, endDate)}
          disabled={loading}
          className="inline-flex items-center space-x-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 shadow-xs transition-colors disabled:opacity-50 self-start sm:self-auto"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold">
            <ShoppingBag className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Total Packets Enjoyed
            </p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              {summary.total_consumed_packets}
            </p>
          </div>
        </div>

        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
            <Sparkles className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Unique Snacks Sampled
            </p>
            <p className="text-2xl font-black text-slate-900 mt-0.5">
              {summary.unique_snacks_tried}
            </p>
          </div>
        </div>
      </div>

      {/* Date Filter Bar */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-xs flex flex-wrap items-center gap-3">
        <div className="flex items-center space-x-2 text-xs font-bold text-slate-700 uppercase tracking-wider">
          <Filter className="w-3.5 h-3.5 text-amber-600" />
          <span>Filter by Date:</span>
        </div>

        <div className="flex items-center space-x-2">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="date"
            value={startDate}
            onChange={(e) => {
              setStartDate(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-700 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-amber-500"
            title="Start Date"
          />
        </div>

        <span className="text-slate-400 text-xs font-medium">to</span>

        <div className="flex items-center space-x-2">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="date"
            value={endDate}
            onChange={(e) => {
              setEndDate(e.target.value);
              setPagination((p) => ({ ...p, page: 1 }));
            }}
            className="px-3 py-1.5 rounded-lg border border-slate-200 text-xs text-slate-700 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-amber-500"
            title="End Date"
          />
        </div>

        {(startDate || endDate) && (
          <button
            onClick={handleResetFilters}
            className="ml-auto text-xs text-amber-600 hover:text-amber-700 font-semibold underline underline-offset-2"
          >
            Clear Date Filters
          </button>
        )}
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start space-x-3 text-xs text-rose-800">
          <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-bold">Unable to load consumption history</p>
            <p className="mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Content Container */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        {loading && items.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-amber-600 animate-spin mx-auto" />
            <p className="text-sm font-semibold text-slate-700">Loading your history...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto">
              <ShoppingBag className="w-7 h-7" />
            </div>
            <h3 className="text-base font-bold text-slate-800">No Consumption Records Found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto">
              {startDate || endDate
                ? 'No snacks consumed during the selected date range. Try widening your filter.'
                : 'You have not grabbed any snacks from the pantry yet. Browse the pantry and grab your first treat!'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50/80 border-b border-slate-200 text-slate-500 uppercase tracking-wider font-bold">
                <tr>
                  <th scope="col" className="px-5 py-3.5">
                    Snack
                  </th>
                  <th scope="col" className="px-5 py-3.5">
                    Quantity Consumed
                  </th>
                  <th scope="col" className="px-5 py-3.5">
                    Date & Time
                  </th>
                  <th scope="col" className="px-5 py-3.5 text-right">
                    Activity ID
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-medium text-slate-700">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/60 transition-colors">
                    <td className="px-5 py-3.5">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex-shrink-0 flex items-center justify-center">
                          {item.snack_image_url ? (
                            <img
                              src={item.snack_image_url}
                              alt={item.snack_name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                // fallback to icon if broken URL
                                (e.target as HTMLElement).style.display = 'none';
                              }}
                            />
                          ) : (
                            <ImageIcon className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900 text-sm">{item.snack_name}</p>
                          <span className="inline-block text-[10px] text-amber-700 font-semibold bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200/50 mt-0.5">
                            Personal Consumption
                          </span>
                        </div>
                      </div>
                    </td>

                    <td className="px-5 py-3.5">
                      <span className="inline-flex items-center space-x-1 font-bold text-slate-900 bg-slate-100 px-2.5 py-1 rounded-lg">
                        <span>{item.amount}</span>
                        <span className="text-[11px] font-normal text-slate-500">
                          {item.amount === 1 ? 'packet' : 'packets'}
                        </span>
                      </span>
                    </td>

                    <td className="px-5 py-3.5">
                      <div className="flex items-center space-x-1.5 text-slate-600">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>{formatTimestamp(item.consumed_at)}</span>
                      </div>
                    </td>

                    <td className="px-5 py-3.5 text-right font-mono text-[11px] text-slate-400">
                      #{item.activity_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Bar */}
        {pagination.total > 0 && (
          <div className="border-t border-slate-200 px-5 py-3.5 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="text-xs text-slate-500 font-medium">
              Showing <span className="font-bold text-slate-800">{startItem}</span> to{' '}
              <span className="font-bold text-slate-800">{endItem}</span> of{' '}
              <span className="font-bold text-slate-800">{pagination.total}</span> items
            </div>

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-1 text-xs text-slate-500">
                <span>Per page:</span>
                <select
                  value={pagination.limit}
                  onChange={(e) => handleLimitChange(Number(e.target.value))}
                  className="py-1 px-2 border border-slate-200 rounded-lg text-xs bg-white focus:outline-none focus:ring-1 focus:ring-amber-500 font-semibold text-slate-700"
                >
                  <option value="5">5</option>
                  <option value="10">10</option>
                  <option value="25">25</option>
                </select>
              </div>

              <div className="flex items-center space-x-1">
                <button
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page <= 1}
                  className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  title="Previous Page"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="text-xs font-semibold px-2 text-slate-700">
                  {pagination.page} / {Math.max(1, pagination.total_pages)}
                </span>
                <button
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.total_pages}
                  className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  title="Next Page"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
