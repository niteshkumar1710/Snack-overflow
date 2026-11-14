import React, { useEffect, useState } from 'react';
import { Coffee, Layers, ShieldCheck, Database, CheckCircle, Terminal } from 'lucide-react';
import { HealthBadge } from './components/HealthBadge';
import { fetchHealth } from './api/health';
import { getErrorMessage } from './api/client';
import { BackendHealthResponse } from './types';

export const App: React.FC = () => {
  const [health, setHealth] = useState<BackendHealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchHealth();
      setHealth(data);
    } catch (err) {
      setError(getErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20">
              <Coffee className="w-6 h-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-slate-900">Snack Overflow</span>
              <span className="hidden sm:inline-block ml-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wider bg-amber-100 text-amber-800 rounded">
                Stage 1 Setup
              </span>
            </div>
          </div>
          <div className="text-xs text-slate-500">
            Pantry Inventory & Concurrency Management
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 space-y-8 w-full">
        {/* Hero Section */}
        <section className="bg-gradient-to-br from-slate-900 to-slate-800 text-white rounded-2xl p-8 shadow-xl relative overflow-hidden">
          <div className="relative z-10 max-w-2xl space-y-3">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-amber-500/20 text-amber-300 text-xs font-medium border border-amber-500/30">
              <CheckCircle className="w-3.5 h-3.5" />
              <span>Stage 1 Completed: Project Setup & Architecture</span>
            </div>
            <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
              Production-Minded Office Pantry Engine
            </h1>
            <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
              FastAPI backend running with SQLAlchemy and Pydantic validation, connecting to Supabase PostgreSQL,
              paired with a modern React + TypeScript + Vite + Tailwind CSS frontend architecture.
            </p>
          </div>
          <div className="absolute right-0 bottom-0 translate-x-12 translate-y-12 opacity-10 pointer-events-none">
            <Coffee className="w-96 h-96" />
          </div>
        </section>

        {/* Live Connectivity / Health Check Card */}
        <HealthBadge
          health={health}
          loading={loading}
          error={error}
          onRefresh={loadHealth}
        />

        {/* Architecture Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
              <Layers className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900">Modern Frontend</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              React with TypeScript, Vite bundler, and Tailwind CSS. Clean component design, modular layout,
              and strict type safety for production readiness.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900">FastAPI & PostgreSQL</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              SQLAlchemy ORM with Alembic migration scaffolding. High-performance asynchronous and pooled connections,
              configured strictly to use FastAPI as the business logic gatekeeper.
            </p>
          </div>

          <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-slate-900">Concurrency & Security</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Architected for atomic database-level operations, conditional updates, role-based JWT authorization,
              and strict API error contract enforcement.
            </p>
          </div>
        </div>

        {/* Stage Roadmap Progress */}
        <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center space-x-2 text-slate-900 font-semibold text-base">
            <Terminal className="w-5 h-5 text-amber-600" />
            <h2>Stage-by-Stage Implementation Roadmap</h2>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-900 font-medium">
              <span className="block text-amber-700 font-bold mb-1">Stage 1</span>
              Setup & Architecture (Ready)
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-500">
              <span className="block font-bold mb-1">Stage 2</span>
              Database Models & Alembic
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-500">
              <span className="block font-bold mb-1">Stage 3</span>
              JWT Auth & Roles
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-500">
              <span className="block font-bold mb-1">Stage 4</span>
              Snack Management APIs
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-500">
              <span className="block font-bold mb-1">Stage 5</span>
              Atomic Stock Consumption
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        Snack Overflow &copy; 2026. Built with FastAPI, PostgreSQL & React.
      </footer>
    </div>
  );
};

export default App;
