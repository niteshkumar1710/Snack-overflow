import React, { useEffect, useState, useCallback } from 'react';
import {
  PackageOpen,
  RotateCcw,
  AlertTriangle,
  CheckCircle,
  X,
  Sparkles,
} from 'lucide-react';
import { snackApi } from '../api/snacks';
import { getErrorMessage } from '../api/client';
import { Snack, PaginatedSnacks } from '../types';
import { SnackCard } from '../components/SnackCard';
import { FilterBar } from '../components/FilterBar';
import { Pagination } from '../components/Pagination';

interface AlertNotification {
  type: 'success' | 'conflict' | 'error';
  title?: string;
  message: string;
}

export const SnacksPage: React.FC = () => {
  const [snacks, setSnacks] = useState<Snack[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(6);

  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [status, setStatus] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [consumingId, setConsumingId] = useState<number | null>(null);
  const [votingId, setVotingId] = useState<number | null>(null);
  const [notification, setNotification] = useState<AlertNotification | null>(null);

  // Debounce search typing
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to page 1 on new search
    }, 350);

    return () => clearTimeout(handler);
  }, [search]);

  // Auto-dismiss notifications after 5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => {
        setNotification(null);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  // Load snacks from server
  const loadSnacks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: PaginatedSnacks = await snackApi.getSnacks({
        page,
        page_size: pageSize,
        search: debouncedSearch,
        category: category || undefined,
        status: status || undefined,
      });
      setSnacks(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, debouncedSearch, category, status]);

  useEffect(() => {
    loadSnacks();
  }, [loadSnacks]);

  // Handler for reset filters
  const handleResetFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setCategory('');
    setStatus('');
    setPage(1);
  };

  // Consume action with concurrency conflict detection (HTTP 409)
  const handleConsume = async (snackId: number) => {
    setConsumingId(snackId);
    setNotification(null);
    try {
      const response = await snackApi.consumeSnack(snackId, 1);
      // Update local state with the returned updated snack
      setSnacks((prev) =>
        prev.map((s) => (s.id === snackId ? { ...s, ...response.snack } : s))
      );
      setNotification({
        type: 'success',
        title: 'Enjoy Your Snack!',
        message: response.message,
      });
    } catch (err: any) {
      const errorMsg = getErrorMessage(err);
      if (err?.response?.status === 409) {
        // Concurrency conflict: someone took the last packet or stock was depleted
        setNotification({
          type: 'conflict',
          title: 'Concurrency Conflict Detected',
          message: errorMsg || 'Someone beat you to the last packet!',
        });
        // Immediately refresh the current page to synchronize live inventory
        loadSnacks();
      } else {
        setNotification({
          type: 'error',
          title: 'Consumption Failed',
          message: errorMsg,
        });
      }
    } finally {
      setConsumingId(null);
    }
  };

  // Vote / Unvote action
  const handleVoteToggle = async (snackId: number, currentlyVoted: boolean) => {
    setVotingId(snackId);
    setNotification(null);
    try {
      if (currentlyVoted) {
        // Retract vote
        const response = await snackApi.unvoteSnack(snackId);
        setSnacks((prev) =>
          prev.map((s) =>
            s.id === snackId
              ? { ...s, votes_count: response.votes_count, user_has_voted: false }
              : s
          )
        );
        setNotification({
          type: 'success',
          message: 'Your vote was removed successfully.',
        });
      } else {
        // Cast vote
        const response = await snackApi.voteSnack(snackId);
        setSnacks((prev) =>
          prev.map((s) =>
            s.id === snackId
              ? { ...s, votes_count: response.votes_count, user_has_voted: true }
              : s
          )
        );
        setNotification({
          type: 'success',
          title: 'Vote Recorded!',
          message: 'Thank you for supporting your favorite office snack!',
        });
      }
    } catch (err: any) {
      const errorMsg = getErrorMessage(err);
      if (err?.response?.status === 409) {
        // User already voted
        setSnacks((prev) =>
          prev.map((s) => (s.id === snackId ? { ...s, user_has_voted: true } : s))
        );
        setNotification({
          type: 'conflict',
          title: 'Vote Conflict',
          message: errorMsg,
        });
      } else {
        setNotification({
          type: 'error',
          title: 'Voting Failed',
          message: errorMsg,
        });
      }
    } finally {
      setVotingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Pantry Snack Catalog
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Browse available treats, vote for your favorites, and reserve snacks with live stock updates.
          </p>
        </div>

        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-semibold self-start sm:self-auto">
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>{total} Snacks Available</span>
        </div>
      </div>

      {/* Floating Notification Toast */}
      {notification && (
        <div
          className={`p-4 rounded-2xl border shadow-lg flex items-start justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-300 ${
            notification.type === 'conflict'
              ? 'bg-amber-50 border-amber-300 text-amber-900 ring-2 ring-amber-400/30'
              : notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-rose-50 border-rose-300 text-rose-900'
          }`}
        >
          <div className="flex items-start space-x-3">
            {notification.type === 'conflict' ? (
              <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            ) : notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
            )}
            <div>
              {notification.title && (
                <p className="text-xs font-bold uppercase tracking-wider">{notification.title}</p>
              )}
              <p className="text-sm font-semibold mt-0.5">{notification.message}</p>
            </div>
          </div>

          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search & Filter Bar */}
      <FilterBar
        search={search}
        category={category}
        status={status}
        onSearchChange={setSearch}
        onCategoryChange={(cat) => {
          setCategory(cat);
          setPage(1);
        }}
        onStatusChange={(st) => {
          setStatus(st);
          setPage(1);
        }}
        onReset={handleResetFilters}
      />

      {/* Loading Skeleton */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 animate-pulse"
            >
              <div className="flex justify-between">
                <div className="h-5 w-20 bg-slate-200 rounded" />
                <div className="h-5 w-20 bg-slate-200 rounded" />
              </div>
              <div className="h-6 w-3/4 bg-slate-200 rounded" />
              <div className="h-4 w-1/2 bg-slate-100 rounded" />
              <div className="h-2 w-full bg-slate-100 rounded" />
              <div className="h-10 w-full bg-slate-200 rounded-xl" />
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="bg-white border border-rose-200 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-500 mx-auto flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Failed to load snacks</h3>
          <p className="text-xs text-rose-600 max-w-sm mx-auto">{error}</p>
          <button
            onClick={loadSnacks}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      ) : snacks.length === 0 ? (
        /* Empty State */
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-12 text-center space-y-4">
          <div className="w-14 h-14 rounded-2xl bg-amber-50 text-amber-500 mx-auto flex items-center justify-center">
            <PackageOpen className="w-8 h-8" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-800">No snacks found</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
              {search || category || status
                ? 'No snacks match your current filter criteria. Try adjusting your search query or clear the filters.'
                : 'The pantry catalog is currently empty. Check back once the administrator adds items!'}
            </p>
          </div>
          {(search || category || status) && (
            <button
              onClick={handleResetFilters}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-amber-600 text-white hover:bg-amber-700 shadow-sm transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear All Filters</span>
            </button>
          )}
        </div>
      ) : (
        /* Snack Cards Grid */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {snacks.map((snack) => (
            <SnackCard
              key={snack.id}
              snack={snack}
              isConsuming={consumingId === snack.id}
              isVoting={votingId === snack.id}
              onConsume={handleConsume}
              onVoteToggle={handleVoteToggle}
            />
          ))}
        </div>
      )}

      {/* Pagination Controls */}
      {!loading && !error && (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={(newPage) => setPage(newPage)}
          onPageSizeChange={(newSize) => {
            setPageSize(newSize);
            setPage(1);
          }}
        />
      )}
    </div>
  );
};
