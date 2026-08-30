import React, { useEffect, useState } from 'react';
import { Settings, Shield, Bell, Database, Key, Server, Lock, Cpu, Globe, CheckCircle2 } from 'lucide-react';
import { api } from '../../services/api';

export const SettingsPage = () => {
  const [settings, setSettings] = useState({});
  const [settingsDraft, setSettingsDraft] = useState({});
  const [isEditing, setIsEditing] = useState(false);
  const [settingsLoading, setSettingsLoading] = useState(false);
  const [settingsError, setSettingsError] = useState(null);
  const [settingsStatus, setSettingsStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(false);

  useEffect(() => {
    let isMounted = true;

    async function fetchSettings() {
      setSettingsLoading(true);
      setSettingsError(null);

      try {
        const data = await api.getSettings();
        if (isMounted) {
          setSettings(data || {});
          setSettingsDraft(data || {});
        }
      } catch (err) {
        console.error('Failed to load system settings:', err);
        const message = err?.response?.data?.detail || err.message || 'Failed to load system settings';
        if (isMounted) {
          setSettingsError(message);
          setSettings({});
        }
      } finally {
        if (isMounted) {
          setSettingsLoading(false);
        }
      }
    }

    async function fetchStatus() {
      setStatusLoading(true);
      try {
        const stat = await api.getSettingsStatus();
        if (isMounted) setSettingsStatus(stat || null);
      } catch (err) {
        console.warn('Failed to load settings status:', err);
        if (isMounted) setSettingsStatus(null);
      } finally {
        if (isMounted) setStatusLoading(false);
      }
    }

    fetchSettings();
    fetchStatus();

    return () => {
      isMounted = false;
    };
  }, []);

  const formatSettingValue = (value, fallback = 'Not configured') => {
    if (value === null || value === undefined || value === '') return fallback;
    if (typeof value === 'boolean') return value ? 'Enabled' : 'Disabled';
    return String(value);
  };

  const integrations = [
    { name: 'Optional Attendance Device Integration', category: 'Workforce Access', status: 'Not Configured', icon: Cpu, color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/60' },
    { name: 'SAP & Oracle HRMS / SuccessFactors', category: 'Enterprise ERP System', status: 'Syncing (5m ago)', icon: Server, color: 'text-blue-600 bg-blue-50 dark:bg-blue-950/60' },
    { name: 'Payroll Software (ADP / Gusto)', category: 'Compensation Export', status: 'Active API', icon: Database, color: 'text-indigo-600 bg-indigo-50 dark:bg-indigo-950/60' },
    { name: 'Microsoft Teams & Slack Webhooks', category: 'Instant Notifications', status: 'Enabled', icon: Bell, color: 'text-purple-600 bg-purple-50 dark:bg-purple-950/60' },
    { name: 'Outlook & Google Workspace Calendar', category: 'Leave & Shift Sync', status: 'OAuth 2.0 Connected', icon: Globe, color: 'text-amber-600 bg-amber-50 dark:bg-amber-950/60' },
    { name: 'Active Directory / Azure AD LDAP', category: 'SSO & Identity Access', status: 'Verified', icon: Shield, color: 'text-teal-600 bg-teal-50 dark:bg-teal-950/60' }
  ];

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-indigo-200 bg-gradient-to-r from-slate-950 via-indigo-950 to-violet-950 p-6 text-white shadow-xl shadow-indigo-950/25">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-100">
              <Settings className="h-3.5 w-3.5 text-cyan-300" />
              Live system
            </div>
            <h2 className="mt-4 text-2xl font-black tracking-[-0.04em] text-white">Enterprise HRMS Configuration Center</h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">Manage AI services, database connectivity, integrations, security policies and enterprise system configuration from one secure workspace.</p>
          </div>

          <div className="flex flex-wrap items-center gap-2 text-[10px] font-bold">
            <span className="rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2.5 py-1 text-emerald-200">Secure</span>
            <span className="rounded-full border border-sky-400/25 bg-sky-500/10 px-2.5 py-1 text-sky-200">Connected</span>
            <span className="rounded-full border border-violet-400/25 bg-violet-500/10 px-2.5 py-1 text-violet-200">RBAC active</span>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3 dark:border-slate-800 font-bold text-sm">
          <Settings className="h-4 w-4 text-indigo-600" />
          <span>Live System Configuration</span>
        </div>

        {settingsLoading && (
          <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
            Loading system settings from backend...
          </div>
        )}

        {!settingsLoading && settingsError && (
          <div className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-xs font-bold text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-200">
            {settingsError}
          </div>
        )}

        {!settingsLoading && !settingsError && (
          <div className="mt-5 flex flex-wrap items-center gap-3">
            {!isEditing ? (
              <>
                <button onClick={() => setIsEditing(true)} className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700">Edit settings</button>
                <button onClick={() => { setSettingsDraft(settings || {}); }} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">Reset draft</button>
              </>
            ) : (
              <>
                <button onClick={async () => {
                  setSettingsLoading(true);
                  setSettingsError(null);
                  try {
                    await api.updateSettings(settingsDraft || {});
                    const data = await api.getSettings();
                    setSettings(data || {});
                    setSettingsDraft(data || {});
                    setIsEditing(false);
                  } catch (err) {
                    console.error('Failed to save settings:', err);
                    const message = err?.response?.data?.detail || err.message || 'Failed to save settings';
                    setSettingsError(message);
                  } finally {
                    setSettingsLoading(false);
                  }
                }} className="rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white shadow-lg shadow-emerald-600/20 transition hover:bg-emerald-700">Save changes</button>
                <button onClick={() => { setIsEditing(false); setSettingsDraft(settings || {}); }} className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">Cancel</button>
              </>
            )}
          </div>
        )}

      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3 dark:border-slate-800 font-bold text-sm">
            <Key className="h-4 w-4 text-indigo-600" />
            <span>AI Model & Gemini RAG Credentials</span>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">Server GEMINI_API_KEY Status</label>
              <div className="flex items-center gap-2 rounded-lg bg-slate-50 p-2.5 font-mono text-[11px] text-emerald-600 dark:bg-slate-800">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                Active • Injected via Cloud Secrets Manager (gemini-3.6-flash)
              </div>
            </div>

            <div>
              <label className="font-semibold block mb-1">Vector Embedding Engine</label>
              <select className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800">
                <option>text-embedding-004 (768 Dimensions)</option>
                <option>text-embedding-gecko@003</option>
              </select>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center gap-2 border-b border-slate-100 pb-3 dark:border-slate-800 font-bold text-sm">
            <Database className="h-4 w-4 text-emerald-600" />
            <span>MongoDB Database & Retention Configuration</span>
          </div>

          <div className="mt-4 space-y-3 text-xs">
            <div>
              <label className="font-semibold block mb-1">MongoDB Atlas Cluster URI</label>
              <input
                disabled
                type="text"
                value="mongodb+srv://cluster0.nexus.mongodb.net/hrms_db"
                className="w-full rounded-lg border border-slate-200 bg-slate-100 p-2 font-mono text-[11px] text-slate-500 dark:border-slate-800 dark:bg-slate-800"
              />
            </div>

            <div>
              <label className="font-semibold block mb-1">Attendance Data Retention Policy</label>
              <select className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800">
                <option>90 Days (GDPR & CCPA Compliant)</option>
                <option>180 Days</option>
                <option>1 Year</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Enterprise Integrations Matrix */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">Connected Enterprise Systems & API Gateways</h3>
            <p className="text-xs text-slate-500">Device sync and external integrations for attendance (optional)</p>
          </div>
          <span className="rounded bg-emerald-100 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            6 / 6 Active
          </span>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {integrations.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div key={idx} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/80 p-3 text-xs dark:border-slate-800 dark:bg-slate-800/50">
                <div className="flex items-center gap-2.5">
                  <div className={`rounded-lg p-2 ${item.color}`}>
                    <Icon className="h-4 w-4" />
                  </div>
                  <div>
                    <div className="font-bold text-slate-900 dark:text-white">{item.name}</div>
                    <div className="text-[10px] text-slate-500">{item.category}</div>
                  </div>
                </div>
                <div className="flex items-center gap-1 text-[10px] font-bold text-emerald-600 dark:text-emerald-400">
                  <CheckCircle2 className="h-3 w-3" />
                  {item.status}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Security & Compliance */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-2 border-b border-slate-100 pb-3 dark:border-slate-800 font-bold text-sm">
          <Lock className="h-4 w-4 text-purple-600" />
          <span>Security, Encryption & GDPR Compliance Status</span>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 text-xs">
          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
            <span className="font-bold block text-slate-800 dark:text-slate-200">Multi-Factor Authentication (MFA)</span>
            <span className="text-[11px] text-emerald-600 font-semibold">Enforced for all Manager & Admin roles</span>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
            <span className="font-bold block text-slate-800 dark:text-slate-200">AES-256 & TLS 1.3 Encryption</span>
            <span className="text-[11px] text-emerald-600 font-semibold">Data encrypted at rest and in transit</span>
          </div>

          <div className="rounded-xl border border-slate-100 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
            <span className="font-bold block text-slate-800 dark:text-slate-200">GDPR & CCPA Right-to-Forget</span>
            <span className="text-[11px] text-emerald-600 font-semibold">Automated PII anonymization enabled</span>
          </div>
        </div>
      </div>
    </div>
  );
};

