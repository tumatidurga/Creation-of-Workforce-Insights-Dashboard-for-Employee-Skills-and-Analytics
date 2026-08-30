import React, { useMemo } from 'react';
import {
  Activity,
  AlertCircle,
  ArrowRight,
  BellRing,
  BrainCircuit,
  BriefcaseBusiness,
  CalendarCheck2,
  CheckCircle2,
  ChevronRight,
  Clock3,
  FileBadge2,
  Sparkles,
  TrendingUp,
  Users,
  Zap,
} from 'lucide-react';
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const toValue = (value, fallback = null) => {
  if (value === undefined || value === null || value === 'N/A') return fallback;
  return value;
};

const normalizeId = (value) => (value === undefined || value === null ? '' : String(value).trim());
const normalizeRole = (value) => String(value || '').toUpperCase();

const getTodayIso = () => new Date().toISOString().slice(0, 10);

const formatStatus = (status) => {
  const value = String(status || '').trim();
  if (!value) return 'Unknown';
  const normalized = value.toLowerCase();
  if (normalized.includes('present')) return 'Present';
  if (normalized.includes('late')) return 'Late';
  if (normalized.includes('absent')) return 'Absent';
  if (normalized.includes('leave')) return 'On Leave';
  if (normalized.includes('pending')) return 'Pending';
  if (normalized.includes('approved')) return 'Approved';
  if (normalized.includes('rejected')) return 'Rejected';
  return value;
};

const getGreeting = () => {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good Morning';
  if (hour < 17) return 'Good Afternoon';
  return 'Good Evening';
};

const getEmployeeStatusToday = (employeeId, attendanceRecords) => {
  const targetId = normalizeId(employeeId);
  const today = getTodayIso();
  const match = (attendanceRecords || []).find((entry) => {
    const id = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
    const date = normalizeId(entry?.date || entry?.Date || entry?.recordDate || entry?.RecordDate || '').slice(0, 10);
    return id === targetId && date === today;
  });

  if (!match) return 'Absent';
  const checkIn = match?.checkIn || match?.CheckIn;
  const checkOut = match?.checkOut || match?.CheckOut;
  const status = String(match?.attendanceStatus || match?.AttendanceStatus || match?.status || '').trim();
  if (checkIn && !checkOut) return 'Present';
  if (status.toLowerCase().includes('late')) return 'Late';
  if (status.toLowerCase().includes('leave')) return 'On Leave';
  if (status.toLowerCase().includes('absent')) return 'Absent';
  return 'Present';
};

// Leave, shift and timesheet requests are visible to every manager, not only for their own
// reports, so team membership is not re-checked against the employees list here. Only the
// manager's own records are excluded, so nobody can approve their own request.
const isReviewableFor = (employeeId, managerId) => {
  const id = normalizeId(employeeId);
  return Boolean(id) && id !== managerId;
};

// Requests can belong to employees outside this manager's team, who are therefore absent from
// the (team-scoped) employees list. Prefer the name carried on the record, fall back to the
// employees list, and last of all show the employee ID so the row is still identifiable.
const resolveEmployeeLabel = (entry, employeeId, employees) => {
  const fromRecord = entry?.empName || entry?.EmpName || entry?.employeeName || entry?.EmployeeName;
  if (fromRecord) return fromRecord;
  const emp = (employees || []).find((member) => {
    const memberId = normalizeId(member?.empId || member?.EmpID || member?.EmpId || member?.employeeId);
    return memberId === employeeId;
  });
  return emp?.EmployeeName || emp?.employeeName || emp?.name || employeeId || 'Employee';
};

const getPendingCount = (items, key = 'status') =>
  (items || []).filter((item) => {
    const value = String(item?.[key] || item?.Status || '').trim().toLowerCase();
    return value === 'pending' || value === 'submitted';
  }).length;

