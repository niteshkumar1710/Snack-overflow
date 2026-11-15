import React, { useEffect, useState, useCallback } from 'react';
import {
  Plus,
  PackagePlus,
  Edit2,
  Trash2,
  Search,
  X,
  RotateCcw,
  CheckCircle,
  AlertTriangle,
  Heart,
  Package,
} from 'lucide-react';
import { snackApi } from '../api/snacks';
import { getErrorMessage } from '../api/client';
import { Snack, PaginatedSnacks, RestockResponse, StockUpdatedEvent } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { CategoryBadge } from '../components/CategoryBadge';
import { Pagination } from '../components/Pagination';
import { AddEditSnackModal } from '../components/AddEditSnackModal';
import { RestockModal } from '../components/RestockModal';
import { DeleteConfirmModal } from '../components/DeleteConfirmModal';
import { usePantryWebSocket } from '../hooks/usePantryWebSocket';

interface AlertNotification {
  type: 'success' | 'error';
  message: string;
}

export const AdminPage: React.FC = () => {
  const [snacks, setSnacks] = useState<Snack[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  const [search, setSearch] = useState<string>('');
  const [debouncedSearch, setDebouncedSearch] = useState<string>('');
  const [category, setCategory] = useState<string>('');
  const [status, setStatus] = useState<string>('');

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [notification, setNotification] = useState<AlertNotification | null>(null);

  // Modals state
  const [isAddEditOpen, setIsAddEditOpen] = useState(false);
  const [addEditMode, setAddEditMode] = useState<'add' | 'edit'>('add');
  const [selectedSnack, setSelectedSnack] = useState<Snack | null>(null);

  const [isRestockOpen, setIsRestockOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);

  // Debounce search typing
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(search);
      setPage(1);
    }, 350);
    return () => clearTimeout(handler);
  }, [search]);

  // Auto-dismiss notification after 5s
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

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

  // Modal Handlers
  const handleOpenAdd = () => {
    setSelectedSnack(null);
    setAddEditMode('add');
    setIsAddEditOpen(true);
  };

  const handleOpenEdit = (snack: Snack) => {
    setSelectedSnack(snack);
    setAddEditMode('edit');
    setIsAddEditOpen(true);
  };

  const handleOpenRestock = (snack: Snack) => {
    setSelectedSnack(snack);
    setIsRestockOpen(true);
  };

  const handleOpenDelete = (snack: Snack) => {
    setSelectedSnack(snack);
    setIsDeleteOpen(true);
  };

  const handleAddEditSuccess = (savedSnack: Snack, mode: 'add' | 'edit') => {
    if (mode === 'add') {
      setNotification({
        type: 'success',
        message: `Successfully created snack '${savedSnack.name}' with ${savedSnack.quantity} initial packets.`,
      });
      loadSnacks();
    } else {
      setNotification({
        type: 'success',
        message: `Updated snack '${savedSnack.name}'.`,
      });
      setSnacks((prev) => prev.map((s) => (s.id === savedSnack.id ? savedSnack : s)));
    }
  };

  const handleRestockSuccess = (response: RestockResponse) => {
    setNotification({
      type: 'success',
      message: response.message,
    });
    setSnacks((prev) =>
      prev.map((s) => (s.id === response.snack.id ? response.snack : s))
    );
  };

  const handleDeleteConfirm = async (snackId: number) => {
    try {
      const res = await snackApi.deleteSnack(snackId);
      setNotification({
        type: 'success',
        message: res.message || 'Snack was deleted successfully.',
      });
      loadSnacks();
    } catch (err: any) {
      setNotification({
        type: 'error',
        message: getErrorMessage(err),
      });
    }
  };

  const handleResetFilters = () => {
    setSearch('');
    setDebouncedSearch('');
    setCategory('');
    setStatus('');
    setPage(1);
  };

  return (
    <div className="space-y-6">
      {/* Header & Primary Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Pantry Administration
            </h1>
            <span className="px-2 py-0.5 rounded-full text-xs font-bold uppercase tracking-wider bg-purple-100 text-purple-800 border border-purple-200">
              Admin Only
            </span>
          </div>
          <p className="text-sm text-slate-500 mt-1">
            Manage pantry snacks, update inventory quantities, configure thresholds, and restock packets.
          </p>
        </div>

        <button
          onClick={handleOpenAdd}
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-xs sm:text-sm text-white bg-amber-600 hover:bg-amber-700 shadow-md shadow-amber-600/20 transition-all hover:scale-105 active:scale-95 self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add New Snack</span>
        </button>
      </div>

      {/* Floating Notification Toast */}
      {notification && (
        <div
          className={`p-4 rounded-2xl border shadow-lg flex items-center justify-between gap-3 animate-in fade-in slide-in-from-top-2 duration-300 ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
              : 'bg-rose-50 border-rose-300 text-rose-900'
          }`}
        >
          <div className="flex items-center space-x-3">
            {notification.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-5 h-5 text-rose-600 flex-shrink-0" />
            )}
            <p className="text-sm font-semibold">{notification.message}</p>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-slate-400 hover:text-slate-600 p-1"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search & Filters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 shadow-sm flex flex-col md:flex-row items-stretch md:items-center gap-3">
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400">
            <Search className="w-4 h-4" />
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search snacks to edit or restock..."
            className="w-full pl-10 pr-9 py-2 rounded-xl text-sm border border-slate-200 focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500 text-slate-800 placeholder-slate-400 bg-slate-50/50 focus:bg-white transition-colors"
          />
          {search && (
            <button
              onClick={() => setSearch('')}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value);
              setPage(1);
            }}
            className="py-2 pl-3 pr-8 rounded-xl text-xs font-semibold border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All Categories</option>
            <option value="sweet">Sweet</option>
            <option value="savoury">Savoury</option>
            <option value="drink">Drink</option>
            <option value="healthy-ish">Healthy-ish</option>
          </select>

          <select
            value={status}
            onChange={(e) => {
              setStatus(e.target.value);
              setPage(1);
            }}
            className="py-2 pl-3 pr-8 rounded-xl text-xs font-semibold border border-slate-200 bg-white text-slate-700 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            <option value="">All Statuses</option>
            <option value="stocked">Stocked</option>
            <option value="running_low">Running Low</option>
            <option value="gone">Out of Stock</option>
          </select>

          {(search || category || status) && (
            <button
              onClick={handleResetFilters}
              className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Admin Snacks Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-slate-500 animate-pulse space-y-3">
            <Package className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-sm font-medium">Loading pantry management records...</p>
          </div>
        ) : error ? (
          <div className="p-12 text-center text-rose-600 space-y-3">
            <AlertTriangle className="w-8 h-8 mx-auto text-rose-500" />
            <p className="text-sm font-semibold">{error}</p>
            <button
              onClick={loadSnacks}
              className="px-4 py-2 rounded-xl text-xs font-semibold bg-slate-900 text-white"
            >
              Retry
            </button>
          </div>
        ) : snacks.length === 0 ? (
          <div className="p-12 text-center text-slate-500 space-y-3">
            <Package className="w-8 h-8 mx-auto text-slate-300" />
            <p className="text-sm font-medium">No snacks found matching your criteria.</p>
            <button
              onClick={handleOpenAdd}
              className="inline-flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold text-white bg-amber-600 hover:bg-amber-700"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Add Your First Snack</span>
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50/80 border-b border-slate-200 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  <th className="py-3.5 px-5">Snack Name</th>
                  <th className="py-3.5 px-4">Category</th>
                  <th className="py-3.5 px-4">Stock / Threshold</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4">Votes</th>
                  <th className="py-3.5 px-5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-sm">
                {snacks.map((snack) => (
                  <tr key={snack.id} className="hover:bg-slate-50/70 transition-colors group">
                    <td className="py-4 px-5">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex-shrink-0 flex items-center justify-center">
                          {snack.image_url ? (
                            <img
                              src={snack.image_url}
                              alt={snack.name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                (e.target as HTMLElement).style.display = 'none';
                              }}
                            />
                          ) : (
                            <Package className="w-5 h-5 text-slate-400" />
                          )}
                        </div>
                        <div>
                          <span className="font-bold text-slate-900 block">{snack.name}</span>
                          <span className="text-[11px] text-slate-400">ID #{snack.id}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-4 px-4">
                      <CategoryBadge category={snack.category} />
                    </td>

                    <td className="py-4 px-4">
                      <span className="font-bold text-slate-900">{snack.quantity}</span>
                      <span className="text-xs text-slate-400 ml-1">
                        / min {snack.low_stock_threshold}
                      </span>
                    </td>

                    <td className="py-4 px-4">
                      <StatusBadge status={snack.status} />
                    </td>

                    <td className="py-4 px-4">
                      <div className="inline-flex items-center space-x-1 text-xs text-slate-600 font-semibold">
                        <Heart className="w-3.5 h-3.5 text-rose-500 fill-rose-500" />
                        <span>{snack.votes_count}</span>
                      </div>
                    </td>

                    <td className="py-4 px-5 text-right">
                      <div className="inline-flex items-center space-x-1.5">
                        {/* Restock Button */}
                        <button
                          onClick={() => handleOpenRestock(snack)}
                          title="Restock packets"
                          className="inline-flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-bold text-emerald-700 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-colors"
                        >
                          <PackagePlus className="w-3.5 h-3.5" />
                          <span>Restock</span>
                        </button>

                        {/* Edit Button */}
                        <button
                          onClick={() => handleOpenEdit(snack)}
                          title="Edit details"
                          className="p-1.5 rounded-lg text-slate-500 hover:text-amber-700 hover:bg-amber-50 transition-colors"
                        >
                          <Edit2 className="w-4 h-4" />
                        </button>

                        {/* Delete Button */}
                        <button
                          onClick={() => handleOpenDelete(snack)}
                          title="Delete snack"
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && !error && (
        <Pagination
          page={page}
          pageSize={pageSize}
          total={total}
          totalPages={totalPages}
          onPageChange={(p) => setPage(p)}
          onPageSizeChange={(s) => {
            setPageSize(s);
            setPage(1);
          }}
        />
      )}

      {/* Modals */}
      <AddEditSnackModal
        isOpen={isAddEditOpen}
        mode={addEditMode}
        snack={selectedSnack}
        onClose={() => setIsAddEditOpen(false)}
        onSuccess={handleAddEditSuccess}
      />

      <RestockModal
        isOpen={isRestockOpen}
        snack={selectedSnack}
        onClose={() => setIsRestockOpen(false)}
        onSuccess={handleRestockSuccess}
      />

      <DeleteConfirmModal
        isOpen={isDeleteOpen}
        snack={selectedSnack}
        onClose={() => setIsDeleteOpen(false)}
        onConfirm={handleDeleteConfirm}
      />
    </div>
  );
};
