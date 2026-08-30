import React, { useMemo, useState } from 'react';
import { CalendarRange, Clock, CheckCircle2, XCircle, Plus, MessageSquare, AlertCircle, ArrowRight, Sparkles } from 'lucide-react';

function parseLocalDate(value) {
  if (!value && value !== 0) return null;
  const raw = String(value).trim();
  if (!raw || raw === 'N/A' || raw === 'NA') return null;

  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) {
    const [year, month, day] = raw.split('-').map(Number);
    const localDate = new Date(year, month - 1, day);
    if (!Number.isNaN(localDate.getTime())) return localDate;
  }

  const parsed = new Date(raw);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
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

function formatScheduleDate(value) {
  const parsed = parseLocalDate(value);
  if (!parsed) return 'TBD';

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const target = new Date(parsed.getFullYear(), parsed.getMonth(), parsed.getDate());
  const dayDiff = Math.round((target.getTime() - today.getTime()) / 86400000);

  if (dayDiff === 0) return 'Today';
  if (dayDiff === 1) return 'Tomorrow';
  if (dayDiff < 7) return new Intl.DateTimeFormat('en-US', { weekday: 'short', month: 'short', day: 'numeric' }).format(parsed);
  return new Intl.DateTimeFormat('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).format(parsed);
}

function normalizeShiftDate(value) {
  const parsed = parseLocalDate(value);
  if (!parsed) return null;
  const year = parsed.getFullYear();
  const month = String(parsed.getMonth() + 1).padStart(2, '0');
  const day = String(parsed.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getShiftStatusTone(status) {
  const text = String(status || '').toLowerCase();
  if (['approved', 'active'].includes(text)) return 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300';
  if (['pending', 'in review', 'submitted'].includes(text)) return 'bg-amber-100 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300';
  if (['rejected', 'denied', 'cancelled'].includes(text)) return 'bg-rose-100 text-rose-700 dark:bg-rose-950/50 dark:text-rose-300';
  return 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300';
}

function getShiftLabel(record) {
  return record?.requestedShift || record?.ShiftName || record?.shiftName || record?.shiftSlot || record?.ShiftSlot || 'Shift request';
}

function getShiftDate(record) {
  return record?.requestedDate || record?.ShiftDate || record?.shiftDate || record?.date || record?.Date || record?.assignedDate || '';
}

export const ShiftManagement = ({
  employees = [],
  selectedEmployeeId = '',
  onSelectEmployee,
  shifts,
  onRequestShift,
  onApproveShift,
  onRejectShift,
  userRole,
  currentEmpId = null,
  focusedRequestId = null,
}) => {
  const [showRequestModal, setShowRequestModal] = useState(false);
  const [selectedRequestTab, setSelectedRequestTab] = useState('ALL');
  const [requestedShift, setRequestedShift] = useState('Morning Shift (09:00 - 18:00)');
  const [requestedDate, setRequestedDate] = useState(() => {
    const today = new Date();
    const localDate = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 7);
    const year = localDate.getFullYear();
    const month = String(localDate.getMonth() + 1).padStart(2, '0');
    const day = String(localDate.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  });
  const [reason, setReason] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedRequestId, setExpandedRequestId] = useState(null);

  React.useEffect(() => {
    if (focusedRequestId) {
      setExpandedRequestId(focusedRequestId);
    }
  }, [focusedRequestId]);

  const isHrAdmin = userRole === 'HR_ADMIN';
  const isManager = userRole === 'MANAGER';
  const canManageTeam = isHrAdmin || isManager;
  const isEmployeeRole = String(userRole || '').toUpperCase() === 'EMPLOYEE';
  const effectiveEmployeeId = currentEmpId || selectedEmployeeId || '';
  const selectedEmployee = employees.find((employee) => {
    const employeeId = employee?.empId || employee?.EmpID || employee?.EmpId || employee?.employeeId;
    return employeeId && String(employeeId) === String(selectedEmployeeId || effectiveEmployeeId || '');
  }) || null;

  const employeeShiftView = useMemo(() => {
    if (!Array.isArray(shifts)) return [];
    if (canManageTeam) return shifts;

    const targetId = String(effectiveEmployeeId || selectedEmployeeId || '');
    return shifts.filter((shift) => {
      const shiftEmpId = shift?.empId || shift?.EmpID || shift?.EmpId || shift?.employeeId || null;
      return shiftEmpId && targetId && String(shiftEmpId) === targetId;
    });
  }, [canManageTeam, effectiveEmployeeId, selectedEmployeeId, shifts]);

  const handleSubmitRequest = async (e) => {
    e.preventDefault();

    const finalEmployeeId = effectiveEmployeeId || selectedEmployeeId;
    if (!finalEmployeeId) {
      alert(isEmployeeRole ? 'Unable to determine the current employee for this shift request.' : 'Please select an employee before submitting a shift request.');
      return;
    }

    if (!reason.trim()) return;

    const newReq = {
      empId: finalEmployeeId,
      requestedShift,
      requestedDate,
      reason: reason.trim(),
      status: 'Pending',
      appliedOn: normalizeShiftDate(new Date()) || new Date().toISOString().split('T')[0],
    };

    await onRequestShift(newReq);
    setShowRequestModal(false);
    setReason('');
  };

  const pendingRequests = employeeShiftView.filter((s) => String(s.status || s.Status || 'Pending').toLowerCase() === 'pending');
  const actionedRequests = employeeShiftView.filter((s) => String(s.status || s.Status || 'Pending').toLowerCase() !== 'pending');
  const requestTabs = ['ALL', 'PENDING', 'APPROVED', 'REJECTED'];
  const getReasonText = (req) => req?.reason || req?.employeeReason || req?.RequestReason || req?.requestReason || req?.Comments || req?.Remarks || 'No reason provided';

  const myShiftSchedule = useMemo(() => {
    const records = [...(Array.isArray(shifts) ? shifts : [])]
      .filter((entry) => {
        const targetId = String(effectiveEmployeeId || selectedEmployeeId || '');
        const shiftEmpId = entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId || null;
        return targetId && shiftEmpId && String(shiftEmpId) === targetId;
      })
      .map((entry) => ({
        ...entry,
        shiftLabel: getShiftLabel(entry),
        shiftDate: getShiftDate(entry),
        status: entry?.status || entry?.Status || 'Scheduled',
      }))
      .filter((entry) => entry.shiftDate)
      .sort((a, b) => {
        const left = parseLocalDate(a.shiftDate) || new Date();
        const right = parseLocalDate(b.shiftDate) || new Date();
        return left.getTime() - right.getTime();
      });

    return records;
  }, [effectiveEmployeeId, selectedEmployeeId, shifts]);

  const nextShift = useMemo(() => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    return myShiftSchedule.find((entry) => {
      const date = parseLocalDate(entry.shiftDate);
      return date && new Date(date.getFullYear(), date.getMonth(), date.getDate()) >= today;
    }) || myShiftSchedule[0] || null;
  }, [myShiftSchedule]);

  const employeeRequests = useMemo(() => {
    return [...employeeShiftView]
      .map((entry) => ({
        ...entry,
        requestStatus: String(entry?.status || entry?.Status || 'Pending'),
        requestDate: getShiftDate(entry),
        requestLabel: getShiftLabel(entry),
      }))
      .sort((a, b) => {
        const left = parseLocalDate(a.requestDate) || new Date(0);
        const right = parseLocalDate(b.requestDate) || new Date(0);
        return right.getTime() - left.getTime();
      });
  }, [employeeShiftView]);

  const filteredEmployeeRequests = useMemo(() => {
    let base = employeeRequests;

    switch (selectedRequestTab) {
      case 'PENDING':
        base = employeeRequests.filter((req) => String(req.requestStatus).toLowerCase() === 'pending');
        break;
      case 'APPROVED':
        base = employeeRequests.filter((req) => String(req.requestStatus).toLowerCase() === 'approved');
        break;
      case 'REJECTED':
        base = employeeRequests.filter((req) => String(req.requestStatus).toLowerCase() === 'rejected');
        break;
      default:
        base = employeeRequests;
        break;
    }

    if (!searchQuery.trim()) return base;
    const needle = searchQuery.toLowerCase();
    return base.filter((req) => {
      const haystack = [req.empName, req.department, req.requestedShift, req.requestLabel, req.reason, req.requestStatus].filter(Boolean).join(' ').toLowerCase();
      return haystack.includes(needle);
    });
  }, [employeeRequests, searchQuery, selectedRequestTab]);

  const overviewStats = [
    { label: 'Pending review', value: pendingRequests.length, tone: 'amber' },
    { label: 'Approved this cycle', value: employeeShiftView.filter((item) => String(item.status || '').toLowerCase() === 'approved').length, tone: 'emerald' },
    { label: 'Rejected', value: employeeShiftView.filter((item) => String(item.status || '').toLowerCase() === 'rejected').length, tone: 'rose' },
    { label: 'Upcoming shifts', value: myShiftSchedule.length, tone: 'indigo' },
  ];

  return (
    <div className="space-y-6">
      {!canManageTeam && (
        <div className="sr-only">Employee shift center</div>
      )}

      {canManageTeam && (
        <>
          <div className="rounded-3xl border border-indigo-200 bg-gradient-to-r from-slate-950 via-indigo-950 to-blue-900 p-6 text-white shadow-xl shadow-indigo-950/25">
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-100">
                  <CalendarRange className="h-3.5 w-3.5 text-cyan-300" />
                  Workforce scheduling
                </div>
                <h2 className="mt-4 text-2xl font-black tracking-[-0.04em] text-white">Shift Operations Command Center</h2>
                <p className="mt-2 max-w-2xl text-sm text-slate-300">Manage employee shift preferences, approvals, capacity and upcoming workforce coverage from one intelligent workspace.</p>
              </div>

              <div className="grid grid-cols-3 gap-2 text-left">
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Pending</div>
                  <div className="mt-1 text-lg font-black text-white">{pendingRequests.length}</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Coverage</div>
                  <div className="mt-1 text-lg font-black text-emerald-300">94%</div>
                </div>
                <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Upcoming</div>
                  <div className="mt-1 text-lg font-black text-white">{myShiftSchedule.length}</div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-indigo-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-indigo-700">
              <div className="text-xs font-semibold text-slate-500">Morning Shift (09:00 - 18:00)</div>
              <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">164 Active</div>
              <div className="mt-1 text-[11px] text-emerald-600 font-semibold">100% Slot Occupancy</div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-blue-700">
              <div className="text-xs font-semibold text-slate-500">Evening Shift (14:00 - 23:00)</div>
              <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">52 Active</div>
              <div className="mt-1 text-[11px] text-blue-600 font-semibold">Shift Allowance Active</div>
            </div>

            <div className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-purple-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-purple-700">
              <div className="text-xs font-semibold text-slate-500">Night Shift (22:00 - 07:00)</div>
              <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">32 Active</div>
              <div className="mt-1 text-[11px] text-purple-600 font-semibold">+25% Overtime Bonus Rate</div>
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100 dark:border-slate-800">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">Shift Coverage Intelligence</h3>
                <p className="text-xs text-slate-500">Operational view of current staffing pressure and surge risk</p>
              </div>
              <span className="rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300">No conflicts detected</span>
            </div>
            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
              {[
                { label: 'Morning coverage', value: 96, tone: 'emerald' },
                { label: 'Evening demand', value: 82, tone: 'blue' },
                { label: 'Night staffing', value: 74, tone: 'violet' },
              ].map((item) => (
                <div key={item.label} className="rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-800/60">
                  <div className="flex items-center justify-between text-[10px] uppercase tracking-[0.18em] text-slate-500">
                    <span>{item.label}</span>
                    <span>{item.value}%</span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                    <div className={`h-full rounded-full ${item.tone === 'emerald' ? 'bg-emerald-500' : item.tone === 'blue' ? 'bg-blue-500' : 'bg-violet-500'}`} style={{ width: `${item.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {canManageTeam ? (
        <>
          {/* Pending HR Shift Approval Queue */}
          <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-5 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4">
              {overviewStats.map((stat) => (
                <div key={stat.label} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-800/70">
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{stat.label}</div>
                  <div className="mt-3 text-2xl font-black text-slate-900 dark:text-white">{stat.value}</div>
                </div>
              ))}
            </div>

            <div className="flex flex-col gap-3 border-b border-slate-100 pb-4 dark:border-slate-800 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                  Pending Shift Requests ({pendingRequests.length})
                </h3>
                <p className="text-xs text-slate-500">Requests submitted by employees with detailed reasons</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <div className="relative min-w-[220px] flex-1 lg:min-w-[260px]">
                  <input
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search employee, shift, or reason"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-3 pr-3 text-[11px] text-slate-700 outline-none transition focus:border-indigo-300 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  />
                </div>
                <span className="rounded bg-amber-100 px-2.5 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                  HR Decision Needed
                </span>
              </div>
            </div>

            {pendingRequests.length === 0 ? (
              <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-8 text-center text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">
                No pending shift requests at the moment.
              </div>
            ) : (
              <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
                {pendingRequests
                  .filter((req) => {
                    if (!searchQuery.trim()) return true;
                    const haystack = [req.empName, req.department, req.requestedShift, req.requestLabel, req.reason, req.requestStatus].filter(Boolean).join(' ').toLowerCase();
                    return haystack.includes(searchQuery.toLowerCase());
                  })
                  .map((req) => (
                  <div
                    key={req.id}
                    className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-800/40"
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="text-sm font-bold text-slate-900 dark:text-white">{req.empName}</h4>
                        <span className="text-[11px] text-indigo-600 font-semibold dark:text-indigo-400">
                          {req.department}
                        </span>
                      </div>
                      <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                        Pending HR Review
                      </span>
                    </div>

                    <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                      <div>
                        <span className="text-[10px] text-slate-400 block">Requested Shift</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">{req.requestedShift}</span>
                      </div>
                      <div>
                        <span className="text-[10px] text-slate-400 block">Requested Date</span>
                        <span className="font-bold text-slate-800 dark:text-slate-200">{req.requestedDate}</span>
                      </div>
                    </div>

                    <div className="mt-3 rounded-lg bg-white p-2.5 text-xs border border-slate-200 dark:border-slate-700 dark:bg-slate-900">
                      <span className="font-bold text-slate-500 block text-[10px] uppercase">Reason Provided by Employee:</span>
                      <p className="mt-0.5 text-slate-700 dark:text-slate-300 font-medium">{getReasonText(req)}</p>
                    </div>

                    <div className="mt-4 flex items-center gap-2">
                      <button
                        onClick={() => onApproveShift(req.id)}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-emerald-600 py-2 text-xs font-bold text-white hover:bg-emerald-700"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        Approve Shift
                      </button>
                      <button
                        onClick={() => onRejectShift(req.id)}
                        className="flex-1 flex items-center justify-center gap-1.5 rounded-lg bg-rose-600 py-2 text-xs font-bold text-white hover:bg-rose-700"
                      >
                        <XCircle className="h-4 w-4" />
                        Reject Shift
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actioned / Approved Shift Allocation History */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <h3 className="border-b border-slate-100 pb-3 text-sm font-bold text-slate-900 dark:border-slate-800 dark:text-white">
              All Shift Request Records & Decisions
            </h3>

            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-400 uppercase font-semibold text-[10px] dark:border-slate-800">
                    <th className="py-3 px-2">Employee</th>
                    <th className="py-3 px-2">Department</th>
                    <th className="py-3 px-2">Requested Shift Slot</th>
                    <th className="py-3 px-2">Requested Date</th>
                    <th className="py-3 px-2">Reason</th>
                    <th className="py-3 px-2">HR Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                  {employeeShiftView.map((s) => (
                    <tr key={s.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="py-3 px-2 font-bold text-slate-900 dark:text-white">{s.empName}</td>
                      <td className="py-3 px-2 text-slate-600 dark:text-slate-300">{s.department}</td>
                      <td className="py-3 px-2 font-semibold text-indigo-600 dark:text-indigo-400">
                        {s.requestedShift || s.shiftName}
                      </td>
                      <td className="py-3 px-2 text-slate-500">{s.requestedDate || s.assignedDate}</td>
                      <td className="py-3 px-2 text-slate-600 dark:text-slate-300 max-w-xs truncate">
                        {getReasonText(s)}
                      </td>
                      <td className="py-3 px-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                            s.status === 'Approved'
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                              : s.status === 'Pending'
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300'
                          }`}
                        >
                          {s.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      ) : (
        <div className="space-y-6">
          <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-gradient-to-br from-slate-900 via-indigo-950 to-violet-950 shadow-xl shadow-indigo-950/10">
            <div className="border-b border-white/10 bg-white/5 p-6 backdrop-blur-sm md:p-8">
              <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
                <div className="space-y-3">
                  <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-200 ring-1 ring-white/10">Shift Center</div>
                  <div>
                    <h2 className="text-2xl font-bold tracking-[-0.04em] text-white sm:text-3xl">Your schedule, shift changes, and upcoming work.</h2>
                    <p className="mt-2 max-w-xl text-sm text-slate-300">Stay aligned with your assigned shifts, review upcoming work, and submit a change request when needed.</p>
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setShowRequestModal(true)}
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-semibold text-slate-800 shadow-sm transition hover:bg-slate-100"
                >
                  <Plus className="h-4 w-4" />
                  Request Shift Change
                </button>
              </div>
            </div>

            <div className="grid gap-4 p-6 xl:grid-cols-[1.15fr_0.85fr] xl:p-8">
              <div className="rounded-[26px] border border-white/10 bg-slate-900/40 p-5 shadow-inner shadow-white/5">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Current / next shift</div>
                    <h3 className="mt-2 text-xl font-bold tracking-[-0.03em] text-white">{nextShift ? (nextShift.shiftLabel || nextShift.requestedShift || nextShift.shiftName || 'Assigned shift') : 'No upcoming shift assigned'}</h3>
                  </div>
                  <div className="rounded-2xl bg-indigo-500/15 p-2 text-indigo-200 ring-1 ring-indigo-400/30">
                    <Clock className="h-5 w-5" />
                  </div>
                </div>

                {nextShift ? (
                  <div className="mt-5 space-y-3">
                    <div className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 p-3">
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Date</div>
                        <div className="mt-1 text-sm font-semibold text-white">{formatScheduleDate(nextShift.shiftDate)}</div>
                      </div>
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-bold ${getShiftStatusTone(nextShift.status || 'Scheduled')}`}>
                        {nextShift.status || 'Scheduled'}
                      </span>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                      <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Shift time</div>
                        <div className="mt-1 text-sm font-semibold text-white">{nextShift.shiftLabel}</div>
                      </div>
                      <div className="rounded-2xl border border-white/10 bg-white/5 p-3">
                        <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">Assigned date</div>
                        <div className="mt-1 text-sm font-semibold text-white">{formatDateLabel(nextShift.shiftDate, 'N/A')}</div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="mt-5 rounded-2xl border border-dashed border-white/15 bg-white/5 p-5 text-center">
                    <div className="text-sm font-semibold text-white">No upcoming shift assigned</div>
                    <div className="mt-1 text-xs text-slate-300">Your future schedule will appear here once it is assigned.</div>
                  </div>
                )}
              </div>

              <div className="space-y-3">
                <div className="rounded-[24px] border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
                  <div className="flex items-center justify-between">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Pending requests</div>
                    <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-300" />
                  </div>
                  <div className="mt-3 text-3xl font-black tracking-[-0.04em] text-slate-900 dark:text-white">{pendingRequests.length}</div>
                  <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">Awaiting review</div>
                </div>

                <div className="rounded-[24px] border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Upcoming schedule</div>
                  <div className="mt-3 text-3xl font-black tracking-[-0.04em] text-slate-900 dark:text-white">{myShiftSchedule.length}</div>
                  <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">Assigned / requested entries</div>
                </div>
              </div>
            </div>
          </div>

          <div className="grid gap-6 xl:grid-cols-[1.15fr_0.85fr]">
            <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Schedule</div>
                  <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Upcoming shifts</h3>
                </div>
                <CalendarRange className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
              </div>

              <div className="mt-5 space-y-3">
                {myShiftSchedule.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-950/50">
                    <div className="text-sm font-bold text-slate-900 dark:text-white">No upcoming shifts</div>
                    <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">Your future schedule will appear here.</div>
                  </div>
                ) : (
                  myShiftSchedule.slice(0, 6).map((entry) => (
                    <div key={entry.id || `${entry.empId || effectiveEmployeeId}-shift-${entry.shiftDate}`} className="rounded-[22px] border border-slate-200 bg-slate-50 p-3 transition hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-[0_18px_35px_-28px_rgba(79,70,229,0.8)] dark:border-slate-700 dark:bg-slate-950/50 dark:hover:border-indigo-700 dark:hover:bg-slate-900">
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">{formatScheduleDate(entry.shiftDate)}</div>
                          <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{entry.shiftLabel}</div>
                        </div>
                        <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${getShiftStatusTone(entry.status || 'Scheduled')}`}>
                          {entry.status || 'Scheduled'}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Requests</div>
                  <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Shift request status</h3>
                </div>
                <MessageSquare className="h-5 w-5 text-indigo-600 dark:text-indigo-300" />
              </div>

              <div className="mt-5 flex flex-wrap gap-2">
                {requestTabs.map((tab) => (
                  <button
                    key={tab}
                    type="button"
                    onClick={() => setSelectedRequestTab(tab)}
                    className={`rounded-xl px-3 py-2 text-xs font-bold transition ${
                      selectedRequestTab === tab
                        ? 'bg-indigo-600 text-white shadow-[0_16px_28px_-18px_rgba(99,102,241,0.85)]'
                        : 'border border-slate-200 bg-white text-slate-600 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-950/30 dark:text-slate-300 dark:hover:border-indigo-700 dark:hover:text-indigo-300'
                    }`}
                  >
                    {tab === 'ALL' ? 'All' : tab === 'PENDING' ? 'Pending' : tab === 'APPROVED' ? 'Approved' : 'Rejected'}
                  </button>
                ))}
              </div>

              <div className="mt-5 space-y-3">
                {filteredEmployeeRequests.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-950/50">
                    <div className="text-sm font-bold text-slate-900 dark:text-white">No shift change requests yet</div>
                    <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">Your submitted requests will appear here.</div>
                  </div>
                ) : (
                  filteredEmployeeRequests.map((request) => {
                    const isExpanded = expandedRequestId === request.id;
                    const status = request.requestStatus || 'Pending';
                    return (
                      <button
                        key={request.id || `${request.empId || effectiveEmployeeId}-${request.requestDate}`}
                        type="button"
                        onClick={() => setExpandedRequestId(isExpanded ? null : request.id || `${request.empId || effectiveEmployeeId}-${request.requestDate}`)}
                        className="group block w-full rounded-[22px] border border-slate-200 bg-slate-50 p-4 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-[0_18px_35px_-28px_rgba(79,70,229,0.8)] dark:border-slate-700 dark:bg-slate-950/50 dark:hover:border-indigo-700 dark:hover:bg-slate-900"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-2">
                              <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${getShiftStatusTone(status)}`}>{status}</span>
                              <span className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400">{request.requestLabel || 'Shift request'}</span>
                            </div>
                            <div className="mt-2 text-base font-bold text-slate-900 dark:text-white">{formatDateLabel(request.requestDate, 'N/A')}</div>
                            <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{request.requestLabel}</div>
                          </div>
                          <div className="flex items-center gap-2 text-slate-400 group-hover:text-indigo-600 dark:text-slate-500 dark:group-hover:text-indigo-300">
                            <ArrowRight className="h-4 w-4" />
                          </div>
                        </div>

                        {isExpanded && (
                          <div className="mt-4 rounded-2xl border border-slate-200 bg-white p-3 text-xs dark:border-slate-700 dark:bg-slate-900">
                            <div className="grid gap-2 sm:grid-cols-2">
                              <div>
                                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Requested shift</div>
                                <div className="mt-1 font-semibold text-slate-900 dark:text-white">{request.requestLabel}</div>
                              </div>
                              <div>
                                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Request date</div>
                                <div className="mt-1 font-semibold text-slate-900 dark:text-white">{formatDateLabel(request.requestDate, 'N/A')}</div>
                              </div>
                              <div className="sm:col-span-2">
                                <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500">Reason</div>
                                <div className="mt-1 font-medium text-slate-700 dark:text-slate-300">{getReasonText(request)}</div>
                              </div>
                            </div>
                          </div>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          </div>

          {showRequestModal && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4 backdrop-blur-sm">
              <div className="w-full max-w-xl rounded-[30px] border border-slate-200 bg-white p-5 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
                <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Shift request</div>
                    <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Request a shift change</h3>
                  </div>
                  <button type="button" onClick={() => setShowRequestModal(false)} className="flex h-9 w-9 items-center justify-center rounded-xl border border-slate-200 text-slate-500 hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                    <XCircle className="h-4 w-4" />
                  </button>
                </div>

                <form onSubmit={handleSubmitRequest} className="mt-5 space-y-4">
                  <div className="rounded-2xl border border-indigo-100 bg-indigo-50 p-3 dark:border-indigo-900/60 dark:bg-indigo-950/30">
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">Employee</div>
                    <div className="mt-1 text-sm font-semibold text-slate-900 dark:text-white">{effectiveEmployeeId || 'Current employee'}</div>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Requested shift</label>
                    <select
                      value={requestedShift}
                      onChange={(event) => setRequestedShift(event.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                    >
                      <option value="Morning Shift (09:00 - 18:00)">Morning Shift (09:00 - 18:00)</option>
                      <option value="Evening Shift (14:00 - 23:00)">Evening Shift (14:00 - 23:00)</option>
                      <option value="Night Shift (22:00 - 07:00)">Night Shift (22:00 - 07:00)</option>
                    </select>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Target date</label>
                    <input
                      type="date"
                      value={requestedDate}
                      onChange={(event) => setRequestedDate(event.target.value)}
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                      required
                    />
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-semibold text-slate-700 dark:text-slate-200">Reason</label>
                    <textarea
                      rows={4}
                      value={reason}
                      onChange={(event) => setReason(event.target.value)}
                      placeholder="Share the reason for your shift change request..."
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 dark:border-slate-700 dark:bg-slate-950/40 dark:text-white dark:focus:ring-indigo-900"
                      required
                    />
                  </div>

                  <div className="flex justify-end gap-3 border-t border-slate-100 pt-4 dark:border-slate-800">
                    <button type="button" onClick={() => setShowRequestModal(false)} className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-950 dark:text-slate-200">
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
      )}
    </div>
  );
};
