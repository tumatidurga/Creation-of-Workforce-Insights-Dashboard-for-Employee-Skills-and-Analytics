import React from 'react';
import { Bell, X, Check, AlertTriangle, Info, Calendar } from 'lucide-react';



export const NotificationsDrawer = ({
  isOpen,
  onClose,
  notifications,
  notificationsLoading,
  notificationsError,
  onMarkAsRead,
  onClearAll
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40 backdrop-blur-xs">
      <div className="h-full w-full max-w-sm border-l border-slate-200 bg-white p-4 shadow-2xl dark:border-slate-800 dark:bg-slate-900 dark:text-white">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Bell className="h-4 w-4 text-indigo-600" />
            <h3 className="text-sm font-bold">Notifications & Alerts</h3>
          </div>
          <div className="flex items-center gap-2">
            <button onClick={onClearAll} className="text-[11px] text-slate-400 hover:underline">
              Clear
            </button>
            <button onClick={onClose} className="rounded-md p-1 hover:bg-slate-100 dark:hover:bg-slate-800">
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {notificationsError && (
          <div className="mt-3 rounded-md border border-red-200 bg-red-50 p-2 text-[10px] text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-200">
            {notificationsError}
          </div>
        )}

        <div className="mt-4 space-y-3 overflow-y-auto max-h-[calc(100vh-8rem)] text-xs">
          {notificationsLoading ? (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
              Loading notifications...
            </div>
          ) : notifications.length === 0 ? (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
              No notifications available.
            </div>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                onClick={() => onMarkAsRead(n)}
                className={`cursor-pointer rounded-xl border p-3 transition ${
                  !(n.read ?? n.isRead ?? false)
                    ? 'border-indigo-200 bg-indigo-50/50 dark:border-indigo-900/40 dark:bg-indigo-950/30'
                    : 'border-slate-100 bg-white dark:border-slate-800 dark:bg-slate-900'
                }`}
              >
                <div className="flex items-start justify-between font-bold">
                  <span className="text-slate-900 dark:text-white">{n.title}</span>
                  <span className="text-[9px] text-slate-400 font-normal">{n.timestamp}</span>
                </div>
                <p className="mt-1 text-[11px] text-slate-600 dark:text-slate-300">{n.message}</p>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
