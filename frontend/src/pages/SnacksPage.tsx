import React, { useEffect, useState, useCallback } from 'react';
import {
  PackageOpen,
  RotateCcw,
  AlertTriangle,
  Sparkles,
} from 'lucide-react';
import { snackApi } from '../api/snacks';
import { getErrorMessage } from '../api/client';
import { Snack, PaginatedSnacks, StockUpdatedEvent } from '../types';
import { SnackCard } from '../components/SnackCard';
import { FilterBar } from '../components/FilterBar';
import { Pagination } from '../components/Pagination';
import { usePantryWebSocket } from '../hooks/usePantryWebSocket';
import { calculateSnackStatus } from '../utils/snackUtils';
import { useNotification } from '../context/NotificationContext';

export const SnacksPage: React.FC = () => {
  const { showSuccess, showError, showWarning } = useNotification();
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

  // Debounce search typing
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1); // Reset to page 1 on new search
    }, 350);

    return () => clearTimeout(handler);
  }, [search]);

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

  // Real-time stock updates via WebSocket
  usePantryWebSocket(
    useCallback((event: StockUpdatedEvent) => {
      setSnacks((prevSnacks) =>
        prevSnacks.map((s) => {
          if (s.id === event.snack_id) {
            return {
              ...s,
              quantity: event.quantity,
              status: event.status,
            };
          }
          return s;
        })
      );
    }, [])
  );

  const handleResetFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setCategory('');
    setStatus('');
    setPage(1);
  };

  // Consume action with Optimistic UI, Idempotency-Key, and safe error rollback
  const handleConsume = async (snackId: number) => {
    // 1. Prevent accidental duplicate clicks
    if (consumingId === snackId) {
      return;
    }

    const currentSnack = snacks.find((s) => s.id === snackId);
    if (!currentSnack || currentSnack.quantity <= 0) {
      return;
    }

    // Save previous snapshot for rollback if network/server rejects
    const previousSnapshot = { ...currentSnack };
    const optimisticQty = Math.max(0, currentSnack.quantity - 1);
    const optimisticStatus = calculateSnackStatus(optimisticQty, currentSnack.low_stock_threshold);

    // 2. Optimistic UI update: immediately decrement displayed count
    setSnacks((prev) =>
      prev.map((s) =>
        s.id === snackId
          ? { ...s, quantity: optimisticQty, status: optimisticStatus }
          : s
      )
    );

    setConsumingId(snackId);

    // 3. Generate unique Idempotency-Key for this specific user action
    const idempotencyKey = crypto.randomUUID();

    try {
      // 4. Send request with Idempotency-Key
      const response = await snackApi.consumeSnack(snackId, 1, idempotencyKey);

      // 5. Reconcile optimistic state with the server's canonical response
      setSnacks((prev) =>
        prev.map((s) => (s.id === snackId ? { ...s, ...response.snack } : s))
      );

      // Display centered dialog popup without shifting layout
      showSuccess(response.message || 'Snack consumed successfully!', 'Enjoy Your Snack!');
    } catch (err: unknown) {
      // 6. Rollback optimistic change on failure
      setSnacks((prev) =>
        prev.map((s) => (s.id === snackId ? previousSnapshot : s))
      );

      const axiosErr = err as { response?: { status?: number; data?: { error?: { message?: string } } } };
      const errorMsg = getErrorMessage(err);

      if (axiosErr.response?.status === 409) {
        // Concurrency conflict (someone beat you to it or stock was depleted)
        showWarning(
          errorMsg || 'Someone beat you to the last packet!',
          'Concurrency Conflict'
        );
        // Resync latest authoritative inventory from server
        loadSnacks();
      } else {
        showError(
          errorMsg || 'Unable to consume this snack. Please try again.',
          'Consumption Failed'
        );
      }
    } finally {
      setConsumingId(null);
    }
  };

  // Vote / Unvote action
  const handleVoteToggle = async (snackId: number, currentlyVoted: boolean) => {
    setVotingId(snackId);
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
        showSuccess('Your vote was removed successfully.', 'Vote Retracted');
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
        showSuccess('Thank you for supporting your favorite office snack!', 'Vote Recorded!');
      }
    } catch (err: any) {
      const errorMsg = getErrorMessage(err);
      if (err?.response?.status === 409) {
        // User already voted
        setSnacks((prev) =>
          prev.map((s) => (s.id === snackId ? { ...s, user_has_voted: true } : s))
        );
        showWarning(errorMsg, 'Vote Conflict');
      } else {
        showError(errorMsg, 'Voting Failed');
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
          <h1 className="text-2xl sm:text-3xl font-black text-slate-900 tracking-tight">
            Pantry Snack Catalog
          </h1>
          <p className="text-xs sm:text-sm text-slate-500 mt-1">
            Browse available treats, vote for your favorites, and reserve snacks with live stock updates.
          </p>
        </div>

        <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-bold self-start sm:self-auto">
          <Sparkles className="w-3.5 h-3.5 text-amber-600" />
          <span>{total} Snacks Available</span>
        </div>
      </div>

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
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div
              key={i}
              className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 animate-pulse"
            >
              <div className="h-40 w-full bg-slate-200 rounded-xl" />
              <div className="h-6 w-3/4 bg-slate-200 rounded" />
              <div className="h-4 w-1/2 bg-slate-100 rounded" />
              <div className="h-2 w-full bg-slate-100 rounded" />
              <div className="h-10 w-full bg-slate-200 rounded-xl" />
            </div>
          ))}
        </div>
      ) : error ? (
        /* Error State */
        <div className="bg-white border border-rose-200 rounded-2xl p-8 sm:p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-rose-50 text-rose-500 mx-auto flex items-center justify-center">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-800">Failed to load snacks</h3>
          <p className="text-xs text-rose-600 max-w-sm mx-auto">{error}</p>
          <button
            onClick={loadSnacks}
            className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-white hover:bg-slate-800 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      ) : snacks.length === 0 ? (
        /* Empty State */
        <div className="bg-white border border-dashed border-slate-300 rounded-2xl p-8 sm:p-12 text-center space-y-4">
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
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 text-white hover:bg-amber-700 shadow-sm transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Clear All Filters</span>
            </button>
          )}
        </div>
      ) : (
        /* Snack Cards Grid - fully responsive on mobile (1 col), tablet (2 cols), desktop (3 cols) */
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 sm:gap-6">
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
