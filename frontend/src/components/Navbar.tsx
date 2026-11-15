import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import {
  Coffee,
  LogOut,
  Shield,
  User as UserIcon,
  LayoutDashboard,
  Cookie,
  History,
  Menu,
  X,
  Activity as ActivityIcon,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Navbar: React.FC = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    setMobileMenuOpen(false);
    logout();
    navigate('/login');
  };

  const isCurrent = (path: string) => {
    if (path === '/') {
      return location.pathname === '/';
    }
    return location.pathname.startsWith(path);
  };

  const closeMenu = () => setMobileMenuOpen(false);

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand & Desktop Nav */}
        <div className="flex items-center space-x-6 lg:space-x-8">
          <Link
            to="/"
            onClick={closeMenu}
            className="flex items-center space-x-3 group focus:outline-none focus:ring-2 focus:ring-amber-500 rounded-xl"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-600 flex items-center justify-center text-white shadow-md shadow-amber-500/20 group-hover:scale-105 transition-transform">
              <Coffee className="w-5 h-5" />
            </div>
            <div>
              <span className="text-lg sm:text-xl font-black tracking-tight text-slate-900 group-hover:text-amber-600 transition-colors">
                Snack Overflow
              </span>
              <span className="hidden md:inline-block ml-2 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-600 rounded-md">
                Pantry Ops
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center space-x-1 lg:space-x-2">
            <Link
              to="/"
              className={`inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold transition-all ${
                isCurrent('/')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <LayoutDashboard className={`w-4 h-4 ${isCurrent('/') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>Dashboard</span>
            </Link>

            <Link
              to="/snacks"
              className={`inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold transition-all ${
                isCurrent('/snacks')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <Cookie className={`w-4 h-4 ${isCurrent('/snacks') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>Snacks Catalog</span>
            </Link>

            <Link
              to="/my-history"
              className={`inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold transition-all ${
                isCurrent('/my-history')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 shadow-xs font-bold'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
              }`}
            >
              <History className={`w-4 h-4 ${isCurrent('/my-history') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>My History</span>
            </Link>

            {isAdmin && (
              <>
                <div className="h-5 w-px bg-slate-200 mx-1 hidden lg:block" />
                <Link
                  to="/admin"
                  className={`inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold transition-all ${
                    isCurrent('/admin')
                      ? 'text-purple-900 bg-purple-50 border border-purple-200 shadow-xs font-bold'
                      : 'text-purple-700 hover:text-purple-900 hover:bg-purple-50'
                  }`}
                >
                  <Shield className={`w-4 h-4 ${isCurrent('/admin') ? 'text-purple-600' : 'text-purple-400'}`} />
                  <span>Admin Portal</span>
                </Link>

                <Link
                  to="/activities"
                  className={`inline-flex items-center space-x-2 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold transition-all ${
                    isCurrent('/activities')
                      ? 'text-purple-900 bg-purple-50 border border-purple-200 shadow-xs font-bold'
                      : 'text-purple-700 hover:text-purple-900 hover:bg-purple-50'
                  }`}
                >
                  <ActivityIcon className={`w-4 h-4 ${isCurrent('/activities') ? 'text-purple-600' : 'text-purple-400'}`} />
                  <span>Activity Log</span>
                </Link>
              </>
            )}
          </nav>
        </div>

        {/* Desktop User Info & Logout */}
        <div className="hidden md:flex items-center space-x-4">
          {user && (
            <div className="flex items-center space-x-3">
              <div className="text-right">
                <div className="text-xs lg:text-sm font-bold text-slate-900 leading-tight">
                  {user.name}
                </div>
                <div className="text-[11px] text-slate-500 max-w-[150px] truncate">
                  {user.email}
                </div>
              </div>

              <div
                className={`flex items-center space-x-1 px-2.5 py-1 rounded-full text-[11px] font-bold uppercase tracking-wider ${
                  isAdmin
                    ? 'bg-purple-100 text-purple-800 border border-purple-200'
                    : 'bg-amber-100 text-amber-800 border border-amber-200'
                }`}
              >
                {isAdmin ? <Shield className="w-3 h-3" /> : <UserIcon className="w-3 h-3" />}
                <span>{user.role}</span>
              </div>
            </div>
          )}

          <button
            onClick={handleLogout}
            className="inline-flex items-center space-x-1.5 px-3 py-2 rounded-xl text-xs lg:text-sm font-semibold text-slate-600 hover:text-rose-600 hover:bg-rose-50 border border-transparent hover:border-rose-200 transition-colors focus:outline-none focus:ring-2 focus:ring-rose-400"
            title="Log out of pantry session"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>

        {/* Mobile Hamburger Button */}
        <div className="flex items-center space-x-2 md:hidden">
          {user && (
            <div
              className={`flex items-center space-x-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                isAdmin
                  ? 'bg-purple-100 text-purple-800 border border-purple-200'
                  : 'bg-amber-100 text-amber-800 border border-amber-200'
              }`}
            >
              <span>{user.role}</span>
            </div>
          )}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            aria-expanded={mobileMenuOpen}
            aria-label="Toggle navigation menu"
            className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-amber-500"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Dropdown Navigation Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-5 space-y-3 shadow-lg animate-in slide-in-from-top-2 duration-200">
          {user && (
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="truncate">
                <p className="text-sm font-bold text-slate-900 truncate">{user.name}</p>
                <p className="text-xs text-slate-500 truncate">{user.email}</p>
              </div>
            </div>
          )}

          <nav className="flex flex-col space-y-1">
            <Link
              to="/"
              onClick={closeMenu}
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                isCurrent('/')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 font-bold'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <LayoutDashboard className={`w-4 h-4 ${isCurrent('/') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>Dashboard</span>
            </Link>

            <Link
              to="/snacks"
              onClick={closeMenu}
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                isCurrent('/snacks')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 font-bold'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <Cookie className={`w-4 h-4 ${isCurrent('/snacks') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>Snacks Catalog</span>
            </Link>

            <Link
              to="/my-history"
              onClick={closeMenu}
              className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                isCurrent('/my-history')
                  ? 'text-amber-900 bg-amber-50 border border-amber-200 font-bold'
                  : 'text-slate-700 hover:bg-slate-100'
              }`}
            >
              <History className={`w-4 h-4 ${isCurrent('/my-history') ? 'text-amber-600' : 'text-slate-400'}`} />
              <span>My Consumption History</span>
            </Link>

            {isAdmin && (
              <>
                <div className="pt-2 pb-1 border-t border-slate-100 text-[10px] font-bold uppercase tracking-wider text-slate-400 px-3">
                  Admin Administration
                </div>
                <Link
                  to="/admin"
                  onClick={closeMenu}
                  className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                    isCurrent('/admin')
                      ? 'text-purple-900 bg-purple-50 border border-purple-200 font-bold'
                      : 'text-purple-700 hover:bg-purple-50'
                  }`}
                >
                  <Shield className={`w-4 h-4 ${isCurrent('/admin') ? 'text-purple-600' : 'text-purple-400'}`} />
                  <span>Admin Portal</span>
                </Link>

                <Link
                  to="/activities"
                  onClick={closeMenu}
                  className={`flex items-center space-x-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition-colors ${
                    isCurrent('/activities')
                      ? 'text-purple-900 bg-purple-50 border border-purple-200 font-bold'
                      : 'text-purple-700 hover:bg-purple-50'
                  }`}
                >
                  <ActivityIcon className={`w-4 h-4 ${isCurrent('/activities') ? 'text-purple-600' : 'text-purple-400'}`} />
                  <span>Activity Log</span>
                </Link>
              </>
            )}
          </nav>

          <div className="pt-2 border-t border-slate-100">
            <button
              onClick={handleLogout}
              className="w-full flex items-center justify-center space-x-2 px-4 py-2.5 rounded-xl text-sm font-bold text-rose-700 bg-rose-50 hover:bg-rose-100 border border-rose-200 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              <span>Log Out</span>
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