export const ManagerDashboard = ({
  employees = [],
  attendance = [],
  leaves = [],
  shifts = [],
  timesheets = [],
  profile = null,
  managerEmpId = null,
  managerLoginId = null,
  userRole = 'MANAGER',
  onNavigate = () => {},
  onApproveLeave = null,
  onRejectLeave = null,
  onApproveShift = null,
  onRejectShift = null,
  onApproveTimesheet = null,
  onRejectTimesheet = null,
  dashboardLoading = false,
  dashboardError = null,
}) => {
  const managerId = normalizeId(managerEmpId || profile?.empId || profile?.EmpID || profile?.EmpId || profile?.employeeId || '');
  const managerName = profile?.name || profile?.EmployeeName || 'Manager';
  const managerDepartment = profile?.department || profile?.Department || 'Operations';
  const managerTitle = profile?.jobRole || profile?.JobRole || 'Operations Manager';

  const directReports = useMemo(() => {
    if (!managerId) return [];
    return (employees || []).filter((employee) => {
      const candidateIds = [
        normalizeId(employee?.ManagerID),
        normalizeId(employee?.managerId),
        normalizeId(employee?.managerEmpId),
        normalizeId(employee?.managerID),
        normalizeId(employee?.manager_id),
      ];
      return candidateIds.includes(managerId) && normalizeRole(employee?.Role || employee?.role || 'Employee') !== 'HR_ADMIN';
    });
  }, [employees, managerId]);

  const todayIso = getTodayIso();

  const presentToday = useMemo(() => {
    return directReports.filter((employee) => {
      const status = getEmployeeStatusToday(employee?.empId || employee?.EmpID || employee?.EmpId, attendance);
      return status === 'Present' || status === 'Late';
    }).length;
  }, [directReports, attendance]);

  const onLeaveToday = useMemo(() => {
    return directReports.filter((employee) => {
      const empId = normalizeId(employee?.empId || employee?.EmpID || employee?.EmpId);
      return (leaves || []).some((entry) => {
        const leavesEmpId = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
        const status = String(entry?.status || entry?.Status || '').trim().toLowerCase();
        const start = normalizeId(entry?.startDate || entry?.StartDate || '');
        const end = normalizeId(entry?.endDate || entry?.EndDate || '');
        const inRange = !start || !end ? false : start <= todayIso && end >= todayIso;
        return leavesEmpId === empId && (status === 'approved' || status === 'pending') && inRange;
      });
    }).length;
  }, [directReports, leaves, todayIso]);

  const pendingApprovals = useMemo(() => {
    const countPending = (records) => (records || []).filter((entry) => {
      const id = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
      return isReviewableFor(id, managerId) && ['pending', 'submitted'].includes(String(entry?.status || entry?.Status || '').trim().toLowerCase());
    }).length;
    return countPending(leaves) + countPending(shifts) + countPending(timesheets);
  }, [managerId, leaves, shifts, timesheets]);

  const teamAttendanceTrend = useMemo(() => {
    const lastDays = Array.from({ length: 7 }).map((_, index) => {
      const date = new Date();
      date.setDate(date.getDate() - (6 - index));
      return date.toISOString().slice(0, 10);
    });

    return lastDays.map((date) => {
      let present = 0;
      let absent = 0;
      let onLeave = 0;

      for (const employee of directReports) {
        const empId = normalizeId(employee?.empId || employee?.EmpID || employee?.EmpId);
        const dayRecord = (attendance || []).find((entry) => {
          const entryEmp = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
          const entryDate = normalizeId(entry?.date || entry?.Date || '').slice(0, 10);
          return entryEmp === empId && entryDate === date;
        });

        if (!dayRecord) {
          absent += 1;
          continue;
        }

        const status = String(dayRecord?.attendanceStatus || dayRecord?.AttendanceStatus || dayRecord?.status || '').toLowerCase();
        if (status.includes('leave')) {
          onLeave += 1;
        } else if (dayRecord?.checkIn || dayRecord?.CheckIn || status.includes('present') || status.includes('late')) {
          present += 1;
        } else {
          absent += 1;
        }
      }

      return { date: date.slice(5), present, absent, onLeave };
    });
  }, [attendance, directReports]);

  const teamBreakdown = useMemo(() => {
    const present = presentToday;
    const absent = Math.max(directReports.length - presentToday - onLeaveToday, 0);
    return [
      { name: 'Present', value: present, color: '#4f46e5' },
      { name: 'On Leave', value: onLeaveToday, color: '#a78bfa' },
      { name: 'Absent', value: absent, color: '#f59e0b' },
    ].filter((entry) => entry.value > 0);
  }, [directReports, onLeaveToday, presentToday]);

  const approvalItems = useMemo(() => {
    const items = [];

    (leaves || []).forEach((entry) => {
      const status = String(entry?.status || entry?.Status || '').trim();
      const employeeId = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
      if (status.toLowerCase() === 'pending' && isReviewableFor(employeeId, managerId)) {
        items.push({
          type: 'Leave',
          employee: resolveEmployeeLabel(entry, employeeId, employees),
          date: entry?.startDate || entry?.StartDate || '—',
          status,
          id: entry?._id || entry?.id || entry?.leaveId,
          target: 'leave',
        });
      }
    });

    (shifts || []).forEach((entry) => {
      const status = String(entry?.status || entry?.Status || '').trim();
      const employeeId = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
      if (status.toLowerCase() === 'pending' && isReviewableFor(employeeId, managerId)) {
        items.push({
          type: 'Shift',
          employee: resolveEmployeeLabel(entry, employeeId, employees),
          date: entry?.shiftDate || entry?.ShiftDate || entry?.date || '—',
          status,
          id: entry?._id || entry?.id || entry?.shiftId,
          target: 'shifts',
        });
      }
    });

    (timesheets || []).forEach((entry) => {
      const status = String(entry?.status || entry?.Status || '').trim();
      const employeeId = normalizeId(entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId);
      if ((status.toLowerCase() === 'pending' || status.toLowerCase() === 'submitted') && isReviewableFor(employeeId, managerId)) {
        items.push({
          type: 'Timesheet',
          employee: resolveEmployeeLabel(entry, employeeId, employees),
          date: entry?.date || entry?.Date || '—',
          status,
          id: entry?._id || entry?.id || entry?.timesheetId,
          target: 'timesheets',
        });
      }
    });

    return items.slice(0, 5);
  }, [managerId, employees, leaves, shifts, timesheets]);

  const latestTeamMembers = useMemo(() => {
    return directReports.slice(0, 4).map((employee) => {
      const empId = normalizeId(employee?.empId || employee?.EmpID || employee?.EmpId || employee?.employeeId);
      const status = getEmployeeStatusToday(empId, attendance);
      return {
        ...employee,
        empId,
        status,
      };
    });
  }, [attendance, directReports]);

  const metricCards = [
    {
      title: 'Total Team Members',
      value: directReports.length,
      hint: 'Direct reports under your management',
      accent: 'from-indigo-500 to-indigo-700',
      icon: Users,
      iconBg: 'bg-indigo-100 text-indigo-700',
      trend: `${directReports.length > 0 ? 'Active team coverage' : 'No direct reports'}`,
    },
    {
      title: 'Present Today',
      value: presentToday,
      hint: `${directReports.length ? `${Math.round((presentToday / directReports.length) * 100)}% team availability` : 'No team activity yet'}`,
      accent: 'from-emerald-500 to-emerald-700',
      icon: CalendarCheck2,
      iconBg: 'bg-emerald-100 text-emerald-700',
      trend: directReports.length ? 'Attendance is on track' : 'Waiting for team check-ins',
    },
    {
      title: 'On Leave',
      value: onLeaveToday,
      hint: `${onLeaveToday ? `${onLeaveToday} planned absence` : 'No planned absences'}`,
      accent: 'from-violet-500 to-violet-700',
      icon: Clock3,
      iconBg: 'bg-violet-100 text-violet-700',
      trend: onLeaveToday ? 'Review staffing coverage' : 'Coverage stable',
    },
    {
      title: 'Pending Approvals',
      value: pendingApprovals,
      hint: pendingApprovals ? `${pendingApprovals} action required` : 'No approvals pending',
      accent: 'from-amber-500 to-orange-500',
      icon: BellRing,
      iconBg: 'bg-amber-100 text-amber-700',
      trend: pendingApprovals ? 'Review queue is active' : 'Queue is clear',
    },
  ];

  const insightText = useMemo(() => {
    if (!directReports.length) return 'No direct reports are available for your current team view.';
    if (pendingApprovals > 0) return `${pendingApprovals} review items are waiting in your approval queue.`;
    if (presentToday >= directReports.length * 0.8) return 'Team productivity is stable and attendance remains strong this week.';
    return 'Team productivity is steady and operational coverage remains balanced.';
  }, [directReports.length, pendingApprovals, presentToday]);

  if (dashboardLoading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse rounded-3xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="mb-4 h-6 w-56 rounded bg-slate-200" />
          <div className="h-4 w-40 rounded bg-slate-200" />
        </div>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          {[...Array(4)].map((_, idx) => (
            <div key={idx} className="h-36 animate-pulse rounded-2xl border border-slate-200 bg-white p-4" />
          ))}
        </div>
      </div>
    );
  }

  if (dashboardError) {
    return (
      <div className="rounded-2xl border border-rose-200 bg-rose-50 p-5 text-sm text-rose-700 shadow-sm">
        <div className="mb-2 flex items-center gap-2 font-semibold">
          <AlertCircle className="h-4 w-4" />
          Manager dashboard data error
        </div>
        <p>{dashboardError}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="relative overflow-hidden rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-600 via-violet-600 to-sky-600 p-6 text-white shadow-xl shadow-indigo-500/20">
        <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full bg-white/10 blur-2xl" />
        <div className="absolute bottom-0 left-1/3 h-28 w-28 rounded-full bg-sky-300/20 blur-3xl" />
        <div className="relative flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[10px] font-bold tracking-[0.22em] text-indigo-50 uppercase">
              <Sparkles className="h-3.5 w-3.5" />
              Team Operations Center
            </div>
            <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">{getGreeting()}, {managerName}</h2>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-sm text-indigo-50/90">
              <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-2.5 py-1 backdrop-blur-sm">
                <BriefcaseBusiness className="h-4 w-4" />
                {managerDepartment}
              </span>
              <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-2.5 py-1 backdrop-blur-sm">
                <Users className="h-4 w-4" />
                {managerTitle}
              </span>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-indigo-100">
              {managerLoginId && (
                <span className="rounded-full border border-white/20 bg-white/5 px-2.5 py-1">Login ID: {managerLoginId}</span>
              )}
              {managerId && (
                <span className="rounded-full border border-white/20 bg-white/5 px-2.5 py-1">Internal ID: {managerId}</span>
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-white/15 bg-slate-950/10 p-4 backdrop-blur-sm">
            <div className="text-[10px] font-semibold uppercase tracking-[0.2em] text-indigo-100/80">Today</div>
            <div className="mt-2 text-lg font-bold">{new Date().toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })}</div>
            <div className="mt-2 flex items-center gap-2 text-xs text-indigo-50/80">
              <BellRing className="h-3.5 w-3.5" />
              {pendingApprovals ? `${pendingApprovals} items need attention` : 'Operations running smoothly'}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        {metricCards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.title}
              className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg"
            >
              <div className="mb-3 flex items-center justify-between">
                <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${card.iconBg}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <div className={`rounded-full bg-gradient-to-r ${card.accent} px-2 py-1 text-[9px] font-bold uppercase tracking-wider text-white`}>
                  {card.trend}
                </div>
              </div>
              <div className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">{card.title}</div>
              <div className="mt-3 text-3xl font-black tracking-tight text-slate-900">{card.value}</div>
              <div className="mt-2 text-xs text-slate-500">{card.hint}</div>
            </div>
          );
        })}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.65fr_0.95fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Team Activity Overview</h3>
              <p className="text-xs text-slate-500">Attendance pattern across the last 7 days</p>
            </div>
            <div className="inline-flex items-center gap-2 rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-bold text-indigo-700">
              <TrendingUp className="h-3.5 w-3.5" />
              Weekly trend
            </div>
          </div>

          <div className="h-72 w-full">
            <ResponsiveContainer>
              <AreaChart data={teamAttendanceTrend}>
                <defs>
                  <linearGradient id="presentGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#4f46e5" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#4f46e5" stopOpacity={0.1} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip />
                <Area type="monotone" dataKey="present" stroke="#4f46e5" strokeWidth={3} fill="url(#presentGradient)" />
                <Area type="monotone" dataKey="onLeave" stroke="#a78bfa" strokeWidth={2} fill="#a78bfa" fillOpacity={0.15} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Team Composition</h3>
              <p className="text-xs text-slate-500">Current distribution</p>
            </div>
            <Zap className="h-4 w-4 text-indigo-500" />
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer>
              <PieChart>
                <Pie data={teamBreakdown} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                  {teamBreakdown.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="space-y-2">
            {teamBreakdown.map((entry) => (
              <div key={entry.name} className="flex items-center justify-between rounded-xl bg-slate-50 px-3 py-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: entry.color }} />
                  <span className="font-medium text-slate-700">{entry.name}</span>
                </div>
                <span className="font-bold text-slate-900">{entry.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.5fr_1fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Team Members Snapshot</h3>
              <p className="text-xs text-slate-500">Your direct reports</p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('employees')}
              className="inline-flex items-center gap-2 rounded-xl bg-slate-900 px-3 py-2 text-[10px] font-bold uppercase tracking-[0.14em] text-white transition hover:bg-slate-800"
            >
              View Team
              <ChevronRight className="h-3.5 w-3.5" />
            </button>
          </div>

          {directReports.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-8 text-center text-sm text-slate-500">
              No direct reports are visible for this manager account.
            </div>
          ) : (
            <div className="space-y-3">
              {latestTeamMembers.map((employee) => {
                const empName = employee?.EmployeeName || employee?.employeeName || employee?.name || 'Employee';
                const empId = normalizeId(employee?.empId || employee?.EmpID || employee?.EmpId || employee?.employeeId);
                const title = employee?.JobRole || employee?.jobRole || 'Team Member';
                const department = employee?.Department || employee?.department || 'Operations';
                const status = getEmployeeStatusToday(empId, attendance);
                const initials = empName.split(' ').map((part) => part[0]).slice(0, 2).join('').toUpperCase();

                return (
                  <div key={empId || empName} className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50/80 p-3 transition hover:border-indigo-200 hover:bg-indigo-50/50">
                    <div className="flex items-center gap-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-sm font-bold text-white">
                        {initials || 'EM'}
                      </div>
                      <div>
                        <div className="font-semibold text-slate-900">{empName}</div>
                        <div className="text-[11px] text-slate-500">{empId || 'Unknown ID'} • {title}</div>
                        <div className="mt-1 text-[10px] text-slate-400">{department}</div>
                      </div>
                    </div>

                    <div className="text-right">
                      <div className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-[10px] font-bold ${
                        status === 'Present' ? 'bg-emerald-100 text-emerald-700' :
                        status === 'Late' ? 'bg-amber-100 text-amber-700' :
                        status === 'On Leave' ? 'bg-violet-100 text-violet-700' : 'bg-slate-200 text-slate-700'
                      }`}>
                        {status}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Approval Center</h3>
              <p className="text-xs text-slate-500">Pending team actions</p>
            </div>
            <button
              type="button"
              onClick={() => onNavigate('leave')}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-700 transition hover:border-slate-300 hover:bg-white"
            >
              Open Approval Center
            </button>
          </div>

          <div className="space-y-3">
            {approvalItems.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-4 text-center text-sm text-slate-500">
                No pending approvals in the current team queue.
              </div>
            ) : (
              approvalItems.map((item) => (
                <div key={`${item.target}-${item.id || item.employee}-${item.date}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <div className="text-sm font-semibold text-slate-900">{item.employee}</div>
                      <div className="mt-1 text-[11px] text-slate-500">{item.type} • {item.date}</div>
                    </div>
                    <span className="rounded-full bg-amber-100 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-amber-700">
                      {item.status}
                    </span>
                  </div>

                  <div className="mt-3 flex gap-2">
                    {item.target === 'leave' && onApproveLeave && (
                      <button type="button" onClick={() => onApproveLeave(item.id, 'Approved by manager review')} className="rounded-lg bg-emerald-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Approve</button>
                    )}
                    {item.target === 'leave' && onRejectLeave && (
                      <button type="button" onClick={() => onRejectLeave(item.id, 'Rejected by manager review')} className="rounded-lg bg-rose-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Reject</button>
                    )}
                    {item.target === 'shifts' && onApproveShift && (
                      <button type="button" onClick={() => onApproveShift(item.id)} className="rounded-lg bg-emerald-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Approve</button>
                    )}
                    {item.target === 'shifts' && onRejectShift && (
                      <button type="button" onClick={() => onRejectShift(item.id)} className="rounded-lg bg-rose-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Reject</button>
                    )}
                    {item.target === 'timesheets' && onApproveTimesheet && (
                      <button type="button" onClick={() => onApproveTimesheet(item.id)} className="rounded-lg bg-emerald-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Approve</button>
                    )}
                    {item.target === 'timesheets' && onRejectTimesheet && (
                      <button type="button" onClick={() => onRejectTimesheet(item.id)} className="rounded-lg bg-rose-600 px-2.5 py-1.5 text-[10px] font-bold text-white">Reject</button>
                    )}
                    <button type="button" onClick={() => onNavigate(item.target === 'leave' ? 'leave' : item.target === 'shifts' ? 'shifts' : 'timesheets')} className="rounded-lg bg-slate-900 px-2.5 py-1.5 text-[10px] font-bold text-white">View</button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">NEXUS AI Workforce Insight</h3>
              <p className="text-xs text-slate-500">Operational intelligence derived from your team data</p>
            </div>
            <div className="rounded-full bg-purple-100 p-2 text-purple-700">
              <BrainCircuit className="h-4 w-4" />
            </div>
          </div>

          <div className="rounded-2xl bg-gradient-to-r from-violet-50 via-indigo-50 to-sky-50 p-4 ring-1 ring-violet-100">
            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-r from-violet-600 to-indigo-600 text-white shadow-md shadow-violet-500/20">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <div className="text-sm font-semibold text-slate-800">Operational insight</div>
                <p className="mt-2 text-sm leading-6 text-slate-700">{insightText}</p>
              </div>
            </div>
          </div>

          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">Attendance</div>
              <div className="mt-2 text-lg font-bold text-slate-900">{directReports.length ? `${Math.round((presentToday / directReports.length) * 100)}%` : '0%'}</div>
              <div className="mt-1 text-[11px] text-slate-500">Present across your team today</div>
            </div>
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
              <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">Queue</div>
              <div className="mt-2 text-lg font-bold text-slate-900">{pendingApprovals}</div>
              <div className="mt-1 text-[11px] text-slate-500">Pending manager actions</div>
            </div>
          </div>
        </div>

        <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="mb-4 flex items-center justify-between">
            <div>
              <h3 className="text-lg font-bold text-slate-900">Quick Actions</h3>
              <p className="text-xs text-slate-500">Fast team navigation</p>
            </div>
            <Activity className="h-4 w-4 text-indigo-500" />
          </div>

          <div className="space-y-3">
            {[
              { label: 'View My Team', tab: 'employees', icon: Users },
              { label: 'Review Attendance', tab: 'attendance', icon: CalendarCheck2 },
              { label: 'Approve Requests', tab: 'leave', icon: FileBadge2 },
              { label: 'Review Timesheets', tab: 'timesheets', icon: Clock3 },
            ].map((action) => {
              const Icon = action.icon;
              return (
                <button
                  key={action.label}
                  type="button"
                  onClick={() => onNavigate(action.tab)}
                  className="flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 text-left transition hover:border-indigo-200 hover:bg-indigo-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-indigo-700 shadow-sm">
                      <Icon className="h-4 w-4" />
                    </div>
                    <span className="font-semibold text-slate-800">{action.label}</span>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-500" />
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ManagerDashboard;
