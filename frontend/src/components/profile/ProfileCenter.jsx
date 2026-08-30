import React, { useEffect, useMemo, useState } from 'react';
import {
  Activity,
  ArrowRight,
  BadgeCheck,
  Briefcase,
  Building2,
  CalendarDays,
  Camera,
  Check,
  ChevronRight,
  Clock3,
  Edit3,
  Fingerprint,
  KeyRound,
  Lock,
  LogOut,
  Mail,
  MapPin,
  Phone,
  Shield,
  Sparkles,
  User,
  Users,
  X,
} from 'lucide-react';

import { api } from '../../services/api';
import { AvatarDisplay } from '../common/AvatarDisplay';
import { AVATAR_IDS, DEFAULT_AVATAR_ID } from '../../utils/avatars';

function normalizeRole(value) {
  if (!value) return 'EMPLOYEE';
  const role = String(value).toUpperCase();
  if (role.includes('HR') || role.includes('ADMIN')) return 'HR_ADMIN';
  if (role.includes('MANAGER')) return 'MANAGER';
  return 'EMPLOYEE';
}

function formatDate(value) {
  if (!value) return 'N/A';
  const text = String(value).trim();
  if (!text || text === 'N/A') return 'N/A';
  const date = new Date(text);
  if (Number.isNaN(date.getTime())) return text;
  return new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric' }).format(date);
}

function getEmployeeRecord(employees, empId) {
  if (!Array.isArray(employees) || !empId) return null;
  return employees.find((employee) => {
    const candidateId = employee?.empId || employee?.EmpID || employee?.EmpId || employee?.empID;
    return candidateId === empId;
  }) || null;
}

function getStatusTone(status) {
  if (!status) return 'bg-slate-100 text-slate-700';
  const text = String(status).toLowerCase();
  if (['active', 'approved', 'present', 'online', 'clear'].includes(text)) return 'bg-emerald-100 text-emerald-700';
  if (['pending', 'warning', 'in review'].includes(text)) return 'bg-amber-100 text-amber-700';
  if (['rejected', 'inactive', 'absent'].includes(text)) return 'bg-rose-100 text-rose-700';
  return 'bg-slate-100 text-slate-700';
}

function normalizeText(value) {
  if (value === null || value === undefined) return '';
  return String(value).trim();
}

function formatDisplayValue(value, fallback = 'Not Provided') {
  const text = normalizeText(value);
  return text || fallback;
}

function buildEditForm(profile, currentEmpName) {
  return {
    name: normalizeText(profile?.name || currentEmpName),
    phone: normalizeText(profile?.phone),
    personalEmail: normalizeText(profile?.personalEmail),
    dateOfBirth: normalizeText(profile?.dateOfBirth),
    gender: normalizeText(profile?.gender),
    address: normalizeText(profile?.address),
    city: normalizeText(profile?.city),
    state: normalizeText(profile?.state),
    country: normalizeText(profile?.country),
    postalCode: normalizeText(profile?.postalCode),
    emergencyContactName: normalizeText(profile?.emergencyContactName),
    emergencyContactRelationship: normalizeText(profile?.emergencyContactRelationship),
    emergencyContactPhone: normalizeText(profile?.emergencyContactPhone),
    skills: Array.isArray(profile?.skills) ? profile.skills.join(', ') : normalizeText(profile?.skills),
    education: normalizeText(profile?.education),
    qualifications: normalizeText(profile?.qualifications),
    mfaEnabled: Boolean(profile?.mfaEnabled),
  };
}

const tabOptions = [
  { id: 'overview', label: 'Overview' },
  { id: 'personal', label: 'Personal Information' },
  { id: 'work', label: 'Work & Employment' },
  { id: 'security', label: 'Security' },
  { id: 'activity', label: 'Activity' },
];

const profileEditTabs = [
  { id: 'personal', label: 'Personal' },
  { id: 'contact', label: 'Contact' },
  { id: 'employment', label: 'Employment' },
  { id: 'professional', label: 'Professional' },
  { id: 'security', label: 'Security' },
  { id: 'review', label: 'Review' },
];

