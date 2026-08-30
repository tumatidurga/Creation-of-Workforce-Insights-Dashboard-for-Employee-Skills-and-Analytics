import React, { useMemo, useState } from 'react';
import {
  ArrowRight,
  CalendarDays,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock3,
  FileText,
  Leaf,
  MessageSquare,
  Plus,
  Sparkles,
  TrendingUp,
  User,
  X,
  XCircle,
} from 'lucide-react';

function normalizeDateKey(value) {
  if (!value) return null;

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;

  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');

  return `${year}-${month}-${day}`;
}

function parseLocalDate(value) {
  if (!value) return null;
  const raw = String(value).trim();
  if (!raw || raw === 'N/A' || raw === 'NA') return null;

  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [year, month, day] = raw.split('-').map(Number);
    const localDate = new Date(year, month - 1, day);
    if (!Number.isNaN(localDate.getTime())) return localDate;
  }

  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
}

function formatDateLabel(value, fallback = 'N/A') {
  const parsed = parseLocalDate(value);
  if (!parsed) return fallback;

  return new Intl.DateTimeFormat('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(parsed);
}

function formatRelativeDate(value) {
  const parsed = parseLocalDate(value);
  if (!parsed) return 'Recently';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
  const diffDays = Math.round((today.getTime() - target.getTime()) / 86400000);

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short' }).format(parsed);
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).format(parsed);
}

function getLeaveDurationDays(startValue, endValue) {
  const start = parseLocalDate(startValue);
  const end = parseLocalDate(endValue);
  if (!start || !end) return 1;

  const diff = end.getTime() - start.getTime();
  const diffDays = Math.round(diff / 86400000);
  return Math.max(1, diffDays + 1);
}

function getStatusTone(status) {
  const text = String(status || '').toLowerCase();
  if (['approved', 'active', 'present'].includes(text)) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300';
  if (['pending', 'in review', 'requested'].includes(text)) return 'bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300';
  if (['rejected', 'denied', 'cancelled', 'inactive'].includes(text)) return 'bg-rose-100 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300';
  return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-200';
}

