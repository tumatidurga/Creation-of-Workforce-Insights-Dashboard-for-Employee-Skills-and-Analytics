import React, { useState } from 'react';
import {
  Bell,
  Bot,
  Building2,
  ChevronDown,
  LogOut,
  Search,
  Shield,
  User,
} from 'lucide-react';

import { AvatarDisplay } from '../common/AvatarDisplay';
import { ProfileDrawer } from '../profile/ProfileDrawer';

export const Navbar = ({
  userRole,
  onOpenAIChat,
  onToggleNotifications,
  unreadCount,
  searchQuery,
  setSearchQuery,
  currentEmpName,
  currentEmpId,
  profile,
  onLogout,
  onRequestChangePassword,
  onProfileUpdated,
  onOpenProfile,
}) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const roleLabel = userRole === 'HR_ADMIN' ? 'HR Admin' : userRole === 'MANAGER' ? 'Manager' : 'Employee Self-Service';

  return (
    <header className="sticky top-0 z-30 flex h-16 w-full items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur transition-all sm:px-6 dark:border-slate-800 dark:bg-slate-900/95">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-500 text-white shadow-md shadow-indigo-500/20">
          <Building2 className="h-5 w-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-tight text-slate-900 dark:text-white">
              NEXUS<span className="text-indigo-600 dark:text-indigo-400">.AI</span>
            </h1>
            <span className="hidden rounded-md bg-indigo-50 px-2 py-0.5 text-[10px] font-semibold tracking-wider text-indigo-700 sm:inline-block dark:bg-indigo-950/60 dark:text-indigo-300">
              ENTERPRISE HRMS
            </span>
          </div>
          <p className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
            Workforce Management Automation
          </p>
        </div>
      </div>

      <div className="hidden max-w-md flex-1 px-8 md:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search employee ID, department, skill, or policy..."
            className="w-full rounded-lg border border-slate-200 bg-slate-50 py-1.5 pl-9 pr-4 text-xs text-slate-900 transition focus:border-indigo-500 focus:bg-white focus:outline-none focus:ring-1 focus:ring-indigo-500 dark:border-slate-800 dark:bg-slate-800/60 dark:text-slate-100 dark:focus:bg-slate-800"
          />
        </div>
      </div>

      <div className="flex items-center gap-3">
        <button
          onClick={onOpenAIChat}
          className="group relative flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-700 p-[1.5px] shadow-sm transition-all duration-200 hover:shadow-md hover:shadow-indigo-500/20"
        >
          <div className="flex items-center gap-2 rounded-[10px] bg-white px-3 py-1.5 text-xs font-bold text-slate-800 transition-all duration-200 group-hover:bg-slate-50 dark:bg-slate-900 dark:text-slate-100 dark:group-hover:bg-slate-850">
            <Bot className="h-4 w-4 text-indigo-600 dark:text-indigo-400" />
            <span className="tracking-tight">Nexus AI Assistant</span>
          </div>
        </button>

        <button
          onClick={onToggleNotifications}
          className="relative rounded-lg border border-slate-200 p-2 text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:border-slate-800 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-100"
          title="Notifications & Alerts"
        >
          <Bell className="h-4 w-4" />
          {unreadCount > 0 && (
            <span className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white ring-2 ring-white dark:ring-slate-900">
              {unreadCount}
            </span>
          )}
        </button>

        <div className="relative border-l border-slate-200 pl-2 dark:border-slate-800">
          <button
            type="button"
            onClick={() => setMenuOpen((open) => !open)}
            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-slate-50 px-2 py-1.5 text-left transition hover:border-indigo-200 hover:bg-white dark:border-slate-800 dark:bg-slate-800/70 dark:hover:border-indigo-800 dark:hover:bg-slate-800"
          >
            <AvatarDisplay
              profile={profile}
              name={currentEmpName || 'User'}
              size="sm"
              className="border-0 bg-indigo-100 text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-300"
            />
            <div className="hidden text-left lg:block">
              <div className="text-xs font-bold text-slate-800 dark:text-slate-200">{currentEmpName || 'User'}</div>
              <div className="text-[10px] font-medium text-slate-500 dark:text-slate-400">{roleLabel}</div>
            </div>
            <ChevronDown className="h-4 w-4 text-slate-500" />
          </button>

          {menuOpen && (
            <div className="absolute right-0 top-12 z-40 w-64 rounded-xl border border-slate-200 bg-white p-3 shadow-lg dark:border-slate-800 dark:bg-slate-900">
              <div className="space-y-2 border-b border-slate-200 pb-2 dark:border-slate-800">
                <div className="text-sm font-bold text-slate-900 dark:text-slate-100">{currentEmpName || 'User'}</div>
                {currentEmpId && (
                  <div className="text-xs text-slate-500 dark:text-slate-400">{currentEmpId}</div>
                )}
                <div className="inline-flex items-center gap-1.5 rounded-full bg-indigo-50 px-2 py-1 text-[10px] font-semibold text-indigo-700 dark:bg-indigo-950/70 dark:text-indigo-300">
                  {userRole === 'HR_ADMIN' ? <Shield className="h-3 w-3" /> : <User className="h-3 w-3" />}
                  {roleLabel}
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onOpenProfile && onOpenProfile();
                }}
                className="mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                <User className="h-4 w-4" />
                Profile
              </button>
              <button
                type="button"
                onClick={() => {
                  setMenuOpen(false);
                  onLogout && onLogout();
                }}
                className="mt-2 flex w-full items-center gap-2 rounded-lg px-2 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          )}
        </div>
      </div>

    </header>
  );
};