export function ProfileCenter({
  profile,
  userRole,
  currentEmpName,
  currentEmpId,
  employees = [],
  attendance = [],
  leaves = [],
  shifts = [],
  payroll = [],
  notifications = [],
  leaveBalance = null,
  onLogout,
  onRequestChangePassword,
  onProfileUpdated,
}) {
  const [activeTab, setActiveTab] = useState('overview');
  const [showEdit, setShowEdit] = useState(false);
  const [editStep, setEditStep] = useState('personal');
  const [editForm, setEditForm] = useState(() => buildEditForm(profile, currentEmpName));
  const [saveState, setSaveState] = useState({ loading: false, error: '', success: '' });
  const [avatarPickerOpen, setAvatarPickerOpen] = useState(false);
  const [selectedAvatarId, setSelectedAvatarId] = useState(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
  const [avatarSaving, setAvatarSaving] = useState(false);
  const [avatarError, setAvatarError] = useState('');

  useEffect(() => {
    setEditForm(buildEditForm(profile, currentEmpName));
    setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
  }, [profile, currentEmpName]);

  const role = normalizeRole(userRole || profile?.role || 'EMPLOYEE');
  const currentEmployee = useMemo(() => getEmployeeRecord(employees, currentEmpId), [employees, currentEmpId]);

  const employeeRecord = currentEmployee || {};
  const fullName = profile?.name || currentEmpName || employeeRecord.EmployeeName || 'User';
  const workEmail = profile?.email || employeeRecord.Email || 'N/A';
  const phoneNumber = profile?.phone || employeeRecord.Phone || profile?.Phone || 'Not provided';
  const department = profile?.department || employeeRecord.Department || 'N/A';
  const designation = profile?.jobRole || employeeRecord.JobRole || employeeRecord.designation || employeeRecord.Designation || 'N/A';
  const roleLabel = role === 'HR_ADMIN' ? 'HR Admin' : role === 'MANAGER' ? 'Manager' : 'Employee';
  const profileCompletionFields = [
    { key: 'name', label: 'Full name', value: normalizeText(profile?.name || currentEmpName) },
    { key: 'phone', label: 'Phone number', value: normalizeText(profile?.phone) },
    { key: 'personalEmail', label: 'Personal email', value: normalizeText(profile?.personalEmail) },
    { key: 'dateOfBirth', label: 'Date of birth', value: normalizeText(profile?.dateOfBirth) },
    { key: 'gender', label: 'Gender', value: normalizeText(profile?.gender) },
    { key: 'address', label: 'Address', value: normalizeText(profile?.address) },
    { key: 'city', label: 'City', value: normalizeText(profile?.city) },
    { key: 'state', label: 'State', value: normalizeText(profile?.state) },
    { key: 'country', label: 'Country', value: normalizeText(profile?.country) },
    { key: 'postalCode', label: 'Postal code', value: normalizeText(profile?.postalCode) },
    { key: 'emergencyContactName', label: 'Emergency contact', value: normalizeText(profile?.emergencyContactName) },
    { key: 'emergencyContactRelationship', label: 'Relationship', value: normalizeText(profile?.emergencyContactRelationship) },
    { key: 'emergencyContactPhone', label: 'Emergency phone', value: normalizeText(profile?.emergencyContactPhone) },
    { key: 'skills', label: 'Skills', value: Array.isArray(profile?.skills) ? profile.skills.join(', ') : normalizeText(profile?.skills) },
    { key: 'education', label: 'Education', value: normalizeText(profile?.education) },
    { key: 'qualifications', label: 'Qualifications', value: normalizeText(profile?.qualifications) },
  ];
  const completedProfileFields = profileCompletionFields.filter(({ value }) => value.length > 0).length;
  const profileCompletionPercent = profileCompletionFields.length > 0 ? Math.round((completedProfileFields / profileCompletionFields.length) * 100) : 0;
  const remainingProfileFields = profileCompletionFields.length - completedProfileFields;
  const employmentStatus = employeeRecord.EmploymentStatus || employeeRecord.status || profile?.employmentStatus || 'Active';
  const joiningDate = employeeRecord.JoiningDate || employeeRecord.joiningDate || 'N/A';
  const location = employeeRecord.Location || employeeRecord.location || 'N/A';
  const managerName = employeeRecord.Manager || employeeRecord.managerName || profile?.managerName || profile?.manager || 'N/A';
  const shiftInfo = Array.isArray(shifts) && shifts.length > 0 ? shifts.find((entry) => {
    const emp = entry?.EmpID || entry?.empId || entry?.employeeId;
    return emp === currentEmpId;
  }) : null;

  const attendanceRate = useMemo(() => {
    if (!attendance || attendance.length === 0) return 0;
    const presentCount = attendance.filter((entry) => {
      const status = String(entry?.AttendanceStatus || entry?.status || '').toLowerCase();
      return status === 'present' || status === 'late' || status === 'approved';
    }).length;
    return Math.round((presentCount / attendance.length) * 100);
  }, [attendance]);

  const presentDays = useMemo(() => {
    if (!attendance || attendance.length === 0) return 0;
    return attendance.filter((entry) => {
      const status = String(entry?.AttendanceStatus || entry?.status || '').toLowerCase();
      return status === 'present' || status === 'late';
    }).length;
  }, [attendance]);

  const leaveBalanceSummary = useMemo(() => {
    if (!leaveBalance) return { casual: 0, sick: 0, earned: 0 };
    return {
      casual: leaveBalance.casualLeave?.remaining ?? leaveBalance.casualLeave?.total ?? 0,
      sick: leaveBalance.sickLeave?.remaining ?? leaveBalance.sickLeave?.total ?? 0,
      earned: leaveBalance.earnedLeave?.remaining ?? leaveBalance.earnedLeave?.total ?? 0,
    };
  }, [leaveBalance]);

  const pendingApprovals = useMemo(() => {
    const pendingLeaves = (leaves || []).filter((entry) => {
      const status = String(entry?.Status || entry?.status || '').toLowerCase();
      return status === 'pending' || status === 'requested';
    }).length;
    const pendingShifts = (shifts || []).filter((entry) => {
      const status = String(entry?.ShiftSwapStatus || entry?.status || '').toLowerCase();
      return status === 'pending';
    }).length;
    return pendingLeaves + pendingShifts;
  }, [leaves, shifts]);

  const totalWorkforce = employees.length;
  const activeUsers = employees.filter((employee) => {
    const status = String(employee?.EmploymentStatus || employee?.status || '').toLowerCase();
    return status === 'active' || !status || status === 'working';
  }).length;

  const recentActivity = useMemo(() => {
    const items = [];
    (attendance || []).slice(0, 3).forEach((entry) => {
      items.push({
        type: 'attendance',
        title: 'Attendance update',
        detail: `${entry?.Date || entry?.date || 'Date'} • ${entry?.AttendanceStatus || entry?.status || 'Updated'}`,
        timestamp: entry?.Date || entry?.date || '',
      });
    });
    (leaves || []).slice(0, 3).forEach((entry) => {
      items.push({
        type: 'leave',
        title: 'Leave request',
        detail: `${entry?.LeaveType || entry?.leaveType || 'Leave'} • ${entry?.Status || entry?.status || 'Updated'}`,
        timestamp: entry?.StartDate || entry?.startDate || '',
      });
    });
    (payroll || []).slice(0, 2).forEach((entry) => {
      items.push({
        type: 'payroll',
        title: 'Payroll record',
        detail: `${entry?.PayrollMonth || entry?.month || 'Payroll'} • Net ${entry?.NetSalary ?? entry?.netPay ?? 'N/A'}`,
        timestamp: entry?.PayrollMonth || entry?.month || '',
      });
    });
    return items
      .sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''))
      .slice(0, 5);
  }, [attendance, leaves, payroll]);

  const overviewCards = useMemo(() => {
    if (role === 'HR_ADMIN') {
      return [
        { label: 'Total Workforce', value: totalWorkforce || 'N/A', hint: 'Active employee records', icon: Users },
        { label: 'Active Users', value: activeUsers || 'N/A', hint: 'Verified system access', icon: BadgeCheck },
        { label: 'Pending Approvals', value: pendingApprovals || 0, hint: 'Reviews across HR operations', icon: Briefcase },
        { label: 'Payroll Status', value: payroll.length ? 'Ready' : 'N/A', hint: 'Latest payroll data', icon: Sparkles },
      ];
    }
    if (role === 'MANAGER') {
      return [
        { label: 'Team Members', value: totalWorkforce || 'N/A', hint: 'Direct workforce view', icon: Users },
        { label: 'Pending Approvals', value: pendingApprovals || 0, hint: 'Requests waiting for review', icon: Briefcase },
        { label: 'Team Attendance', value: `${attendanceRate}%`, hint: 'Coverage across recent activity', icon: Activity },
        { label: 'Leave Requests', value: (leaves || []).filter((entry) => String(entry?.Status || entry?.status || '').toLowerCase() === 'pending').length || 0, hint: 'Current approval queue', icon: CalendarDays },
      ];
    }
    return [
      { label: 'Attendance %', value: `${attendanceRate}%`, hint: 'Recent engagement', icon: Activity },
      { label: 'Present Days', value: presentDays, hint: 'Recorded in recent history', icon: Check },
      { label: 'Leave Balance', value: `${leaveBalanceSummary.casual} / ${leaveBalanceSummary.sick} / ${leaveBalanceSummary.earned}`, hint: 'Casual / Sick / Earned', icon: CalendarDays },
      { label: 'Current Shift', value: shiftInfo ? String(shiftInfo.ShiftName || shiftInfo.shiftName || 'Assigned') : 'N/A', hint: shiftInfo ? `${shiftInfo.ShiftStart || shiftInfo.shiftStart || 'N/A'} - ${shiftInfo.ShiftEnd || shiftInfo.shiftEnd || 'N/A'}` : 'No upcoming shift', icon: Clock3 },
    ];
  }, [role, totalWorkforce, activeUsers, pendingApprovals, payroll, attendanceRate, presentDays, leaveBalanceSummary, shifts, leaves, shiftInfo]);

  const saveProfile = async () => {
    setSaveState({ loading: true, error: '', success: '' });

    const phonePattern = /^\+?[0-9\s\-()]{7,20}$/;
    const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    try {
      if (editForm.phone && !phonePattern.test(editForm.phone)) {
        throw new Error('Please enter a valid phone number.');
      }
      if (editForm.personalEmail && !emailPattern.test(editForm.personalEmail)) {
        throw new Error('Please enter a valid personal email address.');
      }
      if (editForm.emergencyContactPhone && !phonePattern.test(editForm.emergencyContactPhone)) {
        throw new Error('Please enter a valid emergency contact phone number.');
      }
      if (editForm.dateOfBirth) {
        const dateValue = new Date(editForm.dateOfBirth);
        if (Number.isNaN(dateValue.getTime()) || dateValue > new Date()) {
          throw new Error('Date of birth must be a valid date in the past.');
        }
      }

      const payload = {
        name: normalizeText(editForm.name) || fullName,
        phone: normalizeText(editForm.phone) || null,
        personalEmail: normalizeText(editForm.personalEmail) || null,
        dateOfBirth: normalizeText(editForm.dateOfBirth) || null,
        gender: normalizeText(editForm.gender) || null,
        address: normalizeText(editForm.address) || null,
        city: normalizeText(editForm.city) || null,
        state: normalizeText(editForm.state) || null,
        country: normalizeText(editForm.country) || null,
        postalCode: normalizeText(editForm.postalCode) || null,
        emergencyContactName: normalizeText(editForm.emergencyContactName) || null,
        emergencyContactRelationship: normalizeText(editForm.emergencyContactRelationship) || null,
        emergencyContactPhone: normalizeText(editForm.emergencyContactPhone) || null,
        skills: normalizeText(editForm.skills)
          ? Array.from(new Set(editForm.skills.split(',').map((entry) => entry.trim()).filter(Boolean)))
          : [],
        education: normalizeText(editForm.education) || null,
        qualifications: normalizeText(editForm.qualifications) || null,
        mfaEnabled: Boolean(editForm.mfaEnabled),
      };

      const updated = await api.updateProfile(payload);
      if (typeof onProfileUpdated === 'function') {
        onProfileUpdated(updated || payload);
      }
      setSaveState({ loading: false, error: '', success: 'Profile updated successfully.' });
      setShowEdit(false);
    } catch (error) {
      const message = error?.response?.data?.detail || error.message || 'Unable to update profile.';
      setSaveState({ loading: false, error: message, success: '' });
    }
  };

  const saveAvatar = async () => {
    if (!selectedAvatarId) return;
    setAvatarSaving(true);
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
      setAvatarSaving(false);
    }
  };

  const secureStatus = profile?.mfaEnabled ? 'MFA enabled' : 'MFA not enabled';
  const accountStatus = employmentStatus || 'Active';

  return (
    <div className="space-y-6 pb-8">
      <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-950 shadow-xl shadow-indigo-950/10">
        <div className="border-b border-white/10 bg-white/5 p-6 backdrop-blur-sm md:p-8">
          <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex items-center gap-4 sm:gap-5">
              <div className="relative">
                <AvatarDisplay
                  profile={profile}
                  name={fullName}
                  size="xl"
                  className="border-2 border-white/20 bg-white/10 text-lg text-white shadow-xl shadow-indigo-500/20"
                />
                <button
                  type="button"
                  onClick={() => {
                    setSelectedAvatarId(profile?.avatarId || profile?.avatar || DEFAULT_AVATAR_ID);
                    setAvatarPickerOpen(true);
                  }}
                  className="absolute -bottom-1 -right-1 flex h-9 w-9 items-center justify-center rounded-full border border-white/20 bg-white text-slate-700 shadow-lg transition hover:scale-105"
                  aria-label="Change avatar"
                >
                  <Camera className="h-4 w-4" />
                </button>
              </div>

              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/15 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-300 ring-1 ring-emerald-400/40">Active</span>
                  <span className="inline-flex items-center gap-1 rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-200 ring-1 ring-white/10">{roleLabel}</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-white sm:text-3xl">{fullName}</h1>
                  <div className="mt-2 flex flex-wrap items-center gap-4 text-sm text-slate-300">
                    <span className="inline-flex items-center gap-2"><Fingerprint className="h-4 w-4 text-indigo-300" /> {currentEmpId || 'N/A'}</span>
                    <span className="inline-flex items-center gap-2"><Building2 className="h-4 w-4 text-indigo-300" /> {department !== 'N/A' ? department : 'Department unavailable'}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => {
                  setEditStep('personal');
                  setShowEdit(true);
                }}
                className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-100"
              >
                <Edit3 className="h-4 w-4" />
                Edit Profile
              </button>
              <button
                type="button"
                onClick={() => onRequestChangePassword && onRequestChangePassword()}
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                <KeyRound className="h-4 w-4" />
                Change Password
              </button>
              <button
                type="button"
                onClick={() => onLogout && onLogout()}
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-transparent px-4 py-2.5 text-sm font-semibold text-white transition hover:bg-white/10"
              >
                <LogOut className="h-4 w-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500 dark:text-slate-400">Profile completion</p>
            <div className="mt-2 flex items-baseline gap-3">
              <span className="text-2xl font-bold text-slate-900 dark:text-white">{profileCompletionPercent}%</span>
              <span className="text-sm text-slate-600 dark:text-slate-300">{remainingProfileFields === 0 ? 'Complete' : `${remainingProfileFields} details remaining`}</span>
            </div>
          </div>
          <button type="button" onClick={() => {
            setEditStep('personal');
            setShowEdit(true);
          }} className="inline-flex items-center gap-2 rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/40 dark:text-indigo-300">
            <Edit3 className="h-4 w-4" />
            {remainingProfileFields === 0 ? 'Review profile' : 'Complete profile'}
          </button>
        </div>
        <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
          <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-violet-500 to-purple-500 transition-all duration-300" style={{ width: `${profileCompletionPercent}%` }} />
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-1 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <nav className="flex flex-wrap gap-1">
          {tabOptions.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveTab(tab.id)}
              className={`rounded-xl px-4 py-2.5 text-sm font-semibold transition ${activeTab === tab.id ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white'}`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            {overviewCards.map(({ label, value, hint, icon: Icon }) => (
              <div key={label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
                <div className="mb-3 flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300">
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Live</span>
                </div>
                <div className="text-xl font-bold text-slate-900 dark:text-white">{value}</div>
                <div className="mt-1 text-sm font-medium text-slate-600 dark:text-slate-300">{label}</div>
                <div className="mt-2 text-[11px] text-slate-500 dark:text-slate-400">{hint}</div>
              </div>
            ))}
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.5fr_1fr]">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Summary</p>
                  <h2 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{role === 'HR_ADMIN' ? 'Workforce summary' : role === 'MANAGER' ? 'Team overview' : 'Personal overview'}</h2>
                </div>
                <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] ${getStatusTone(accountStatus)}`}>{accountStatus}</span>
              </div>

              <div className="space-y-4">
                {role === 'EMPLOYEE' ? (
                  <>
                    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Reporting manager</div>
                        <div className="mt-1 font-semibold text-slate-900 dark:text-white">{managerName !== 'N/A' ? managerName : 'Not available'}</div>
                      </div>
                      <User className="h-5 w-5 text-indigo-500" />
                    </div>
                    <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Current shift</div>
                        <div className="mt-1 font-semibold text-slate-900 dark:text-white">{shiftInfo ? `${shiftInfo.ShiftName || shiftInfo.shiftName || 'Assigned'} • ${shiftInfo.ShiftStart || shiftInfo.shiftStart || 'N/A'}-${shiftInfo.ShiftEnd || shiftInfo.shiftEnd || 'N/A'}` : 'N/A'}</div>
                      </div>
                      <Clock3 className="h-5 w-5 text-indigo-500" />
                    </div>
                  </>
                ) : (
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/50">
                    <div>
                      <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Current workforce status</div>
                      <div className="mt-1 font-semibold text-slate-900 dark:text-white">{activeUsers || 0} active users across {totalWorkforce || 0} records</div>
                    </div>
                    <Shield className="h-5 w-5 text-indigo-500" />
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Performance pulse</p>
                  <h2 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Profile health</h2>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 dark:bg-slate-950/50">
                  <span className="text-sm text-slate-600 dark:text-slate-300">Security</span>
                  <span className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-semibold text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">{secureStatus}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 dark:bg-slate-950/50">
                  <span className="text-sm text-slate-600 dark:text-slate-300">Role access</span>
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">{roleLabel}</span>
                </div>
                <div className="flex items-center justify-between rounded-xl bg-slate-50 p-3 dark:bg-slate-950/50">
                  <span className="text-sm text-slate-600 dark:text-slate-300">Latest payroll</span>
                  <span className="text-sm font-semibold text-slate-900 dark:text-white">{payroll.length ? 'Available' : 'Not found'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'personal' && (
        <div className="grid gap-6 xl:grid-cols-2">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
              <Mail className="h-4 w-4 text-indigo-600" />
              <h2 className="text-lg font-bold">Contact Information</h2>
            </div>
            <div className="space-y-3">
              <InfoRow label="Work email" value={workEmail} icon={<Mail className="h-4 w-4" />} />
              <InfoRow label="Personal email" value={profile?.personalEmail ? profile.personalEmail : 'Not provided'} icon={<Mail className="h-4 w-4" />} />
              <InfoRow label="Phone number" value={profile?.phone ? profile.phone : phoneNumber === 'Not provided' ? 'Not provided' : phoneNumber} icon={<Phone className="h-4 w-4" />} />
              <InfoRow label="Location" value={location} icon={<MapPin className="h-4 w-4" />} />
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
              <User className="h-4 w-4 text-indigo-600" />
              <h2 className="text-lg font-bold">Personal Details</h2>
            </div>
            <div className="space-y-3">
              <InfoRow label="Full name" value={fullName} icon={<User className="h-4 w-4" />} />
              <InfoRow label="Employee ID" value={currentEmpId || 'N/A'} icon={<Fingerprint className="h-4 w-4" />} />
              <InfoRow label="Gender" value={profile?.gender ? profile.gender : employeeRecord.Gender || employeeRecord.gender || 'Not provided'} icon={<BadgeCheck className="h-4 w-4" />} />
              <InfoRow label="Date of birth" value={profile?.dateOfBirth ? formatDate(profile.dateOfBirth) : formatDate(employeeRecord.DateOfBirth || employeeRecord.dateOfBirth || employeeRecord.DOB) === 'N/A' ? 'Not provided' : formatDate(employeeRecord.DateOfBirth || employeeRecord.dateOfBirth || employeeRecord.DOB)} icon={<CalendarDays className="h-4 w-4" />} />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'work' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-5 flex items-center gap-2 text-slate-900 dark:text-white">
            <Briefcase className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-bold">Work & Employment</h2>
          </div>

          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            <InfoRow label="Employee ID" value={currentEmpId || 'N/A'} icon={<Fingerprint className="h-4 w-4" />} />
            <InfoRow label="Department" value={department} icon={<Building2 className="h-4 w-4" />} />
            <InfoRow label="Designation" value={designation} icon={<Briefcase className="h-4 w-4" />} />
            <InfoRow label="Role" value={roleLabel} icon={<Shield className="h-4 w-4" />} />
            <InfoRow label="Joining date" value={formatDate(joiningDate)} icon={<CalendarDays className="h-4 w-4" />} />
            <InfoRow label="Employment type" value={employeeRecord.EmploymentType || employeeRecord.employmentType || 'N/A'} icon={<BadgeCheck className="h-4 w-4" />} />
            <InfoRow label="Reporting manager" value={managerName !== 'N/A' ? managerName : 'Not available'} icon={<User className="h-4 w-4" />} />
            <InfoRow label="Work location" value={location} icon={<MapPin className="h-4 w-4" />} />
            <InfoRow label="Current shift" value={shiftInfo ? `${shiftInfo.ShiftName || shiftInfo.shiftName || 'Assigned'} (${shiftInfo.ShiftStart || shiftInfo.shiftStart || 'N/A'} - ${shiftInfo.ShiftEnd || shiftInfo.shiftEnd || 'N/A'})` : 'N/A'} icon={<Clock3 className="h-4 w-4" />} />
          </div>
        </div>
      )}

      {activeTab === 'security' && (
        <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
              <Lock className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-bold">Security & Account</h2>
            </div>
            <div className="space-y-4">
              <button
                type="button"
                onClick={() => onRequestChangePassword && onRequestChangePassword()}
                className="flex w-full items-center justify-between rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3 text-left text-sm font-semibold text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-300"
              >
                <span className="inline-flex items-center gap-2"><KeyRound className="h-4 w-4" /> Change Password</span>
                <ChevronRight className="h-4 w-4" />
              </button>

              <div className="grid gap-3 md:grid-cols-2">
                <InfoRow label="Account status" value={accountStatus} icon={<BadgeCheck className="h-4 w-4" />} />
                <InfoRow label="Password state" value={secureStatus} icon={<Shield className="h-4 w-4" />} />
              </div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center gap-2 text-slate-900 dark:text-white">
              <Activity className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-bold">Session</h2>
            </div>
            <div className="space-y-3">
              <InfoRow label="Role" value={roleLabel} icon={<Shield className="h-4 w-4" />} />
              <InfoRow label="Last login" value={profile?.lastLogin ? formatDate(profile.lastLogin) : 'Not available'} icon={<Clock3 className="h-4 w-4" />} />
              <InfoRow label="MFA" value={profile?.mfaEnabled ? 'Enabled' : 'Disabled'} icon={<Lock className="h-4 w-4" />} />
            </div>
          </div>
        </div>
      )}

      {activeTab === 'activity' && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="mb-5 flex items-center justify-between gap-2">
            <div className="flex items-center gap-2 text-slate-900 dark:text-white">
              <Activity className="h-5 w-5 text-indigo-600" />
              <h2 className="text-lg font-bold">Recent activity</h2>
            </div>
            <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-600 dark:bg-slate-800 dark:text-slate-300">{recentActivity.length} items</span>
          </div>

          <div className="space-y-4">
            {recentActivity.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/30 dark:text-slate-400">No recent activity is available for this profile.</div>
            ) : recentActivity.map((item, index) => (
              <div key={`${item.title}-${index}`} className="flex gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/40">
                <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-100 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300">
                  {item.type === 'attendance' ? <Activity className="h-4 w-4" /> : item.type === 'leave' ? <CalendarDays className="h-4 w-4" /> : item.type === 'payroll' ? <Sparkles className="h-4 w-4" /> : <Shield className="h-4 w-4" />}
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-semibold text-slate-900 dark:text-white">{item.title}</p>
                    <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">{item.type}</span>
                  </div>
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">{item.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {showEdit && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-4xl rounded-[24px] border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Profile settings</p>
                <h3 className="mt-1 text-xl font-bold text-slate-900 dark:text-white">{remainingProfileFields === 0 ? 'Review profile' : 'Complete profile'}</h3>
              </div>
              <button type="button" onClick={() => setShowEdit(false)} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                <X className="h-4 w-4" />
              </button>
            </div>

            {saveState.error && <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">{saveState.error}</div>}
            {saveState.success && <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">{saveState.success}</div>}

            <div className="mb-5 flex flex-wrap gap-2">
              {profileEditTabs.map((tab) => (
                <button
                  key={tab.id}
                  type="button"
                  onClick={() => setEditStep(tab.id)}
                  className={`rounded-xl px-3 py-2 text-sm font-semibold transition ${editStep === tab.id ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20' : 'border border-slate-200 bg-slate-50 text-slate-600 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300'}`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            <div className="max-h-[70vh] space-y-5 overflow-y-auto pr-1">
              {editStep === 'personal' && (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                    <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Personal information</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field value={editForm.name} label="Full name" className="md:col-span-2" onChange={(value) => setEditForm((current) => ({ ...current, name: value }))} />
                      <Field value={editForm.dateOfBirth} label="Date of birth" type="date" onChange={(value) => setEditForm((current) => ({ ...current, dateOfBirth: value }))} />
                      <Field value={editForm.gender} label="Gender" onChange={(value) => setEditForm((current) => ({ ...current, gender: value }))} />
                    </div>
                  </div>
                </div>
              )}

              {editStep === 'contact' && (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                    <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Contact & address</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field value={editForm.phone} label="Phone number" onChange={(value) => setEditForm((current) => ({ ...current, phone: value }))} />
                      <Field value={editForm.personalEmail} label="Personal email" onChange={(value) => setEditForm((current) => ({ ...current, personalEmail: value }))} />
                      <Field value={editForm.address} label="Address" className="md:col-span-2" onChange={(value) => setEditForm((current) => ({ ...current, address: value }))} />
                      <Field value={editForm.city} label="City" onChange={(value) => setEditForm((current) => ({ ...current, city: value }))} />
                      <Field value={editForm.state} label="State" onChange={(value) => setEditForm((current) => ({ ...current, state: value }))} />
                      <Field value={editForm.country} label="Country" onChange={(value) => setEditForm((current) => ({ ...current, country: value }))} />
                      <Field value={editForm.postalCode} label="Postal code" onChange={(value) => setEditForm((current) => ({ ...current, postalCode: value }))} />
                    </div>
                  </div>

                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                    <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Emergency contact</p>
                    <div className="grid gap-3 md:grid-cols-2">
                      <Field value={editForm.emergencyContactName} label="Contact name" onChange={(value) => setEditForm((current) => ({ ...current, emergencyContactName: value }))} />
                      <Field value={editForm.emergencyContactRelationship} label="Relationship" onChange={(value) => setEditForm((current) => ({ ...current, emergencyContactRelationship: value }))} />
                      <Field value={editForm.emergencyContactPhone} label="Contact phone" className="md:col-span-2" onChange={(value) => setEditForm((current) => ({ ...current, emergencyContactPhone: value }))} />
                    </div>
                  </div>
                </div>
              )}

              {editStep === 'employment' && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                  <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Work & employment</p>
                  <div className="grid gap-3 md:grid-cols-2">
                    <InfoRow label="Employee ID" value={currentEmpId || 'N/A'} icon={<Fingerprint className="h-4 w-4" />} />
                    <InfoRow label="Department" value={department} icon={<Building2 className="h-4 w-4" />} />
                    <InfoRow label="Designation" value={designation} icon={<Briefcase className="h-4 w-4" />} />
                    <InfoRow label="Role" value={roleLabel} icon={<Shield className="h-4 w-4" />} />
                    <InfoRow label="Employment type" value={employeeRecord.EmploymentType || employeeRecord.employmentType || 'N/A'} icon={<BadgeCheck className="h-4 w-4" />} />
                    <InfoRow label="Joining date" value={formatDate(joiningDate)} icon={<CalendarDays className="h-4 w-4" />} />
                    <InfoRow label="Reporting manager" value={managerName !== 'N/A' ? managerName : 'Not available'} icon={<User className="h-4 w-4" />} />
                    <InfoRow label="Work location" value={location} icon={<MapPin className="h-4 w-4" />} />
                  </div>
                  <div className="mt-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-700 dark:border-amber-900 dark:bg-amber-950/20 dark:text-amber-300">
                    Organization-managed employment details are protected and not editable in this employee self-service flow.
                  </div>
                </div>
              )}

              {editStep === 'professional' && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                  <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Professional profile</p>
                  <div className="grid gap-3 md:grid-cols-2">
                    <Field value={editForm.skills} label="Skills" className="md:col-span-2" onChange={(value) => setEditForm((current) => ({ ...current, skills: value }))} />
                    <Field value={editForm.education} label="Education" onChange={(value) => setEditForm((current) => ({ ...current, education: value }))} />
                    <Field value={editForm.qualifications} label="Qualifications" onChange={(value) => setEditForm((current) => ({ ...current, qualifications: value }))} />
                  </div>
                </div>
              )}

              {editStep === 'security' && (
                <div className="space-y-4">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                    <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Security</p>
                    <div className="space-y-3">
                      <div className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
                        <div>
                          <div className="text-sm font-semibold text-slate-900 dark:text-white">Multi-factor authentication</div>
                          <div className="text-xs text-slate-500 dark:text-slate-400">Keep account access protected</div>
                        </div>
                        <button
                          type="button"
                          onClick={() => setEditForm((current) => ({ ...current, mfaEnabled: !current.mfaEnabled }))}
                          className={`relative h-7 w-12 rounded-full transition ${editForm.mfaEnabled ? 'bg-indigo-600' : 'bg-slate-200 dark:bg-slate-700'}`}
                        >
                          <span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition ${editForm.mfaEnabled ? 'left-6' : 'left-1'}`} />
                        </button>
                      </div>
                      <button type="button" onClick={() => onRequestChangePassword && onRequestChangePassword()} className="flex w-full items-center justify-between rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2.5 text-left text-sm font-semibold text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950/30 dark:text-indigo-300">
                        <span className="inline-flex items-center gap-2"><KeyRound className="h-4 w-4" /> Change password</span>
                        <ChevronRight className="h-4 w-4" />
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {editStep === 'review' && (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/40">
                  <p className="mb-3 text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Review & save</p>
                  <div className="space-y-3">
                    {profileCompletionFields.map((field) => (
                      <div key={field.key} className="flex items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                        <span className="text-sm text-slate-700 dark:text-slate-200">{field.label}</span>
                        <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-[0.14em] ${field.value ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300' : 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300'}`}>
                          {field.value ? 'Saved' : 'Missing'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="mt-6 flex items-center justify-between gap-3">
              <div className="text-xs font-medium text-slate-500 dark:text-slate-400">
                {completedProfileFields} of {profileCompletionFields.length} eligible fields completed
              </div>
              <div className="flex gap-3">
                {editStep !== 'personal' && (
                  <button type="button" onClick={() => setEditStep(profileEditTabs[Math.max(0, profileEditTabs.findIndex((tab) => tab.id === editStep) - 1)].id)} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">Back</button>
                )}
                {editStep !== 'review' ? (
                  <button type="button" onClick={() => setEditStep(profileEditTabs[Math.min(profileEditTabs.length - 1, profileEditTabs.findIndex((tab) => tab.id === editStep) + 1)].id)} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700">Next</button>
                ) : (
                  <button type="button" disabled={saveState.loading} onClick={saveProfile} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70">{saveState.loading ? 'Saving...' : 'Save changes'}</button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {avatarPickerOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/40 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-[24px] border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-5 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Appearance</p>
                <h3 className="mt-1 text-xl font-bold text-slate-900 dark:text-white">Choose avatar</h3>
              </div>
              <button type="button" onClick={() => setAvatarPickerOpen(false)} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              {AVATAR_IDS.map((avatarIdValue) => {
                const isSelected = selectedAvatarId === avatarIdValue;
                return (
                  <button
                    key={avatarIdValue}
                    type="button"
                    onClick={() => setSelectedAvatarId(avatarIdValue)}
                    className={`relative rounded-2xl border p-3 transition ${isSelected ? 'border-indigo-500 bg-indigo-50 ring-2 ring-indigo-200 dark:border-indigo-400 dark:bg-indigo-950/40 dark:ring-indigo-900' : 'border-slate-200 bg-slate-50 hover:border-indigo-200 dark:border-slate-700 dark:bg-slate-950/40'}`}
                  >
                    <div className="flex justify-center">
                      <AvatarDisplay avatarId={avatarIdValue} name={fullName} size="lg" className="border-0" />
                    </div>
                    {isSelected && (
                      <span className="absolute right-2 top-2 flex h-5 w-5 items-center justify-center rounded-full bg-indigo-600 text-white shadow-sm">
                        <Check className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {avatarError && <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">{avatarError}</div>}

            <div className="mt-6 flex justify-end gap-3">
              <button type="button" onClick={() => setAvatarPickerOpen(false)} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">Cancel</button>
              <button type="button" disabled={avatarSaving} onClick={saveAvatar} className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70">{avatarSaving ? 'Saving...' : 'Save avatar'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({ label, value, onChange, type = 'text', className = '' }) {
  return (
    <label className={`block ${className}`}>
      <span className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">{label}</span>
      <input
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-100 dark:focus:ring-indigo-900"
      />
    </label>
  );
}

function InfoRow({ label, value, icon }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40">
      <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-lg bg-white text-indigo-600 shadow-sm dark:bg-slate-900 dark:text-indigo-300">{icon}</div>
      <div className="min-w-0 flex-1">
        <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">{label}</p>
        <p className="mt-1 break-words text-sm font-semibold text-slate-900 dark:text-white">{value || 'N/A'}</p>
      </div>
    </div>
  );
}