export const LeaveManagement = ({
  employees = [],
  selectedEmployeeId,
  onSelectEmployee,
  leaves = [],
  leaveBalance,
  leaveLoading = false,
  leaveError = null,
  onApplyLeave,
  onApproveLeave,
  onRejectLeave,
  userRole,
  currentEmpId,
  focusedRequestId = null,
}) => {
  const [selectedTab, setSelectedTab] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [leaveTypeFilter, setLeaveTypeFilter] = useState('ALL');
  const [departmentFilter, setDepartmentFilter] = useState('ALL');
  const [expandedLeaveId, setExpandedLeaveId] = useState(null);
  const [commentInput, setCommentInput] = useState({});
  const [calendarMonth, setCalendarMonth] = useState(() => {
    const today = new Date();
    return new Date(today.getFullYear(), today.getMonth(), 1);
  });
  const [selectedCalendarDate, setSelectedCalendarDate] = useState(() => {
    const today = new Date();
    return new Date(today.getFullYear(), today.getMonth(), today.getDate());
  });

  React.useEffect(() => {
    if (!focusedRequestId) return;
    // The focusedRequestId may be either the canonical id or a legacy requestId label.
    // Resolve to the canonical id (entry.id) when possible so approval/rejection
    // always operate on the backend's canonical identifier.
    if (Array.isArray(leaves)) {
      const match = leaves.find((entry) => {
        const canonical = entry?.id || entry?._id || entry?.Id || null;
        const label = entry?.requestId || entry?.RequestID || entry?.RequestId || null;
        return (canonical && String(canonical) === String(focusedRequestId)) || (label && String(label) === String(focusedRequestId));
      });
      if (match) {
        setExpandedLeaveId(match.id || match._id || focusedRequestId);
        return;
      }
    }
    // Fallback: use the provided value directly
    setExpandedLeaveId(focusedRequestId);
  }, [focusedRequestId, leaves]);
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [applicantName, setApplicantName] = useState('');
  const [department, setDepartment] = useState('');
  const [leaveType, setLeaveType] = useState('Casual Leave');
  const [startDate, setStartDate] = useState(() => {
    const today = new Date();
    const localDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 7);
    return normalizeDateKey(localDate) || '';
  });
  const [endDate, setEndDate] = useState(() => {
    const today = new Date();
    const localDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 10);
    return normalizeDateKey(localDate) || '';
  });
  const [reason, setReason] = useState('');
  const [formError, setFormError] = useState('');

  const isEmployeeRole = String(userRole || '').toUpperCase() === 'EMPLOYEE';
  const effectiveEmployeeId = isEmployeeRole
    ? (currentEmpId || selectedEmployeeId || selectedEmployee?.empId || selectedEmployee?.EmpID || selectedEmployee?.EmpId || employees?.[0]?.empId || null)
    : selectedEmployeeId || '';

  const selectedEmployee = (employees || []).find((emp) => {
    const candidateId = emp?.empId || emp?.EmpID || emp?.EmpId || emp?.employeeId;
    const targetId = isEmployeeRole ? effectiveEmployeeId : selectedEmployeeId;
    return candidateId && targetId && String(candidateId) === String(targetId);
  }) || null;

  React.useEffect(() => {
    if (selectedEmployee) {
      const derivedName = `${selectedEmployee.firstName || ''} ${selectedEmployee.lastName || ''}`.trim() || selectedEmployee.empId || '';
      setApplicantName(derivedName);
      setDepartment(selectedEmployee.department || '');
    } else if (isEmployeeRole && effectiveEmployeeId) {
      const fallbackEmployee = (employees || []).find((emp) => {
        const candidateId = emp?.empId || emp?.EmpID || emp?.EmpId || emp?.employeeId;
        return candidateId && String(candidateId) === String(effectiveEmployeeId);
      });
      if (fallbackEmployee) {
        setApplicantName(`${fallbackEmployee.firstName || ''} ${fallbackEmployee.lastName || ''}`.trim() || fallbackEmployee.empId || '');
        setDepartment(fallbackEmployee.department || '');
    } else if (currentEmpId) {
      setApplicantName('Current employee');
      setDepartment('');
    }
  }
  }, [selectedEmployeeId, selectedEmployee, employees, effectiveEmployeeId, isEmployeeRole, currentEmpId]);

  const safeLeaveBalance = useMemo(() => ({
    casualLeave: { total: 0, used: 0, remaining: 0, ...(leaveBalance?.casualLeave || {}) },
    sickLeave: { total: 0, used: 0, remaining: 0, ...(leaveBalance?.sickLeave || {}) },
    earnedLeave: { total: 0, used: 0, remaining: 0, ...(leaveBalance?.earnedLeave || {}) },
    parentalLeave: { total: 0, used: 0, remaining: 0, ...(leaveBalance?.parentalLeave || {}) },
  }), [leaveBalance]);

  const employeeOnlyLeaves = useMemo(() => {
    if (!Array.isArray(leaves)) return [];
    if (userRole === 'HR_ADMIN' || userRole === 'MANAGER') return leaves;
    const targetEmployeeId = currentEmpId || selectedEmployeeId || effectiveEmployeeId;
    if (!targetEmployeeId) return leaves;
    return leaves.filter((entry) => {
      const candidateId = entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId || null;
      return candidateId && String(candidateId) === String(targetEmployeeId);
    });
  }, [leaves, selectedEmployeeId, userRole, currentEmpId, effectiveEmployeeId]);

  const normalizedLeaves = useMemo(() => {
    return [...employeeOnlyLeaves]
      .map((entry) => ({
        ...entry,
        statusLabel: String(entry?.status || entry?.Status || 'Pending').trim() || 'Pending',
        leaveTypeLabel: entry?.leaveType || entry?.LeaveType || entry?.type || 'Casual Leave',
        startDateValue: entry?.startDate || entry?.StartDate || entry?.fromDate || entry?.FromDate || '',
        endDateValue: entry?.endDate || entry?.EndDate || entry?.toDate || entry?.ToDate || '',
        submittedOn: entry?.appliedOn || entry?.AppliedOn || entry?.submittedOn || entry?.SubmittedOn || '',
        requestId: entry?.requestId || entry?.RequestID || entry?.RequestId || null,
      }))
      .sort((a, b) => {
        const left = a?.endDateValue || a?.startDateValue || '';
        const right = b?.endDateValue || b?.startDateValue || '';
        return String(right).localeCompare(String(left));
      });
  }, [employeeOnlyLeaves]);

  const pendingLeaves = normalizedLeaves.filter((entry) => ['pending', 'requested'].includes(String(entry.statusLabel).toLowerCase()));
  const approvedLeaves = normalizedLeaves.filter((entry) => String(entry.statusLabel).toLowerCase() === 'approved');
  const rejectedLeaves = normalizedLeaves.filter((entry) => ['rejected', 'denied'].includes(String(entry.statusLabel).toLowerCase()));

  const leaveTypeOptions = useMemo(() => {
    const types = new Set();
    normalizedLeaves.forEach((entry) => {
      const value = String(entry?.leaveTypeLabel || '').trim();
      if (value) types.add(value);
    });
    return ['ALL', ...Array.from(types).sort()];
  }, [normalizedLeaves]);

  const departmentOptions = useMemo(() => {
    const departments = new Set();
    normalizedLeaves.forEach((entry) => {
      const value = String(entry?.department || '').trim();
      if (value) departments.add(value);
    });
    return ['ALL', ...Array.from(departments).sort()];
  }, [normalizedLeaves]);

  const statusFilteredLeaves = useMemo(() => {
    let base = normalizedLeaves;
    switch (selectedTab) {
      case 'PENDING':
        base = pendingLeaves;
        break;
      case 'APPROVED':
        base = approvedLeaves;
        break;
      case 'REJECTED':
        base = rejectedLeaves;
        break;
      default:
        base = normalizedLeaves;
        break;
    }

    const query = searchQuery.trim().toLowerCase();
    const typeFilter = leaveTypeFilter === 'ALL' ? 'all' : leaveTypeFilter.toLowerCase();
    const departmentFilterValue = departmentFilter === 'ALL' ? 'all' : departmentFilter.toLowerCase();

    return base.filter((entry) => {
      const employeeText = `${entry?.empName || ''} ${entry?.empId || ''}`.toLowerCase();
      const reasonText = `${entry?.reason || ''}`.toLowerCase();
      const departmentText = `${entry?.department || ''}`.toLowerCase();
      const matchesSearch = !query || employeeText.includes(query) || reasonText.includes(query) || entry?.leaveTypeLabel?.toLowerCase().includes(query);
      const matchesType = typeFilter === 'all' || String(entry?.leaveTypeLabel || '').toLowerCase() === typeFilter;
      const matchesDepartment = departmentFilterValue === 'all' || departmentText === departmentFilterValue;
      return matchesSearch && matchesType && matchesDepartment;
    });
  }, [normalizedLeaves, pendingLeaves, approvedLeaves, rejectedLeaves, selectedTab, searchQuery, leaveTypeFilter, departmentFilter]);

  const upcomingApprovedLeave = useMemo(() => {
    const now = new Date();
    return approvedLeaves
      .filter((entry) => {
        const endDate = parseLocalDate(entry.endDateValue || entry.startDateValue);
        return endDate && endDate.getTime() >= now.getTime();
      })
      .sort((a, b) => {
        const left = parseLocalDate(a.startDateValue) || new Date();
        const right = parseLocalDate(b.startDateValue) || new Date();
        return left.getTime() - right.getTime();
      })
      .slice(0, 1);
  }, [approvedLeaves]);

  const totalRequestedDays = useMemo(() => {
    return normalizedLeaves.reduce((sum, entry) => {
      const days = getLeaveDurationDays(entry.startDateValue, entry.endDateValue);
      return sum + days;
    }, 0);
  }, [normalizedLeaves]);

  const toggleExpand = (id) => {
    setExpandedLeaveId((prev) => (prev === id ? null : id));
  };

  const handleCommentChange = (id, text) => {
    setCommentInput((prev) => ({ ...prev, [id]: text }));
  };

  const handleLeaveSubmit = (event) => {
    event.preventDefault();

    if (!reason.trim()) {
      setFormError('Please include a valid reason for the leave request.');
      return;
    }

    const finalEmployeeId = isEmployeeRole ? effectiveEmployeeId : selectedEmployeeId;
    if (!finalEmployeeId) {
      setFormError(isEmployeeRole ? 'Unable to determine the current employee for this request.' : 'Please select an employee before submitting a leave request.');
      return;
    }

    if (!startDate || !endDate) {
      setFormError('Please select both a start and end date.');
      return;
    }

    const start = parseLocalDate(startDate);
    const end = parseLocalDate(endDate);
    if (!start || !end) {
      setFormError('Please choose valid leave dates.');
      return;
    }

    if (end.getTime() < start.getTime()) {
      setFormError('End date cannot be earlier than the start date.');
      return;
    }

    const duration = getLeaveDurationDays(startDate, endDate);
    const newLeave = {
      id: null,
      empName: applicantName || `${selectedEmployee?.firstName || ''} ${selectedEmployee?.lastName || ''}`.trim() || finalEmployeeId,
      empId: finalEmployeeId,
      department: department || selectedEmployee?.department || '',
      leaveType,
      startDate,
      endDate,
      days: duration,
      reason,
      status: 'Pending',
      appliedOn: normalizeDateKey(new Date()) || new Date().toISOString().slice(0, 10),
    };

    if (onApplyLeave) {
      onApplyLeave(newLeave);
    }

    setShowApplyModal(false);
    setReason('');
    setFormError('');
    setSelectedTab('PENDING');
  };

  const leaveBalanceCards = [
    {
      key: 'casualLeave',
      title: 'Casual Leave',
      color: 'indigo',
      remaining: safeLeaveBalance.casualLeave.remaining || 0,
      total: safeLeaveBalance.casualLeave.total || 0,
      used: safeLeaveBalance.casualLeave.used || 0,
    },
    {
      key: 'sickLeave',
      title: 'Sick Leave',
      color: 'emerald',
      remaining: safeLeaveBalance.sickLeave.remaining || 0,
      total: safeLeaveBalance.sickLeave.total || 0,
      used: safeLeaveBalance.sickLeave.used || 0,
    },
    {
      key: 'earnedLeave',
      title: 'Earned Leave',
      color: 'violet',
      remaining: safeLeaveBalance.earnedLeave.remaining || 0,
      total: safeLeaveBalance.earnedLeave.total || 0,
      used: safeLeaveBalance.earnedLeave.used || 0,
    },
    {
      key: 'parentalLeave',
      title: 'Parental Leave',
      color: 'sky',
      remaining: safeLeaveBalance.parentalLeave.remaining || 0,
      total: safeLeaveBalance.parentalLeave.total || 0,
      used: safeLeaveBalance.parentalLeave.used || 0,
    },
  ].filter((card) => (card.total || card.remaining || card.used) > 0);

  const approvedThisMonth = useMemo(() => {
    const monthKey = new Date().toISOString().slice(0, 7);
    return approvedLeaves.filter((entry) => {
      const start = parseLocalDate(entry.startDateValue || entry.endDateValue);
      if (!start) return false;
      return new Date(start).toISOString().slice(0, 7) === monthKey;
    }).reduce((sum, entry) => sum + getLeaveDurationDays(entry.startDateValue, entry.endDateValue), 0);
  }, [approvedLeaves]);

  const activeLeaveEmployees = useMemo(() => {
    const todayKey = normalizeDateKey(new Date());
    const ids = new Set();
    normalizedLeaves.forEach((entry) => {
      const start = normalizeDateKey(entry.startDateValue);
      const end = normalizeDateKey(entry.endDateValue);
      const status = String(entry.statusLabel || '').toLowerCase();
      if ((status === 'approved' || status === 'pending') && start && end) {
        const current = new Date(`${todayKey}T00:00:00`);
        const startDate = new Date(`${start}T00:00:00`);
        const endDate = new Date(`${end}T00:00:00`);
        if (current >= startDate && current <= endDate) {
          ids.add(String(entry.empId || entry.empName || 'unknown'));
        }
      }
    });
    return ids.size;
  }, [normalizedLeaves]);

  const leaveTypeDistribution = useMemo(() => {
    const counts = new Map();
    normalizedLeaves.forEach((entry) => {
      const type = String(entry?.leaveTypeLabel || 'Other').trim() || 'Other';
      counts.set(type, (counts.get(type) || 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [normalizedLeaves]);

  const leaveCalendarDays = useMemo(() => {
    const monthStart = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
    const startOffset = (monthStart.getDay() + 6) % 7;
    const startDate = new Date(monthStart);
    startDate.setDate(monthStart.getDate() - startOffset);

    const cells = [];
    for (let index = 0; index < 42; index += 1) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + index);
      const key = normalizeDateKey(date);
      const holidayMatch = normalizedLeaves.filter((entry) => {
        const start = normalizeDateKey(entry.startDateValue);
        const end = normalizeDateKey(entry.endDateValue);
        if (!start || !end) return false;
        const candidate = new Date(`${key}T00:00:00`);
        const startDateObj = new Date(`${start}T00:00:00`);
        const endDateObj = new Date(`${end}T00:00:00`);
        return candidate >= startDateObj && candidate <= endDateObj;
      });
      cells.push({
        date,
        key,
        isCurrentMonth: date.getMonth() === calendarMonth.getMonth(),
        isSelected: key === normalizeDateKey(selectedCalendarDate),
        leaveEntries: holidayMatch,
      });
    }
    return cells;
  }, [calendarMonth, normalizedLeaves, selectedCalendarDate]);

  const selectedDayLeaves = useMemo(() => {
    const key = normalizeDateKey(selectedCalendarDate);
    if (!key) return [];
    return normalizedLeaves.filter((entry) => {
      const start = normalizeDateKey(entry.startDateValue);
      const end = normalizeDateKey(entry.endDateValue);
      if (!start || !end) return false;
      const current = new Date(`${key}T00:00:00`);
      const startDate = new Date(`${start}T00:00:00`);
      const endDate = new Date(`${end}T00:00:00`);
      return current >= startDate && current <= endDate;
    });
  }, [normalizedLeaves, selectedCalendarDate]);

  const isEmployeeView = userRole === 'EMPLOYEE';

  if (!isEmployeeView) {
    return (
      <div className="space-y-6">
        {leaveError && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
            Error loading leave data: {leaveError}
          </div>
        )}
        {leaveLoading && (
          <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300">
            Loading leave data...
          </div>
        )}

        <div className="rounded-[28px] border border-indigo-100 bg-gradient-to-br from-indigo-950 via-violet-950 to-slate-950 p-6 text-white shadow-[0_30px_80px_-28px_rgba(67,56,202,0.75)]">
          <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-100">
                <Leaf className="h-3.5 w-3.5" />
                HR leave operations
              </div>
              <h2 className="mt-3 text-3xl font-black tracking-tight text-white">Leave Management</h2>
              <p className="mt-2 max-w-2xl text-sm text-indigo-100/80">
                Manage employee leave requests, workforce availability, and approvals with a premium operational view.
              </p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/15 px-3 py-2 text-xs font-bold text-emerald-200 ring-1 ring-emerald-400/20">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Live queue
            </div>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {[
            { label: 'Pending requests', value: pendingLeaves.length, accent: 'bg-amber-50 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300', icon: Clock3 },
            { label: 'Approved this month', value: approvedThisMonth, accent: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300', icon: CheckCircle2 },
            { label: 'Employees on leave', value: activeLeaveEmployees, accent: 'bg-violet-50 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300', icon: User },
            { label: 'Upcoming leaves', value: approvedLeaves.filter((entry) => parseLocalDate(entry.startDateValue) && parseLocalDate(entry.startDateValue).getTime() >= Date.now()).length, accent: 'bg-sky-50 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300', icon: CalendarDays },
            { label: 'Rejected', value: rejectedLeaves.length, accent: 'bg-rose-50 text-rose-700 dark:bg-rose-950/60 dark:text-rose-300', icon: XCircle },
          ].map((metric) => (
            <div key={metric.label} className="rounded-[26px] border border-slate-200 bg-white p-4 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] transition duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${metric.accent}`}>
                  <metric.icon className="h-4 w-4" />
                </span>
                <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Live</span>
              </div>
              <div className="mt-4 text-3xl font-black text-slate-900 dark:text-white">{metric.value}</div>
              <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">{metric.label}</div>
            </div>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Distribution</div>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Leave types</h3>
              </div>
              <span className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">Real data</span>
            </div>
            <div className="space-y-3">
              {leaveTypeDistribution.length > 0 ? leaveTypeDistribution.map((item) => (
                <div key={item.label}>
                  <div className="mb-1 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                    <span>{item.label}</span>
                    <span className="font-semibold">{item.value}</span>
                  </div>
                  <div className="h-2.5 rounded-full bg-slate-100 dark:bg-slate-800">
                    <div className="h-2.5 rounded-full bg-gradient-to-r from-indigo-500 to-violet-400" style={{ width: `${Math.max(10, (item.value / Math.max(...leaveTypeDistribution.map((point) => point.value), 1)) * 100)}%` }} />
                  </div>
                </div>
              )) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">Insufficient leave type data is available to generate a chart.</div>
              )}
            </div>
          </div>

          <div className="rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Planning</div>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Leave calendar</h3>
              </div>
              <CalendarDays className="h-5 w-5 text-violet-600 dark:text-violet-300" />
            </div>
            <div className="space-y-3">
              {normalizedLeaves.length > 0 ? (
                <>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Next approved leave</div>
                    <div className="mt-2 text-sm font-bold text-slate-900 dark:text-white">{upcomingApprovedLeave[0]?.leaveTypeLabel || 'No approved leave upcoming'}</div>
                    <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                      {upcomingApprovedLeave[0] ? `${formatDateLabel(upcomingApprovedLeave[0].startDateValue, 'N/A')} → ${formatDateLabel(upcomingApprovedLeave[0].endDateValue, 'N/A')}` : 'No future approved dates were found.'}
                    </div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.14em] text-slate-500">Pending approvals</div>
                    <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{pendingLeaves.length}</div>
                  </div>
                </>
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">No leave records are currently available for planning.</div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-4 rounded-[28px] border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 xl:grid-cols-[1.25fr_0.75fr]">
          <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="mb-3 flex items-center justify-between gap-2">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Leave planner</div>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Availability calendar</h3>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1))} className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:border-indigo-200 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"> <ChevronUp className="h-4 w-4 rotate-[-90deg]" /> </button>
                <button type="button" onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1))} className="rounded-xl border border-slate-200 bg-white p-2 text-slate-600 hover:border-indigo-200 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"> <ChevronUp className="h-4 w-4 rotate-[90deg]" /> </button>
              </div>
            </div>
            <div className="mb-3 flex items-center justify-between rounded-2xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-800 dark:bg-slate-900">
              <div className="text-sm font-bold text-slate-900 dark:text-white">{new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(calendarMonth)}</div>
              <button type="button" onClick={() => { const now = new Date(); setCalendarMonth(new Date(now.getFullYear(), now.getMonth(), 1)); setSelectedCalendarDate(now); }} className="rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-600 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">Today</button>
            </div>
            <div className="grid grid-cols-7 gap-2 text-center text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
              {['Mon','Tue','Wed','Thu','Fri','Sat','Sun'].map((day) => <div key={day} className="py-1">{day}</div>)}
            </div>
            <div className="mt-2 grid grid-cols-7 gap-2">
              {leaveCalendarDays.map(({ date, key, isCurrentMonth, isSelected, leaveEntries }) => (
                <button key={key} type="button" onClick={() => setSelectedCalendarDate(date)} className={['relative min-h-[80px] rounded-2xl border p-2 text-left transition', isCurrentMonth ? 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900' : 'border-slate-100 bg-slate-100 text-slate-400 dark:border-slate-800 dark:bg-slate-950/40 dark:text-slate-500', isSelected ? 'border-indigo-300 bg-indigo-50 shadow-sm dark:border-indigo-700 dark:bg-indigo-950/40' : 'hover:border-indigo-200 hover:bg-indigo-50/60 dark:hover:border-indigo-800 dark:hover:bg-slate-800/80'].join(' ')}>
                  <div className="flex items-center justify-between">
                    <span className={['text-sm font-bold', isSelected ? 'text-indigo-700 dark:text-indigo-300' : 'text-slate-700 dark:text-slate-200'].join(' ')}>{date.getDate()}</span>
                    {leaveEntries.length > 0 ? <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" title={`${leaveEntries.length} leave entries`} /> : null}
                  </div>
                  {leaveEntries.slice(0, 2).map((entry, idx) => (
                    <div key={`${entry.id || entry.empId || key}-${idx}`} className="mt-1 truncate rounded-full bg-indigo-50 px-1 py-0.5 text-[8px] font-bold uppercase tracking-[0.08em] text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300">{entry.leaveTypeLabel || 'Leave'}</div>
                  ))}
                  {leaveEntries.length > 2 ? <div className="mt-1 text-[8px] font-bold text-slate-500 dark:text-slate-400">+{leaveEntries.length - 2} more</div> : null}
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-[22px] border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="mb-3 flex items-center justify-between">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Selected day</div>
                <h3 className="mt-1 text-base font-black text-slate-900 dark:text-white">{formatDateLabel(normalizeDateKey(selectedCalendarDate), 'N/A')}</h3>
              </div>
              <CalendarDays className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
            </div>
            {selectedDayLeaves.length > 0 ? (
              <div className="space-y-2">
                {selectedDayLeaves.slice(0, 4).map((entry, index) => (
                  <div key={`${entry.id || entry.empId || 'day'}-${index}`} className="rounded-2xl border border-slate-200 bg-white p-2.5 dark:border-slate-800 dark:bg-slate-900">
                    <div className="text-xs font-bold text-slate-900 dark:text-white">{entry.empName || entry.empId || 'Employee'}</div>
                    <div className="mt-1 text-[11px] text-slate-600 dark:text-slate-300">{entry.leaveTypeLabel} • {entry.statusLabel}</div>
                  </div>
                ))}
                {selectedDayLeaves.length > 4 ? <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">+{selectedDayLeaves.length - 4} additional employees</div> : null}
              </div>
            ) : (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                No planned leave is scheduled for this date.
              </div>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-3 rounded-[28px] border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 md:grid-cols-[1fr_1fr_1fr_1fr]">
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Search</div>
            <input value={searchQuery} onChange={(event) => setSearchQuery(event.target.value)} placeholder="Name, ID or reason" className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white" />
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Status</div>
            <select value={selectedTab} onChange={(event) => setSelectedTab(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white">
              {['ALL','PENDING','APPROVED','REJECTED'].map((tab) => <option key={tab} value={tab}>{tab === 'ALL' ? 'All' : tab}</option>)}
            </select>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Type</div>
            <select value={leaveTypeFilter} onChange={(event) => setLeaveTypeFilter(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white">
              {leaveTypeOptions.map((option) => <option key={option} value={option}>{option === 'ALL' ? 'All types' : option}</option>)}
            </select>
          </div>
          <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
            <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500">Department</div>
            <select value={departmentFilter} onChange={(event) => setDepartmentFilter(event.target.value)} className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white">
              {departmentOptions.map((option) => <option key={option} value={option}>{option === 'ALL' ? 'All departments' : option}</option>)}
            </select>
          </div>
        </div>

        <div className="mt-4 flex border-b border-slate-200 dark:border-slate-800">
          {['PENDING', 'APPROVED', 'REJECTED', 'ALL'].map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setSelectedTab(tab)}
              className={`border-b-2 px-4 py-3 text-xs font-bold transition ${
                selectedTab === tab ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400' : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              {tab === 'ALL' ? 'All' : tab === 'PENDING' ? 'Pending' : tab === 'APPROVED' ? 'Approved' : 'Rejected'}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
          {statusFilteredLeaves.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-white p-12 text-center text-slate-500 dark:border-slate-800 dark:bg-slate-900">
              <CalendarDays className="mx-auto mb-2 h-8 w-8 text-slate-400" />
              <p className="text-xs font-semibold">No leave applications found in this section.</p>
            </div>
          ) : statusFilteredLeaves.map((leave, index) => {
            const rowKey = leave.id || `${leave.empId || 'unknown'}-${index}`;
            const isExpanded = expandedLeaveId === rowKey;
            const displayName = leave.empName || leave.empId || 'Employee';
            const initials = displayName.split(' ').filter(Boolean).map((segment) => segment[0]).join('').slice(0, 2) || 'E';
            const leaveStatus = String(leave.statusLabel || leave.status || 'Pending');

            return (
              <div key={rowKey} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-indigo-300 dark:border-slate-800 dark:bg-slate-900">
                <div onClick={() => toggleExpand(rowKey)} className="flex cursor-pointer items-start justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-100 text-sm font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                      {initials}
                    </div>
                    <div>
                      <h3 className="flex items-center gap-2 text-sm font-bold text-slate-900 dark:text-white">
                        {displayName}
                        <span className="text-[10px] font-semibold text-indigo-600 dark:text-indigo-400">({leave.empId || 'N/A'})</span>
                      </h3>
                      <div className="text-xs text-slate-500">{leave.department || 'N/A'}</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${getStatusTone(leaveStatus)}`}>
                      {leaveStatus}
                    </span>
                    {isExpanded ? <ChevronUp className="h-4 w-4 text-slate-400" /> : <ChevronDown className="h-4 w-4 text-slate-400" />}
                  </div>
                </div>

                <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                  <div>
                    <span className="mb-1 block text-[10px] text-slate-400">Leave category</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">{leave.leaveTypeLabel}</span>
                  </div>
                  <div>
                    <span className="mb-1 block text-[10px] text-slate-400">Duration</span>
                    <span className="font-semibold text-slate-800 dark:text-slate-200">
                      {formatDateLabel(leave.startDateValue, 'N/A')} → {formatDateLabel(leave.endDateValue, 'N/A')} ({getLeaveDurationDays(leave.startDateValue, leave.endDateValue)} days)
                    </span>
                  </div>
                </div>

                {isExpanded && (
                  <div className="mt-4 space-y-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                    <div className="rounded-xl bg-slate-50 p-3 text-xs dark:bg-slate-800/60">
                      <span className="mb-1 block font-bold text-slate-700 dark:text-slate-300">Reason for leave:</span>
                      <p className="leading-relaxed text-slate-600 dark:text-slate-300">{leave.reason || 'No reason provided.'}</p>
                    </div>
                    <div className="flex justify-between text-[11px] text-slate-400">
                      <span>Submitted: {leave.submittedOn ? formatDateLabel(leave.submittedOn) : 'N/A'}</span>
                      <span>Request ID: {leave.id || 'N/A'}</span>
                    </div>

                    {leaveStatus.toLowerCase() === 'pending' && (
                      <div className="space-y-2 pt-2">
                        <div className="relative">
                          <MessageSquare className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-400" />
                          <input
                            type="text"
                            placeholder="Add approval remarks..."
                            value={commentInput[rowKey] || ''}
                            onChange={(event) => handleCommentChange(rowKey, event.target.value)}
                            className="w-full rounded-lg border border-slate-200 bg-white py-1.5 pl-8 pr-3 text-xs text-slate-900 focus:border-indigo-500 focus:outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                          />
                        </div>
                        <div className="flex items-center gap-2 pt-1">
                          <button
                            type="button"
                            onClick={() => onApproveLeave(leave.id, commentInput[rowKey] || 'Approved by HR Manager')}
                            className="flex-1 rounded-lg bg-emerald-600 py-2 text-xs font-bold text-white hover:bg-emerald-700"
                          >
                            <span className="inline-flex items-center gap-1.5"><CheckCircle2 className="h-4 w-4" /> Approve</span>
                          </button>
                          <button
                            type="button"
                            onClick={() => onRejectLeave(leave.id, commentInput[rowKey] || 'Rejected due to coverage constraints')}
                            className="flex-1 rounded-lg bg-rose-600 py-2 text-xs font-bold text-white hover:bg-rose-700"
                          >
                            <span className="inline-flex items-center gap-1.5"><XCircle className="h-4 w-4" /> Reject</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 pb-4">
      {leaveError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          Error loading leave data: {leaveError}
        </div>
      )}
      {leaveLoading && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-950/40 dark:text-slate-300">
          Loading leave data...
        </div>
      )}

      <div className="relative overflow-hidden rounded-[30px] border border-indigo-100 bg-gradient-to-br from-indigo-950 via-violet-950 to-slate-950 p-6 text-white shadow-[0_30px_80px_-28px_rgba(67,56,202,0.7)]">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(255,255,255,0.12),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(56,189,248,0.17),_transparent_30%)]" />
        <div className="relative z-10 flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
          <div className="max-w-2xl">
            <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-200">Leave center</div>
            <h2 className="mt-2 text-3xl font-black tracking-tight text-white">Manage your time away</h2>
            <p className="mt-3 text-sm text-indigo-100/80">Plan your time away and keep track of every leave request with a premium, data-driven self-service view.</p>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setShowApplyModal(true)}
              className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-indigo-900 shadow-lg shadow-indigo-950/20 transition hover:-translate-y-0.5"
            >
              <Plus className="h-4 w-4" />
              Apply for Leave
            </button>
          </div>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {leaveBalanceCards.length > 0 ? leaveBalanceCards.map((card) => {
          const colorMap = {
            indigo: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300',
            emerald: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300',
            violet: 'bg-violet-100 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300',
            sky: 'bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300',
          };

          return (
            <div key={card.key} className="rounded-[26px] border border-slate-200 bg-white p-4 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] transition duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900 dark:hover:border-indigo-700">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Available</div>
                  <div className="mt-2 text-3xl font-black text-slate-900 dark:text-white">{card.remaining}</div>
                </div>
                <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${colorMap[card.color] || 'bg-slate-100 text-slate-700'}`}>
                  <Leaf className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-3 text-sm font-semibold text-slate-700 dark:text-slate-200">{card.title}</div>
              <div className="mt-2 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                <span>Used {card.used}</span>
                <span>Total {card.total}</span>
              </div>
              <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800">
                <div
                  className={`h-full ${card.color === 'indigo' ? 'bg-indigo-600' : card.color === 'emerald' ? 'bg-emerald-600' : card.color === 'violet' ? 'bg-violet-600' : 'bg-sky-600'}`}
                  style={{ width: `${card.total ? Math.max(0, Math.min(100, (card.remaining / card.total) * 100)) : 0}%` }}
                />
              </div>
            </div>
          );
        }) : (
          <div className="rounded-[26px] border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
            No leave balance data available for this employee.
          </div>
        )}
      </div>

      <div className="grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Requests</div>
              <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Your leave history</h3>
            </div>
            <div className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-600 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-300">
              {normalizedLeaves.length} total
            </div>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {['ALL', 'PENDING', 'APPROVED', 'REJECTED'].map((tab) => (
              <button
                key={tab}
                type="button"
                onClick={() => setSelectedTab(tab)}
                className={`rounded-xl px-3 py-2 text-xs font-bold transition ${
                  selectedTab === tab
                    ? 'bg-indigo-600 text-white shadow-[0_16px_28px_-18px_rgba(99,102,241,0.85)]'
                    : 'border border-slate-200 bg-white text-slate-600 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-950/30 dark:text-slate-300 dark:hover:border-indigo-700 dark:hover:text-indigo-300'
                }`}
              >
                {tab === 'ALL' ? 'All' : tab === 'PENDING' ? 'Pending' : tab === 'APPROVED' ? 'Approved' : 'Rejected'}
              </button>
            ))}
          </div>

          <div className="mt-5 space-y-3">
            {statusFilteredLeaves.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-950/50">
                <div className="text-sm font-bold text-slate-900 dark:text-white">No leave requests yet</div>
                <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">Your submitted leave applications will appear here.</div>
              </div>
            ) : statusFilteredLeaves.map((leave, index) => {
              const rowKey = leave.id || `${leave.empId || 'employee'}-${index}`;
              const isExpanded = expandedLeaveId === rowKey;
              const status = String(leave.statusLabel || leave.status || 'Pending');

              return (
                <button
                  key={rowKey}
                  type="button"
                  onClick={() => toggleExpand(rowKey)}
                  className="group block w-full rounded-[22px] border border-slate-200 bg-slate-50 p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-[0_18px_35px_-28px_rgba(79,70,229,0.8)] dark:border-slate-700 dark:bg-slate-950/50 dark:hover:border-indigo-700 dark:hover:bg-slate-900"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${getStatusTone(status)}`}>{status}</span>
                        <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{leave.leaveTypeLabel}</span>
                      </div>
                      <div className="mt-2 text-base font-bold text-slate-900 dark:text-white">{formatDateLabel(leave.startDateValue, 'N/A')} to {formatDateLabel(leave.endDateValue, 'N/A')}</div>
                      <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{getLeaveDurationDays(leave.startDateValue, leave.endDateValue)} days • Submitted {formatRelativeDate(leave.submittedOn || leave.startDateValue || leave.endDateValue)}</div>
                    </div>
                    <div className="flex items-center gap-2 text-slate-400 group-hover:text-indigo-600 dark:text-slate-500 dark:group-hover:text-indigo-300">
                      <ArrowRight className="h-4 w-4" />
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-3 text-xs dark:border-slate-700 dark:bg-slate-900">
                      <div className="grid gap-2 sm:grid-cols-2">
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Leave type</div>
                          <div className="mt-1 font-semibold text-slate-900 dark:text-white">{leave.leaveTypeLabel}</div>
                        </div>
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Duration</div>
                          <div className="mt-1 font-semibold text-slate-900 dark:text-white">{getLeaveDurationDays(leave.startDateValue, leave.endDateValue)} day(s)</div>
                        </div>
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Start date</div>
                          <div className="mt-1 font-semibold text-slate-900 dark:text-white">{formatDateLabel(leave.startDateValue, 'N/A')}</div>
                        </div>
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">End date</div>
                          <div className="mt-1 font-semibold text-slate-900 dark:text-white">{formatDateLabel(leave.endDateValue, 'N/A')}</div>
                        </div>
                      </div>

                      <div className="mt-4 rounded-xl bg-slate-50 p-3 dark:bg-slate-950/40">
                        <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Reason</div>
                        <div className="mt-1 text-sm leading-relaxed text-slate-700 dark:text-slate-300">{leave.reason || 'No reason provided.'}</div>
                      </div>

                      <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
                        <span>Requested on {leave.submittedOn ? formatDateLabel(leave.submittedOn) : 'N/A'}</span>
                        <span>Request ID: {leave.id || 'N/A'}</span>
                      </div>
                    </div>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Overview</div>
                <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Smart insights</h3>
              </div>
              <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
            </div>

            <div className="mt-5 space-y-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/50">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Pending requests</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{pendingLeaves.length}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/50">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Approved days</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{approvedLeaves.reduce((sum, entry) => sum + getLeaveDurationDays(entry.startDateValue, entry.endDateValue), 0)}</div>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/50">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Total requested</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{totalRequestedDays}</div>
              </div>
            </div>
          </div>

          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Upcoming</div>
                <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Time off</h3>
              </div>
              <CalendarDays className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
            </div>

            <div className="mt-5">
              {upcomingApprovedLeave.length > 0 ? upcomingApprovedLeave.map((entry) => (
                <div key={entry.id || 'upcoming'} className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3 dark:border-indigo-800 dark:bg-indigo-950/50">
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">Next approved leave</div>
                  <div className="mt-2 text-sm font-black text-slate-900 dark:text-white">{entry.leaveTypeLabel || 'Leave'}</div>
                  <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">
                    {formatDateLabel(entry.startDateValue, 'N/A')} to {formatDateLabel(entry.endDateValue, 'N/A')} • {getLeaveDurationDays(entry.startDateValue, entry.endDateValue)} days
                  </div>
                </div>
              )) : (
                <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-950/50 dark:text-slate-300">
                  No upcoming approved leave
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {showApplyModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-[30px] border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Leave request</div>
                <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Apply for leave</h3>
              </div>
              <button type="button" onClick={() => { setShowApplyModal(false); setFormError(''); }} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={handleLeaveSubmit} className="mt-5 space-y-4">
              {formError && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
                  {formError}
                </div>
              )}

              {!isEmployeeRole && (
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Employee</label>
                  <select
                    value={selectedEmployeeId || ''}
                    onChange={(event) => onSelectEmployee?.(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                    required
                  >
                    <option value="">Select employee</option>
                    {(employees || []).map((employee) => {
                      const label = `${employee.firstName || ''} ${employee.lastName || ''}`.trim() || employee.empId || 'Employee';
                      return (
                        <option key={employee.empId || label} value={employee.empId || ''}>
                          {label} ({employee.empId || 'N/A'})
                        </option>
                      );
                    })}
                  </select>
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Leave type</label>
                  <select
                    value={leaveType}
                    onChange={(event) => setLeaveType(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                  >
                    <option value="Casual Leave">Casual Leave</option>
                    <option value="Sick Leave">Sick Leave</option>
                    <option value="Privilege Leave">Privilege Leave</option>
                    <option value="Parental Leave">Parental Leave</option>
                  </select>
                </div>

                {isEmployeeRole && (
                  <div className="flex items-end">
                    <div className="w-full rounded-xl border border-indigo-100 bg-indigo-50 p-3 dark:border-indigo-900/60 dark:bg-indigo-950/30">
                      <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">Employee</div>
                      <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{effectiveEmployeeId || 'Current employee'}</div>
                    </div>
                  </div>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Start date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(event) => setStartDate(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                    required
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">End date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(event) => setEndDate(event.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                    required
                  />
                </div>
              </div>

              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/40">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">Duration</span>
                  <span className="text-sm font-bold text-slate-900 dark:text-white">
                    {startDate && endDate && startDate <= endDate
                      ? `${getLeaveDurationDays(startDate, endDate)} day(s)`
                      : 'Select dates'}
                  </span>
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Reason</label>
                <textarea
                  rows={4}
                  value={reason}
                  onChange={(event) => setReason(event.target.value)}
                  placeholder="Share a concise reason for the leave request..."
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                  required
                />
              </div>

              <div className="flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button type="button" onClick={() => { setShowApplyModal(false); setFormError(''); }} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
                  Cancel
                </button>
                <button type="submit" className="rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-[0_16px_28px_-18px_rgba(99,102,241,0.85)] hover:bg-indigo-700">
                  Submit request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
