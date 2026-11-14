import React, { useEffect, useState, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Package,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  RefreshCw,
  AlertCircle,
  PieChart,
  ArrowRight,
  Cookie,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { summaryApi } from '../api/summary';
import { PantrySummary } from '../types';
import { getErrorMessage } from '../api/client';
import { SummaryCard } from '../components/SummaryCard';
import { SnackOfTheWeekCard } from '../components/SnackOfTheWeekCard';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [summary, setSummary] = useState<PantrySummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await summaryApi.getSummary();
      setSummary(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSummary();
  }, [fetchSummary]);

  // Derived percentages for inventory health distribution bar
  const total = summary?.total_snacks || 0;
  const stockedPercent = total > 0 ? Math.round(((summary?.stocked_count || 0) / total) * 100) : 0;
  const runningLowPercent = total > 0 ? Math.round(((summary?.running_low_count || 0) / total) * 100) : 0;
  const gonePercent = total > 0 ? Math.round(((summary?.gone_count || 0) / total) * 100) : 0;

  return (
    <div className="space-y-8">
      {/* Welcome & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Pantry Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Welcome back, <span className="font-semibold text-slate-700">{user?.name}</span>! Here is
            the live inventory status of the office pantry.
          </p>
        </div>

        <button
          onClick={fetchSummary}
          disabled={loading}
          className="inline-flex items-center space-x-2 px-4 py-2 rounded-xl text-sm font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-sm disabled:opacity-50 transition-colors self-start sm:self-auto"
        >
          <RefreshCw className={`w-4 h-4 text-slate-500 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Metrics</span>
        </button>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-center justify-between text-rose-800 text-sm">
          <div className="flex items-center space-x-3">
            <AlertCircle className="w-5 h-5 text-rose-500 flex-shrink-0" />
            <div>
              <p className="font-semibold">Unable to load pantry metrics</p>
              <p className="text-xs text-rose-700">{error}</p>
            </div>
          </div>
          <button
            onClick={fetchSummary}
            className="px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-800 rounded-lg text-xs font-semibold transition-colors"
          >
            Retry
          </button>
        </div>
      )}

      {/* 4 Summary Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <SummaryCard
          title="Total Snacks"
          value={summary?.total_snacks ?? 0}
          subtitle="Registered in pantry"
          icon={Package}
          colorScheme="blue"
          loading={loading}
        />
        <SummaryCard
          title="Stocked"
          value={summary?.stocked_count ?? 0}
          subtitle="Above low-stock threshold"
          icon={CheckCircle2}
          colorScheme="emerald"
          loading={loading}
        />
        <SummaryCard
          title="Running Low"
          value={summary?.running_low_count ?? 0}
          subtitle="At or below threshold"
          icon={AlertTriangle}
          colorScheme="amber"
          loading={loading}
        />
        <SummaryCard
          title="Out of Stock"
          value={summary?.gone_count ?? 0}
          subtitle="Depleted packets"
          icon={XCircle}
          colorScheme="rose"
          loading={loading}
        />
      </div>

      {/* Snack of the Week Spotlight */}
      <section className="space-y-3">
        <SnackOfTheWeekCard
          snack={summary?.snack_of_the_week ?? null}
          loading={loading}
        />
      </section>

      {/* Inventory Health Distribution Bar */}
      <section className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <PieChart className="w-5 h-5 text-amber-500" />
            <h2 className="text-base font-bold text-slate-900">Inventory Health Breakdown</h2>
          </div>
          <span className="text-xs text-slate-500 font-medium">
            {total} total items monitored
          </span>
        </div>

        {/* Multi-segment progress bar */}
        <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden flex">
          <div
            style={{ width: `${stockedPercent}%` }}
            className="bg-emerald-500 transition-all duration-500"
            title={`Stocked: ${stockedPercent}%`}
          />
          <div
            style={{ width: `${runningLowPercent}%` }}
            className="bg-amber-500 transition-all duration-500"
            title={`Running Low: ${runningLowPercent}%`}
          />
          <div
            style={{ width: `${gonePercent}%` }}
            className="bg-rose-500 transition-all duration-500"
            title={`Out of Stock: ${gonePercent}%`}
          />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-6 pt-2 text-xs">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-emerald-500" />
            <span className="font-semibold text-slate-700">Stocked:</span>
            <span className="text-slate-500">{stockedPercent}% ({summary?.stocked_count ?? 0})</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-amber-500" />
            <span className="font-semibold text-slate-700">Running Low:</span>
            <span className="text-slate-500">{runningLowPercent}% ({summary?.running_low_count ?? 0})</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-rose-500" />
            <span className="font-semibold text-slate-700">Out of Stock:</span>
            <span className="text-slate-500">{gonePercent}% ({summary?.gone_count ?? 0})</span>
          </div>
        </div>
      </section>

      {/* Snacks Catalog Action Banner */}
      <section className="bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-md">
        <div className="space-y-2 max-w-xl">
          <div className="inline-flex items-center space-x-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-xs font-semibold">
            <Cookie className="w-3.5 h-3.5" />
            <span>Pantry Snacks Catalog</span>
          </div>
          <h3 className="text-lg sm:text-xl font-bold tracking-tight">
            Browse, Vote & Grab Your Office Snacks
          </h3>
          <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
            Search across categories, filter by stock availability, cast your vote for Snack of the Week,
            and consume snacks with live concurrency protection.
          </p>
        </div>

        <Link
          to="/snacks"
          className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-sm bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-md shadow-amber-500/20 transition-all hover:scale-105 active:scale-95 self-start md:self-center"
        >
          <span>Open Snacks Catalog</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </section>
    </div>
  );
};
