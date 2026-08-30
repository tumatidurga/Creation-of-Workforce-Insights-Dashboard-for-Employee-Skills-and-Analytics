import React from 'react';
import {
  LayoutDashboard,
  Users,
  Clock,
  CalendarDays,
  CalendarRange,
  FileSpreadsheet,
  Banknote,
  TrendingUp,
  BrainCircuit,
  FileText,
  ShieldAlert,
  Settings,
  Bot,
  User
} from 'lucide-react';



export const Sidebar = ({
  activeTab,
  setActiveTab,
  userRole
}) => {
  const navGroups = {
    workspace: [
      { id: 'profile', label: 'Profile Center', icon: User, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
      { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
    ],
    workforce: [
      { id: 'employees', label: 'Employee Directory', icon: Users, roles: ['HR_ADMIN', 'MANAGER'] },
      { id: 'attendance', label: 'Attendance', icon: Clock, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
      { id: 'leave', label: 'Leave Management', icon: CalendarDays, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
      { id: 'shifts', label: 'Shift Management', icon: CalendarRange, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
    ],
    operations: [
      { id: 'payroll', label: 'Payroll', icon: Banknote, roles: ['HR_ADMIN', 'MANAGER', 'EMPLOYEE'] },
      { id: 'timesheets', label: 'Timesheets', icon: FileSpreadsheet, roles: ['HR_ADMIN', 'MANAGER'] },
      { id: 'reports', label: 'Reports & Analytics', icon: FileText, roles: ['HR_ADMIN'] },
    ],
    insights: [
      { id: 'ai_planning', label: 'AI Workforce Planning', icon: BrainCircuit, roles: ['HR_ADMIN'] },
      { id: 'audit', label: 'Audit Logs', icon: ShieldAlert, roles: ['HR_ADMIN'] },
      { id: 'settings', label: 'System Settings', icon: Settings, roles: ['HR_ADMIN'] },
    ],
  };

  const visibleNav = Object.entries(navGroups).reduce((acc, [groupKey, items]) => {
    const visibleItems = items.filter((item) => item.roles.includes(userRole));
    if (visibleItems.length > 0) acc[groupKey] = visibleItems;
    return acc;
  }, {});

  return (
    <aside className="sticky top-16 z-20 flex h-[calc(100vh-4rem)] w-72 flex-col border-r border-slate-200/80 bg-slate-50/90 p-4 backdrop-blur-xl transition-all duration-300 dark:border-slate-800/80 dark:bg-slate-950/90">
      <div className="mb-5 rounded-2xl border border-indigo-100/80 bg-gradient-to-br from-indigo-50 via-white to-sky-50 p-3 dark:border-indigo-900/80 dark:from-indigo-950/40 dark:via-slate-900 dark:to-slate-900">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.24em] text-indigo-600 dark:text-indigo-300">Workspace</p>
            <h3 className="mt-1 text-sm font-bold text-slate-900 dark:text-slate-100">{userRole === 'HR_ADMIN' ? 'HR Command Center' : userRole === 'MANAGER' ? 'Manager Workspace' : 'Employee Hub'}</h3>
          </div>
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-md shadow-indigo-600/25">
            <Bot className="h-4 w-4" />
          </div>
        </div>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto pr-1">
        {Object.entries(visibleNav).map(([groupKey, items]) => (
          <div key={groupKey} className="space-y-2">
            <div className="px-2.5 text-[10px] font-bold uppercase tracking-[0.24em] text-slate-400 dark:text-slate-500">
              {groupKey === 'workspace' ? 'Workspace' : groupKey === 'workforce' ? 'Workforce' : groupKey === 'operations' ? 'Operations' : 'Insights'}
            </div>
            <nav className="space-y-1.5">
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    aria-current={isActive ? 'page' : undefined}
                    onClick={() => setActiveTab(item.id)}
                    tabIndex={0}
                    className={`group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 ${
                      isActive
                        ? 'bg-slate-900 text-white shadow-lg shadow-slate-900/10 dark:bg-indigo-600 dark:text-white'
                        : 'text-slate-700 hover:bg-slate-200/80 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-slate-100'
                    }`}
                  >
                    <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-slate-500 dark:text-slate-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400'}`} />
                    <span className="truncate">{item.label}</span>
                    {item.id === 'ai_planning' && (
                      <span className="ml-auto rounded-full bg-violet-100 px-1.5 py-0.5 text-[8px] font-bold uppercase tracking-[0.12em] text-violet-700 dark:bg-violet-950/80 dark:text-violet-300">
                        AI
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        ))}
      </div>

      <div className="mt-auto rounded-2xl border border-emerald-100 bg-gradient-to-br from-emerald-50 via-white to-sky-50 p-3.5 shadow-sm dark:border-emerald-900/80 dark:from-emerald-950/40 dark:via-slate-900 dark:to-slate-900">
        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500 shadow-[0_0_18px_rgba(16,185,129,0.9)]" />
          <span className="text-[11px] font-bold text-slate-800 dark:text-slate-200">Live operations status</span>
        </div>
        <p className="mt-2 text-[10px] leading-relaxed text-slate-500 dark:text-slate-400">Attendance, approvals, and workforce data are syncing with the real backend.</p>
      </div>
    </aside>
  );
};
