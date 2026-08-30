import React, { useEffect, useMemo, useState } from 'react';
import {
  ArrowRight,
  Briefcase,
  Building2,
  Camera,
  Check,
  ChevronRight,
  Lock,
  LogOut,
  Shield,
  User,
  X,
} from 'lucide-react';

import { api } from '../../services/api';
import { AvatarDisplay } from '../common/AvatarDisplay';
import { AVATAR_IDS, DEFAULT_AVATAR_ID } from '../../utils/avatars';

function normalizeRole(value) {
  if (!value) return 'EMPLOYEE';
  const normalized = String(value).toUpperCase();
  if (normalized.includes('HR') || normalized.includes('ADMIN')) return 'HR_ADMIN';
  if (normalized.includes('MANAGER')) return 'MANAGER';
  return 'EMPLOYEE';
}

export function ProfileDrawer({
  open,
  onClose,
  profile,
  userRole,
  currentEmpName,
  currentEmpId,
  onRequestChangePassword,
  onLogout,
  onProfileUpdated,
}) {
  const [selectedAvatarId, setSelectedAvatarId] = useState(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
  const [avatarPickerOpen, setAvatarPickerOpen] = useState(false);
  const [savingAvatar, setSavingAvatar] = useState(false);
  const [avatarError, setAvatarError] = useState('');

  useEffect(() => {
    if (!open) return;
    setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
    setAvatarError('');
  }, [open, profile]);

  const role = normalizeRole(userRole || profile?.role || 'EMPLOYEE');
  const fullName = profile?.name || currentEmpName || 'User';
  const employeeId = profile?.empId || currentEmpId || 'N/A';
  const email = profile?.email || 'N/A';
  const phone = profile?.phone || profile?.Phone || 'N/A';
  const department = profile?.department || profile?.Department || 'N/A';
  const designation = profile?.jobRole || profile?.JobRole || profile?.designation || profile?.Designation || 'N/A';
  const managerName = profile?.managerName || profile?.manager || profile?.Manager || profile?.ManagerID || profile?.reportingManager || 'N/A';
  const joiningDate = profile?.joiningDate || profile?.JoiningDate || 'N/A';
  const employmentStatus = profile?.employmentStatus || profile?.EmploymentStatus || 'N/A';
  const teamSize = profile?.teamSize || profile?.teamCount || 'N/A';

  const accessHint = useMemo(() => {
    if (role === 'HR_ADMIN') return 'Full workforce administration';
    if (role === 'MANAGER') return 'Team oversight and approvals';
    return 'Personal workspace access';
  }, [role]);

  const roleBadge = useMemo(() => {
    if (role === 'HR_ADMIN') {
      return { label: 'HR Admin', className: 'bg-violet-100 text-violet-700 ring-violet-200 dark:bg-violet-950/50 dark:text-violet-300 dark:ring-violet-900' };
    }
    if (role === 'MANAGER') {
      return { label: 'Manager', className: 'bg-blue-100 text-blue-700 ring-blue-200 dark:bg-blue-950/50 dark:text-blue-300 dark:ring-blue-900' };
    }
    return { label: 'Employee', className: 'bg-indigo-100 text-indigo-700 ring-indigo-200 dark:bg-indigo-950/50 dark:text-indigo-300 dark:ring-indigo-900' };
  }, [role]);

  const personalDetails = [
    { label: 'Full Name', value: fullName },
    { label: 'Work Email', value: email },
    { label: 'Phone Number', value: phone },
    { label: 'Employee ID', value: employeeId },
  ].filter((item) => item.value && item.value !== 'N/A');

  const workDetails = role === 'HR_ADMIN'
    ? [
        ['Department', department],
        ['Designation', designation],
        ['Joining Date', joiningDate],
        ['Employment Status', employmentStatus],
        ['Access Scope', accessHint],
      ]
    : role === 'MANAGER'
      ? [
          ['Department', department],
          ['Designation', designation],
          ['Team Size', teamSize],
          ['Joining Date', joiningDate],
          ['Employment Status', employmentStatus],
        ]
      : [
          ['Department', department],
          ['Designation', designation],
          ['Reporting Manager', managerName],
          ['Joining Date', joiningDate],
          ['Employment Status', employmentStatus],
        ];

  const handleSaveAvatar = async () => {
    if (!selectedAvatarId) return;
    setSavingAvatar(true);
    setAvatarError('');
    try {
      const updatedProfile = await api.updateProfile({ avatarId: selectedAvatarId });
      if (typeof onProfileUpdated === 'function') {
        onProfileUpdated(updatedProfile || { avatarId: selectedAvatarId });
      }
      setAvatarPickerOpen(false);
    } catch (error) {
      setAvatarError(error?.response?.data?.detail || 'Unable to save the selected avatar.');
    } finally {
      setSavingAvatar(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/45 backdrop-blur-[1px]">
      <div className="absolute inset-0" onClick={onClose} />
      <aside className="relative ml-auto flex h-full w-full max-w-xl flex-col border-l border-slate-200 bg-white shadow-2xl shadow-slate-900/10 dark:border-slate-800 dark:bg-slate-950">
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-white shadow-lg shadow-indigo-500/20">
              <AvatarDisplay profile={profile} name={fullName} size="lg" className="border-0 bg-transparent text-lg text-white" />
            </div>
            <div>
              <div className="text-lg font-bold text-slate-900 dark:text-white">{fullName}</div>
              <div className="mt-1 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-semibold ring-1 ${roleBadge.className}`}>
                  {role === 'HR_ADMIN' ? <Shield className="h-3 w-3" /> : role === 'MANAGER' ? <Briefcase className="h-3 w-3" /> : <User className="h-3 w-3" />}
                  {roleBadge.label}
                </span>
                <span>{employeeId}</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
            aria-label="Close profile panel"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-6 py-5">
          <section className="rounded-2xl border border-slate-200 bg-slate-50/80 p-4 dark:border-slate-800 dark:bg-slate-900/80">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
                <User className="h-4 w-4 text-indigo-600" />
                Profile
              </div>
              <button
                type="button"
                onClick={() => {
                  setAvatarPickerOpen((open) => !open);
                  setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
                }}
                className="inline-flex items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300 dark:hover:bg-indigo-900/80"
              >
                <Camera className="h-3.5 w-3.5" />
                Change Avatar
              </button>
            </div>

            <div className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center gap-4">
                <AvatarDisplay profile={profile} name={fullName} size="xl" className="border-0 shadow-md shadow-indigo-500/10" />
                <div>
                  <p className="text-lg font-bold text-slate-900 dark:text-white">{fullName}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">{employeeId}</p>
                  <div className="mt-2 flex items-center gap-2 text-[10px] font-medium text-slate-500 dark:text-slate-400">
                    <Building2 className="h-3 w-3" />
                    <span>{department !== 'N/A' ? department : 'Department unavailable'}</span>
                  </div>
                </div>
              </div>
              <div className="rounded-xl bg-slate-100 px-3 py-2 text-right dark:bg-slate-800">
                <p className="text-[10px] uppercase tracking-wide text-slate-500 dark:text-slate-400">Role</p>
                <p className="mt-1 text-sm font-semibold text-slate-800 dark:text-slate-200">{roleBadge.label}</p>
              </div>
            </div>

            {avatarPickerOpen && (
              <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900/80">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <div className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Select Avatar</div>
                  <button
                    type="button"
                    onClick={() => {
                      setAvatarPickerOpen(false);
                      setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
                      setAvatarError('');
                    }}
                    className="text-xs font-semibold text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  >
                    Close
                  </button>
                </div>

                <div className="grid grid-cols-4 gap-3">
                  {AVATAR_IDS.map((avatarIdValue) => {
                    const isSelected = selectedAvatarId === avatarIdValue;
                    return (
                      <button
                        key={avatarIdValue}
                        type="button"
                        onClick={() => setSelectedAvatarId(avatarIdValue)}
                        className={`relative flex items-center justify-center rounded-2xl border p-2 transition ${isSelected ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200 dark:border-indigo-400 dark:bg-indigo-950/40 dark:ring-indigo-900' : 'border-slate-200 bg-white hover:border-indigo-200 dark:border-slate-700 dark:bg-slate-900'}`}
                        aria-label={`Select ${avatarIdValue}`}
                        title={avatarIdValue}
                      >
                        <AvatarDisplay avatarId={avatarIdValue} name={fullName} size="lg" className="border-0" />
                        {isSelected && (
                          <span className="absolute right-1 top-1 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
                            <Check className="h-3.5 w-3.5" />
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>

                {avatarError && (
                  <div className="mt-3 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300">
                    {avatarError}
                  </div>
                )}

                <div className="mt-4 flex justify-end gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setAvatarPickerOpen(false);
                      setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
                      setAvatarError('');
                    }}
                    className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveAvatar}
                    disabled={savingAvatar}
                    className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {savingAvatar ? 'Saving...' : 'Save Avatar'}
                  </button>
                </div>
              </div>
            )}
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
              <User className="h-4 w-4 text-indigo-600" />
              Personal Information
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {personalDetails.map((item) => (
                <div key={item.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                  <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{item.label}</div>
                  <div className="mt-1 break-words text-sm font-semibold text-slate-900 dark:text-white">{item.value}</div>
                </div>
              ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
              <Briefcase className="h-4 w-4 text-indigo-600" />
              Work Information
            </div>
            <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
              {workDetails
                .filter(([, value]) => value && value !== 'N/A')
                .map(([label, value]) => (
                  <div key={label} className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                    <div className="text-[10px] font-bold uppercase tracking-wide text-slate-500 dark:text-slate-400">{label}</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{value}</div>
                  </div>
                ))}
            </div>
          </section>

          <section className="rounded-2xl border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center gap-2 text-sm font-bold text-slate-800 dark:text-slate-100">
              <Shield className="h-4 w-4 text-indigo-600" />
              Security & Account
            </div>
            <div className="space-y-3">
              <button
                type="button"
                onClick={() => {
                  onClose();
                  if (onRequestChangePassword) onRequestChangePassword();
                }}
                className="flex w-full items-center justify-between rounded-xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-left text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300 dark:hover:bg-indigo-900/70"
              >
                <span className="flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Change Password
                </span>
                <ChevronRight className="h-4 w-4" />
              </button>

              <button
                type="button"
                onClick={() => {
                  onClose();
                  if (onLogout) onLogout();
                }}
                className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-white px-4 py-3 text-left text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-200 dark:hover:bg-slate-800"
              >
                <span className="flex items-center gap-2">
                  <LogOut className="h-4 w-4" />
                  Logout
                </span>
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </section>
        </div>

        <div className="border-t border-slate-200 bg-slate-50/70 px-6 py-4 dark:border-slate-800 dark:bg-slate-900/70">
          <div className="flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span>Secure profile access</span>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-1 font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              Active
            </span>
          </div>
        </div>
      </aside>
    </div>
  );
}
