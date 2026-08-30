import React from 'react';
import {
  Users,
  Clock,
  AlertTriangle,
  DollarSign,
  TrendingUp,
  Sparkles,
  ArrowUpRight,
  ShieldAlert,
  UserPlus,
  FileSpreadsheet,
  Zap,
  CheckCircle2,
  Calendar
} from 'lucide-react';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';



export const ExecutiveDashboard = ({
  employees = [],
  attendance = [],
  leaves = [],
  dashboardMetrics = {},
  dashboardLoading = false,
  dashboardError = null,
  userRole = 'EMPLOYEE',
  onNavigate = () => {},
  onOpenAIChat = () => {},
  shifts = [],
  payroll = [],
  payrollLoading = false,
  leaveBalance = {},
  profile = null,
  holidays = [],
  holidaysLoading = false,
  holidaysError = null
}) => {
  const metrics = dashboardMetrics || {};
  const formatCurrencyCompact = (value) => {
    const numericValue = Number(value);
    if (!Number.isFinite(numericValue)) {
      return 'N/A';
    }

    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 1
    }).format(numericValue);
  };

  const totalEmployees = Number.isFinite(Number(metrics.totalEmployees))
    ? Number(metrics.totalEmployees)
    : (employees?.length ?? 'N/A');
  const activeCount = Number.isFinite(Number(metrics.activeEmployees))
    ? Number(metrics.activeEmployees)
    : employees.filter((e) => String(e.status).toLowerCase() === 'active').length;
  const pendingLeaves = leaves.filter((l) => String(l.status).toLowerCase() === 'pending');
  const pendingLeaveRequests = Number.isFinite(Number(metrics.pendingLeaveRequests))
    ? Number(metrics.pendingLeaveRequests)
    : pendingLeaves.length;
  const attendanceRate = metrics.attendanceRate || 'N/A';
  const payrollValue = Number.isFinite(Number(metrics.totalMonthlyPayroll))
    ? formatCurrencyCompact(metrics.totalMonthlyPayroll)
    : 'N/A';
  const pendingShiftRequests = Number.isFinite(Number(metrics.pendingShiftRequests))
    ? Number(metrics.pendingShiftRequests)
    : 0;
  const attritionRiskCount = Number.isFinite(Number(metrics.attritionRiskCount))
    ? Number(metrics.attritionRiskCount)
    : 0;

  const normalizeAttendanceStatus = (value) => {
    if (value === null || value === undefined) return '';
    return String(value).trim().toLowerCase();
  };

  const attendanceSummary = (attendance || []).reduce((acc, record) => {
    const status = normalizeAttendanceStatus(record?.AttendanceStatus || record?.attendanceStatus || record?.status || '');
    if (['present', 'on time', 'check in', 'checked in'].includes(status)) {
      acc.present += 1;
    } else if (status === 'late') {
      acc.late += 1;
    } else if (status === 'absent') {
      acc.absent += 1;
    } else if (status === 'leave') {
      acc.leave += 1;
    }
    return acc;
  }, { present: 0, late: 0, absent: 0, leave: 0 });

  const attendanceLiveTotal = Math.max(1, attendanceSummary.present + attendanceSummary.late + attendanceSummary.absent + attendanceSummary.leave);
  const attendanceLiveRate = attendanceSummary.present + attendanceSummary.late > 0
    ? `${Math.round(((attendanceSummary.present + attendanceSummary.late) / attendanceLiveTotal) * 100)}%`
    : 'N/A';

  const formatHolidayDate = (value) => {
    if (!value) return '—';
    const parsed = new Date(value);
    if (Number.isNaN(parsed.getTime())) return value;
    return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  const upcomingHolidays = (holidays || [])
    .map((holiday) => {
      const holidayDate = holiday?.date || holiday?.Date || holiday?.holidayDate || holiday?.holiday_date || holiday?.day || null;
      const dateValue = holidayDate ? new Date(holidayDate) : null;
      return {
        ...holiday,
        dateValue,
        label: holiday?.name || holiday?.Name || holiday?.holidayName || holiday?.title || 'Holiday',
        dateText: formatHolidayDate(holidayDate),
      };
    })
    .filter((holiday) => holiday.dateValue && holiday.dateValue.getTime() >= new Date(new Date().setHours(0, 0, 0, 0)).getTime())
    .sort((a, b) => a.dateValue - b.dateValue)
    .slice(0, 4);

  const pendingApprovalQueue = [
    ...pendingLeaves.map((leave) => ({
      id: leave?.id || leave?._id || leave?.requestId || leave?.request_id || `leave-${leave?.empId || 'unknown'}`,
      type: 'Leave',
      label: leave?.empName || leave?.employeeName || leave?.EmpName || 'Employee',
      detail: `${leave?.leaveType || 'Leave'} • ${leave?.days ?? 0} day(s) • ${leave?.startDate || '—'} to ${leave?.endDate || '—'}`,
      date: leave?.startDate || leave?.StartDate || '—',
      status: leave?.status || leave?.Status || 'Pending',
      route: 'leave',
    })),
    ...((Array.isArray(shifts) ? shifts : [])
      .filter((shift) => String(shift?.status || shift?.Status || '').toLowerCase() === 'pending')
      .map((shift) => ({
        id: shift?.id || shift?._id || shift?.shiftId || shift?.ShiftID || `shift-${shift?.empId || 'unknown'}`,
        type: 'Shift',
        label: shift?.employeeName || shift?.EmployeeName || shift?.empName || 'Employee',
        detail: `${shift?.shiftName || shift?.ShiftName || 'Shift'} • ${shift?.shiftStart || shift?.ShiftStart || '—'} - ${shift?.shiftEnd || shift?.ShiftEnd || '—'}`,
        date: shift?.shiftDate || shift?.ShiftDate || '—',
        status: shift?.status || shift?.Status || 'Pending',
        route: 'shifts',
      }))),
    ...((Array.isArray(payroll) ? payroll : [])
      .filter((item) => String(item?.status || item?.Status || '').toLowerCase() === 'pending')
      .map((item) => ({
        id: item?.id || item?._id || item?.payrollId || item?.PayrollID || `payroll-${item?.empId || 'unknown'}`,
        type: 'Payroll',
        label: item?.employeeName || item?.EmployeeName || item?.empName || 'Employee',
        detail: `Payroll review • ${item?.payrollMonth || item?.PayrollMonth || 'Current month'}`,
        date: item?.payrollMonth || item?.PayrollMonth || '—',
        status: item?.status || item?.Status || 'Pending',
        route: 'payroll',
      }))),
  ].slice(0, 5);

  // Employee-specific personal dashboard
  if (userRole === 'EMPLOYEE') {
    const empId = (dashboardMetrics && dashboardMetrics.empId) || profile?.empId || profile?.EmpID || profile?.EmpId || null;
    const deriveEmpId = (record) => record?.empId || record?.EmpID || record?.EmpId || record?.employeeId || null;
    const inferredEmpId = empId || (attendance && attendance.length ? deriveEmpId(attendance[0]) : null);
    const myEmpId = inferredEmpId || null;
    const employeeRecord = (employees || []).find((entry) => {
      const candidateId = entry?.empId || entry?.EmpID || entry?.EmpId || entry?.employeeId || null;
      return candidateId && myEmpId && String(candidateId) === String(myEmpId);
    }) || null;
    const employeeName = profile?.name || profile?.fullName || `${employeeRecord?.firstName || ''} ${employeeRecord?.lastName || ''}`.trim() || 'Employee';
    const employeeDepartment = profile?.department || employeeRecord?.Department || employeeRecord?.department || 'Operations';
    const employeeRole = profile?.jobRole || employeeRecord?.JobRole || employeeRecord?.jobRole || 'Employee';
    const todayKey = new Date().toLocaleDateString('en-CA');

    const normalizeDateKey = (value) => {
      if (!value) return null;
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) return null;
      const year = date.getFullYear();
      const month = String(date.getMonth() + 1).padStart(2, '0');
      const day = String(date.getDate()).padStart(2, '0');
      return `${year}-${month}-${day}`;
    };

    const todaysRecord = (attendance || []).find((record) => {
      const rid = deriveEmpId(record);
      const recordDate = normalizeDateKey(record?.date || record?.Date || record?.checkInDate || record?.checkIn || record?.CheckIn);
      return rid && myEmpId && String(rid) === String(myEmpId) && recordDate === todayKey;
    }) || null;

    const workMode =
      profile?.workMode ||
      dashboardMetrics?.workMode ||
      todaysRecord?.workMode ||
      todaysRecord?.WorkMode ||
      'Office';

    const statusLabel = todaysRecord
      ? (todaysRecord?.AttendanceStatus || todaysRecord?.status || (todaysRecord?.checkOut || todaysRecord?.CheckOut ? 'Completed' : 'Working'))
      : 'Not Checked In';

    const checkInValue = todaysRecord?.checkIn || todaysRecord?.CheckIn || '—';
    const checkOutValue = todaysRecord?.checkOut || todaysRecord?.CheckOut || '—';
    const workingHoursValue = todaysRecord?.workingHours ?? todaysRecord?.WorkingHours ?? 0;

    const days = Array.from({ length: 7 }).map((_, idx) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - idx));
      return normalizeDateKey(d);
    });

    const attendanceMap = days.map((day) => {
      const records = (attendance || []).filter((r) => {
        const rid = deriveEmpId(r);
        const date = normalizeDateKey(r.date || r.Date || r.DateString || r.DateTime || r.RecordDate);
        return rid && myEmpId && String(rid) === String(myEmpId) && date === day;
      });
      const present = records.filter((r) => {
        const status = (r.AttendanceStatus || r.attendanceStatus || r.status || '').toString().toLowerCase();
        return status === 'present' || status === 'late' || (r.workingHours || r.WorkingHours || 0) > 0;
      }).length;
      const late = records.filter((r) => r.LateArrival === true || r.lateArrival === true).length;
      const leave = records.filter((r) => {
        const status = (r.AttendanceStatus || r.attendanceStatus || r.status || '').toString().toLowerCase();
        return status === 'leave';
      }).length;
      const holiday = records.filter((r) => (r.AttendanceStatus || r.status || '').toString().toLowerCase() === 'holiday').length;
      return {
        date: day,
        present,
        late,
        leave,
        holiday,
      };
    });

    const totalPresent = attendanceMap.reduce((sum, item) => sum + item.present, 0);
    const totalDays = attendanceMap.length || 1;
    const attendanceRateEmp = totalDays ? `${Math.round((totalPresent / totalDays) * 100)}%` : 'N/A';

    const myLeaves = (leaves || []).filter((l) => {
      const lid = deriveEmpId(l);
      return lid && myEmpId && String(lid) === String(myEmpId);
    });

    const myNextShift = (Array.isArray(shifts) ? shifts : []).filter((s) => {
      const sid = deriveEmpId(s);
      return sid && myEmpId && String(sid) === String(myEmpId);
    }).sort((a, b) => {
      const aDate = a.ShiftDate || a.shiftDate || '9999-12-31';
      const bDate = b.ShiftDate || b.shiftDate || '9999-12-31';
      return String(aDate).localeCompare(String(bDate));
    })[0];

    const myPayroll = (Array.isArray(payroll) ? payroll : []).filter((p) => {
      const pid = deriveEmpId(p);
      return pid && myEmpId && String(pid) === String(myEmpId);
    }).sort((a, b) => {
      const aMonth = a.PayrollMonth ?? a.payrollMonth ?? a.month ?? '0000-00';
      const bMonth = b.PayrollMonth ?? b.payrollMonth ?? b.month ?? '0000-00';
      return String(bMonth).localeCompare(String(aMonth));
    })[0];

    const latestPayrollDisplay = (() => {
      if (payrollLoading) return 'Loading...';
      if (!myPayroll) return 'No payroll available';
      const rawValue = myPayroll.NetSalary ?? myPayroll.netSalary ?? myPayroll.NetPay ?? myPayroll.netPay ?? null;
      if (rawValue === null || rawValue === undefined || Number.isNaN(Number(rawValue))) {
        return 'No payroll available';
      }
      return `₹${Number(rawValue).toLocaleString()}`;
    })();

    const latestPayrollPeriod = (() => {
      if (payrollLoading) return 'Loading...';
      if (!myPayroll) return 'No payroll available';
      return myPayroll?.PayrollMonth ?? myPayroll?.payrollMonth ?? myPayroll?.month ?? 'No payroll available';
    })();

    const latestPayrollStatus = (() => {
      if (payrollLoading) return 'Loading...';
      if (!myPayroll) return 'No payroll available';
      return 'Processed';
    })();

    const leaveBalanceSummary = leaveBalance || {
      casualLeave: { remaining: 0, total: 0 },
      sickLeave: { remaining: 0, total: 0 },
      earnedLeave: { remaining: 0, total: 0 },
    };

    const parseLocalDate = (value) => {
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
    };

    const formatTimelineDate = (value) => {
      const date = parseLocalDate(value);
      if (!date) return 'Recently';

      const now = new Date();
      const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
      const target = new Date(date.getFullYear(), date.getMonth(), date.getDate());
      const diffDays = Math.round((today.getTime() - target.getTime()) / 86400000);

      if (diffDays === 0) return 'Today';
      if (diffDays === 1) return 'Yesterday';
      if (diffDays < 7) {
        return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
      }
      return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
    };

    const recentActivity = (() => {
      const timeline = [];

      const pushItem = (item) => {
        if (!item || !item.label) return;
        const dateValue = item.dateValue || item.date || item.time || item.timestamp || new Date();
        const parsedDate = parseLocalDate(dateValue) || new Date();
        timeline.push({
          ...item,
          dateValue: parsedDate,
          target: item.target || 'attendance',
        });
      };

      (attendance || []).forEach((entry) => {
        const rid = deriveEmpId(entry);
        if (!rid || !myEmpId || String(rid) !== String(myEmpId)) return;

        const status = String(entry?.AttendanceStatus || entry?.attendanceStatus || entry?.status || '').toLowerCase();
        const dateValue = entry?.Date || entry?.date || entry?.checkInDate || entry?.checkIn || entry?.CheckIn || entry?.CheckOut || entry?.checkOut;
        const checkIn = entry?.CheckIn || entry?.checkIn;
        const checkOut = entry?.CheckOut || entry?.checkOut;
        const late = entry?.LateArrival === true || entry?.lateArrival === true || status === 'late';

        if (late) {
          pushItem({
            type: 'attendance',
            label: 'Late attendance',
            detail: checkIn ? `Checked in at ${checkIn}` : 'Late arrival recorded',
            dateValue,
            target: 'attendance',
          });
        }

        if (checkIn) {
          pushItem({
            type: 'attendance',
            label: 'Attendance check-in',
            detail: `Check-in recorded at ${checkIn}`,
            dateValue,
            target: 'attendance',
          });
        }

        if (checkOut) {
          pushItem({
            type: 'attendance',
            label: 'Attendance check-out',
            detail: `Check-out recorded at ${checkOut}`,
            dateValue,
            target: 'attendance',
          });
        }

        if (status === 'absent') {
          pushItem({
            type: 'attendance',
            label: 'Attendance exception',
            detail: 'No attendance was recorded for this day',
            dateValue,
            target: 'attendance',
          });
        }
      });

      (myLeaves || []).forEach((entry) => {
        const status = String(entry?.Status || entry?.status || '').toLowerCase();
        const dateValue = entry?.StartDate || entry?.startDate || entry?.EndDate || entry?.endDate || new Date();
        if (status === 'pending') {
          pushItem({
            type: 'leave',
            label: 'Leave request submitted',
            detail: `${entry?.LeaveType || entry?.leaveType || 'Leave'} requested`,
            dateValue,
            target: 'leave',
          });
        }
        if (status === 'approved') {
          pushItem({
            type: 'leave',
            label: 'Leave request approved',
            detail: `${entry?.LeaveType || entry?.leaveType || 'Leave'} approved`,
            dateValue,
            target: 'leave',
          });
        }
        if (status === 'rejected') {
          pushItem({
            type: 'leave',
            label: 'Leave request rejected',
            detail: `${entry?.LeaveType || entry?.leaveType || 'Leave'} rejected`,
            dateValue,
            target: 'leave',
          });
        }
      });

      (Array.isArray(shifts) ? shifts : []).forEach((entry) => {
        const sid = deriveEmpId(entry);
        if (!sid || !myEmpId || String(sid) !== String(myEmpId)) return;

        const status = String(entry?.ShiftSwapStatus || entry?.status || '').toLowerCase();
        const dateValue = entry?.ShiftDate || entry?.shiftDate || entry?.AppliedOn || entry?.appliedOn || new Date();

        if (status === 'pending') {
          pushItem({
            type: 'shift',
            label: 'Shift request submitted',
            detail: `${entry?.ShiftName || entry?.shiftName || 'Shift'} waiting for approval`,
            dateValue,
            target: 'shifts',
          });
        }
        if (status === 'approved') {
          pushItem({
            type: 'shift',
            label: 'Shift request approved',
            detail: `${entry?.ShiftName || entry?.shiftName || 'Shift'} approved`,
            dateValue,
            target: 'shifts',
          });
        }
        if (status === 'rejected') {
          pushItem({
            type: 'shift',
            label: 'Shift request rejected',
            detail: `${entry?.ShiftName || entry?.shiftName || 'Shift'} rejected`,
            dateValue,
            target: 'shifts',
          });
        }
      });

      (Array.isArray(payroll) ? payroll : []).forEach((entry) => {
        const pid = deriveEmpId(entry);
        if (!pid || !myEmpId || String(pid) !== String(myEmpId)) return;
        const dateValue = entry?.PayrollMonth ?? entry?.payrollMonth ?? entry?.month ?? entry?.ProcessedOn ?? entry?.processedOn ?? new Date();
        pushItem({
          type: 'payroll',
          label: 'Payroll processed',
          detail: `Net salary ${entry?.NetSalary ?? entry?.netSalary ?? entry?.NetPay ?? entry?.netPay ?? 'N/A'}`,
          dateValue,
          target: 'payroll',
        });
      });

      return timeline
        .sort((a, b) => new Date(b.dateValue).getTime() - new Date(a.dateValue).getTime())
        .slice(0, 6);
    })();

    const nextLeave = myLeaves.filter((entry) => {
      const status = String(entry?.Status || entry?.status || '').toLowerCase();
      return status === 'pending' || status === 'approved';
    }).slice(0, 2);

    const primaryAction = todaysRecord && (todaysRecord.checkIn || todaysRecord.CheckIn) && !(todaysRecord.checkOut || todaysRecord.CheckOut)
      ? { label: 'Check Out', target: 'attendance' }
      : { label: 'Check In', target: 'attendance' };

    return (
      <div className="space-y-6">
        <div className="relative overflow-hidden rounded-[30px] border border-indigo-200/70 bg-gradient-to-br from-indigo-950 via-violet-950 to-slate-950 p-6 text-white shadow-[0_30px_80px_-28px_rgba(79,70,229,0.7)] dark:border-indigo-900/80">
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(147,197,253,0.22),_transparent_34%),radial-gradient(circle_at_bottom_right,_rgba(34,197,94,0.16),_transparent_32%)]" />
          <div className="relative z-10 flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
            <div className="flex items-start gap-4">
              <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-white/10 ring-1 ring-white/20 backdrop-blur-md">
                <span className="text-xl font-black">{(employeeName || 'E').charAt(0).toUpperCase()}</span>
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-200">Employee command center</div>
                <h3 className="mt-2 text-3xl font-black tracking-tight text-white">Good day, {employeeName.split(' ')[0] || 'Employee'} 👋</h3>
                <div className="mt-3 flex flex-wrap items-center gap-2 text-xs text-indigo-100/80">
                  <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1">{employeeRole}</span>
                  <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1">{employeeDepartment}</span>
                  <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1">{new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-4 rounded-[24px] border border-white/10 bg-white/5 px-4 py-3 backdrop-blur-sm">
              <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-400/15 text-emerald-300">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-400 shadow-[0_0_18px_rgba(52,211,153,0.9)]" />
              </div>
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-100/75">Live status</div>
                <div className="mt-1 text-sm font-bold text-white">{statusLabel === 'Not Checked In' ? 'Ready to start' : statusLabel}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Today</div>
                <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Workday snapshot</h4>
              </div>
              <span className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-700 dark:border-indigo-800 dark:bg-indigo-950/60 dark:text-indigo-300">{workMode}</span>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-[1.2fr_0.8fr]">
              <div className="rounded-[24px] border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950/60">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Attendance status</div>
                    <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{statusLabel === 'Not Checked In' ? 'Ready' : statusLabel}</div>
                  </div>
                  <div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${statusLabel === 'Not Checked In' ? 'bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200' : 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300'}`}>
                    <Clock className="h-5 w-5" />
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                    <span className="text-xs text-slate-500">Check-in</span>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{checkInValue}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                    <span className="text-xs text-slate-500">Check-out</span>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{checkOutValue}</span>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 bg-white px-3 py-2 dark:border-slate-700 dark:bg-slate-900">
                    <span className="text-xs text-slate-500">Hours</span>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{workingHoursValue} hrs</span>
                  </div>
                </div>
              </div>

              <div className="flex flex-col justify-between rounded-[24px] bg-gradient-to-br from-indigo-50 to-violet-50 p-4 ring-1 ring-indigo-100 dark:from-indigo-950/60 dark:to-violet-950/50 dark:ring-indigo-900/60">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">Current shift</div>
                  <div className="mt-2 text-lg font-black text-slate-900 dark:text-white">{myNextShift ? myNextShift.ShiftName || myNextShift.shiftName || 'Shift' : 'No upcoming shift'}</div>
                  <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{myNextShift ? myNextShift.ShiftDate || myNextShift.shiftDate || 'N/A' : 'Not assigned'}</div>
                </div>

                <div className="mt-5 rounded-2xl border border-indigo-200 bg-white/80 p-3 dark:border-indigo-800 dark:bg-slate-900/60">
                  <div className="flex items-center justify-between text-[10px] font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                    <span>Progress</span>
                    <span>{workingHoursValue ? Math.min(100, Math.round((Number(workingHoursValue) / 8) * 100)) : 0}%</span>
                  </div>
                  <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                    <div className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-cyan-500" style={{ width: `${workingHoursValue ? Math.min(100, Math.round((Number(workingHoursValue) / 8) * 100)) : 0}%` }} />
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => onNavigate(primaryAction.target)}
                  className="mt-5 inline-flex items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-bold text-white shadow-[0_18px_28px_-18px_rgba(99,102,241,0.9)] transition hover:translate-y-[-1px]"
                >
                  {primaryAction.label}
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-5">
            <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">My workforce</div>
              <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Personal summary</h4>

              <div className="mt-4 space-y-3">
                <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Attendance rate</div>
                    <div className="mt-1 text-xl font-black text-slate-900 dark:text-white">{attendanceRateEmp}</div>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                    <TrendingUp className="h-5 w-5" />
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Leave balance</div>
                    <div className="mt-1 text-xl font-black text-slate-900 dark:text-white">{leaveBalanceSummary?.casualLeave?.remaining ?? 0} days</div>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-violet-100 text-violet-700 dark:bg-violet-950/60 dark:text-violet-300">
                    <Calendar className="h-5 w-5" />
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Current shift</div>
                    <div className="mt-1 text-xl font-black text-slate-900 dark:text-white">{myNextShift ? myNextShift.ShiftName || myNextShift.shiftName || 'Shift' : 'N/A'}</div>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-sky-100 text-sky-700 dark:bg-sky-950/60 dark:text-sky-300">
                    <Clock className="h-5 w-5" />
                  </div>
                </div>

                <div className="flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Latest salary</div>
                    <div className="mt-1 text-xl font-black text-slate-900 dark:text-white">{latestPayrollDisplay}</div>
                  </div>
                  <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-amber-100 text-amber-700 dark:bg-amber-950/60 dark:text-amber-300">
                    <DollarSign className="h-5 w-5" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">My week</div>
                <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Attendance pattern</h4>
              </div>
              <button type="button" onClick={() => onNavigate('attendance')} className="text-xs font-bold text-indigo-600 dark:text-indigo-300">View calendar</button>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-7">
              {attendanceMap.map((day, index) => {
                const date = new Date(day.date);
                const isWeekend = date.getDay() === 0 || date.getDay() === 6;
                const isHoliday = day.holiday > 0;
                const isLate = day.late > 0;
                const isLeave = day.leave > 0;
                const isPresent = day.present > 0;
                const toneClasses = isHoliday
                  ? 'bg-amber-100 text-amber-700 ring-amber-200 dark:bg-amber-950/60 dark:text-amber-300 dark:ring-amber-800'
                  : isLate
                    ? 'bg-yellow-100 text-yellow-700 ring-yellow-200 dark:bg-yellow-950/60 dark:text-yellow-300 dark:ring-yellow-800'
                    : isLeave
                      ? 'bg-violet-100 text-violet-700 ring-violet-200 dark:bg-violet-950/60 dark:text-violet-300 dark:ring-violet-800'
                      : isWeekend
                        ? 'bg-slate-100 text-slate-700 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700'
                        : isPresent
                          ? 'bg-emerald-100 text-emerald-700 ring-emerald-200 dark:bg-emerald-950/60 dark:text-emerald-300 dark:ring-emerald-800'
                          : 'bg-slate-100 text-slate-600 ring-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:ring-slate-700';

                return (
                  <div key={`${day.date}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-700 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.16em] text-slate-500">{date.toLocaleDateString('en-US', { weekday: 'short' })}</div>
                    <div className={`mt-2 inline-flex h-9 w-9 items-center justify-center rounded-full text-sm font-black ring-1 ${toneClasses}`}>
                      {date.getDate()}
                    </div>
                    <div className="mt-2 text-[9px] font-bold uppercase tracking-[0.12em] text-slate-500">{isHoliday ? 'Holiday' : isLate ? 'Late' : isLeave ? 'Leave' : isWeekend ? 'Off' : isPresent ? 'Present' : 'Working'}</div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Upcoming</div>
                <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Schedule</h4>
              </div>
              <button type="button" onClick={() => onNavigate('shifts')} className="text-xs font-bold text-indigo-600 dark:text-indigo-300">View all</button>
            </div>

            <div className="mt-5 space-y-3">
              {myNextShift ? (
                <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-3 dark:border-indigo-800 dark:bg-indigo-950/50">
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">Next shift</div>
                  <div className="mt-2 text-sm font-black text-slate-900 dark:text-white">{myNextShift.ShiftName || myNextShift.shiftName || 'Shift'}</div>
                  <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{myNextShift.ShiftDate || myNextShift.shiftDate || 'N/A'} • {myNextShift.ShiftStart || myNextShift.shiftStart || 'N/A'} - {myNextShift.ShiftEnd || myNextShift.shiftEnd || 'N/A'}</div>
                </div>
              ) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">No upcoming shift assigned.</div>
              )}

              {nextLeave.length > 0 ? nextLeave.map((entry, index) => (
                <div key={`${entry?.LeaveType || 'leave'}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Approved leave</div>
                  <div className="mt-2 text-sm font-black text-slate-900 dark:text-white">{entry?.LeaveType || entry?.leaveType || 'Leave'}</div>
                  <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{entry?.StartDate || entry?.startDate || 'N/A'} to {entry?.EndDate || entry?.endDate || 'N/A'}</div>
                </div>
              )) : (
                <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">No scheduled leave blocks.</div>
              )}
            </div>
          </div>
        </div>

        <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Leave</div>
                <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Overview</h4>
              </div>
              <button type="button" onClick={() => onNavigate('leave')} className="rounded-xl bg-indigo-600 px-3 py-2 text-xs font-bold text-white">Quick apply</button>
            </div>

            <div className="mt-5 grid gap-3">
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Available leave</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{leaveBalanceSummary?.casualLeave?.remaining ?? 0}</div>
                <div className="text-xs text-slate-600 dark:text-slate-300">Casual leave remaining</div>
              </div>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-950/60">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Pending requests</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{myLeaves.filter((entry) => String(entry?.Status || entry?.status || '').toLowerCase() === 'pending').length}</div>
                <div className="text-xs text-slate-600 dark:text-slate-300">Awaiting review</div>
              </div>
            </div>
          </div>

          <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Payroll</div>
                <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Snapshot</h4>
              </div>
              <div className="rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950/60 dark:text-emerald-300">{myPayroll ? 'Updated' : 'No data'}</div>
            </div>

            <div className="mt-5 rounded-[24px] bg-gradient-to-br from-emerald-50 to-cyan-50 p-4 ring-1 ring-emerald-100 dark:from-emerald-950/40 dark:to-cyan-950/30 dark:ring-emerald-800/60">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700 dark:text-emerald-300">Latest salary</div>
                  <div className="mt-2 text-3xl font-black text-slate-900 dark:text-white">{latestPayrollDisplay}</div>
                </div>
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-emerald-600 shadow-sm dark:bg-slate-900 dark:text-emerald-300">
                  <DollarSign className="h-5 w-5" />
                </div>
              </div>
              <div className="mt-4 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                <span>Period</span>
                <span className="font-bold text-slate-900 dark:text-white">{latestPayrollPeriod}</span>
              </div>
              <div className="mt-2 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                <span>Payment</span>
                <span className="font-bold text-emerald-700 dark:text-emerald-300">{latestPayrollStatus}</span>
              </div>
            </div>
          </div>
        </div>

        <div className="rounded-[30px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.22em] text-slate-500">Recent activity</div>
              <h4 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Smart timeline</h4>
            </div>
            <div className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-600 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-300">Live</div>
          </div>

          <div className="mt-5 space-y-3">
            {recentActivity.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-slate-200 bg-slate-50 p-5 text-center dark:border-slate-700 dark:bg-slate-950/60">
                <div className="text-sm font-bold text-slate-900 dark:text-white">No recent activity yet</div>
                <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">Your attendance, leave, shift, and payroll updates will appear here.</div>
              </div>
            ) : recentActivity.map((item, index) => {
              const icon = item.type === 'attendance'
                ? <CheckCircle2 className="h-4 w-4" />
                : item.type === 'leave'
                  ? <Calendar className="h-4 w-4" />
                  : item.type === 'shift'
                    ? <Clock className="h-4 w-4" />
                    : <DollarSign className="h-4 w-4" />;

              const tone = item.type === 'attendance'
                ? 'bg-emerald-100 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-300'
                : item.type === 'leave'
                  ? 'bg-violet-100 text-violet-600 dark:bg-violet-950/60 dark:text-violet-300'
                  : item.type === 'shift'
                    ? 'bg-sky-100 text-sky-600 dark:bg-sky-950/60 dark:text-sky-300'
                    : 'bg-amber-100 text-amber-600 dark:bg-amber-950/60 dark:text-amber-300';

              return (
                <button
                  key={`${item.label}-${item.dateValue?.getTime?.() || index}`}
                  type="button"
                  onClick={() => onNavigate(item.target || 'attendance')}
                  className="group flex w-full items-start gap-3 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:bg-white hover:shadow-[0_12px_30px_-22px_rgba(79,70,229,0.7)] dark:border-slate-700 dark:bg-slate-950/60 dark:hover:border-indigo-700 dark:hover:bg-slate-900"
                >
                  <div className={`flex h-9 w-9 items-center justify-center rounded-xl ${tone}`}>
                    {icon}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-3">
                      <div className="text-sm font-bold text-slate-900 dark:text-white">{item.label}</div>
                      <ArrowUpRight className="h-4 w-4 text-slate-400 opacity-0 transition group-hover:opacity-100 dark:text-slate-500" />
                    </div>
                    <div className="mt-1 text-xs text-slate-600 dark:text-slate-300">{item.detail}</div>
                  </div>
                  <div className="pt-1 text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">{formatTimelineDate(item.dateValue)}</div>
                </button>
              );
            })}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 p-6 text-white shadow-xl">
        <div className="absolute -right-10 -top-10 h-64 w-64 rounded-full bg-indigo-500/10 blur-3xl" />
        <div className="relative z-10 flex flex-col justify-between gap-4 md:flex-row md:items-center">
          <div>
            <div className="flex items-center gap-2">
              <span className="rounded-md bg-indigo-500/20 px-2.5 py-1 text-xs font-semibold text-indigo-300 backdrop-blur">
                LIVE ENTERPRISE CONTROL CENTER
              </span>
              <span className="flex items-center gap-1 text-xs text-emerald-400">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                Real-time Sync Active
              </span>
            </div>
            <h2 className="mt-2 text-2xl font-bold tracking-tight sm:text-3xl">
              Workforce Intelligence Overview
            </h2>
            <p className="mt-1 max-w-2xl text-xs text-slate-300">
              Live workforce coverage, leave approvals, payroll status, and frontline operational insights generated from the connected backend data source.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={onOpenAIChat}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 px-4 py-2.5 text-xs font-bold shadow-lg shadow-indigo-500/30 transition hover:opacity-95"
            >
              <Sparkles className="h-4 w-4" />
              Ask AI Assistant
            </button>
            <button
              onClick={() => onNavigate('reports')}
              className="flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-800/80 px-4 py-2.5 text-xs font-semibold backdrop-blur transition hover:bg-slate-700"
            >
              <FileSpreadsheet className="h-4 w-4" />
              Executive Report
            </button>
          </div>
        </div>
      </div>

      {dashboardError && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200">
          Dashboard metrics unavailable: {dashboardError}
        </div>
      )}

      {dashboardLoading && !dashboardMetrics && (
        <div className="rounded-xl border border-slate-200 bg-white p-3 text-xs text-slate-600 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300">
          Loading dashboard metrics...
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {/* KPI 1: Headcount */}
        <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-indigo-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-indigo-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Active Headcount</span>
            <div className="rounded-xl bg-indigo-50 p-2.5 text-indigo-600 transition-transform duration-300 group-hover:scale-110 dark:bg-indigo-950/60 dark:text-indigo-400">
              <Users className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">{totalEmployees}</span>
            <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">Live directory</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            {activeCount} active employee records synced
          </p>
        </div>

        {/* KPI 2: Attendance Rate */}
        <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-emerald-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-emerald-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Today's Attendance</span>
            <div className="rounded-xl bg-emerald-50 p-2.5 text-emerald-600 transition-transform duration-300 group-hover:scale-110 dark:bg-emerald-950/60 dark:text-emerald-400">
              <Clock className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">{attendanceRate}</span>
            <span className="text-[10px] font-bold text-emerald-600">{attendanceRate === 'N/A' ? 'Unavailable' : 'Live Data'}</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Verified (method)
          </p>
        </div>

        {/* KPI 3: Pending Leaves */}
        <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-amber-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-amber-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Pending Leave Requests</span>
            <div className="rounded-xl bg-amber-50 p-2.5 text-amber-600 transition-transform duration-300 group-hover:scale-110 dark:bg-amber-950/60 dark:text-amber-400">
              <Calendar className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">
              {Number.isFinite(Number(metrics.pendingLeaveRequests)) ? `${pendingLeaveRequests} Pending` : 'N/A'}
            </span>
            <span className="text-[10px] font-bold text-amber-600">Action Required</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Requires Manager Approval
          </p>
        </div>

        {/* KPI 4: Projected Payroll */}
        <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-blue-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-blue-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">August Payroll Est.</span>
            <div className="rounded-xl bg-blue-50 p-2.5 text-blue-600 transition-transform duration-300 group-hover:scale-110 dark:bg-blue-950/60 dark:text-blue-400">
              <DollarSign className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">{payrollValue}</span>
            <span className="text-[10px] font-bold text-slate-500">{Number.isFinite(Number(metrics.totalMonthlyPayroll)) ? 'Auto Calculated' : 'Unavailable'}</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            {Number.isFinite(Number(metrics.totalMonthlyPayroll)) ? 'Live monthly payroll total' : 'Payroll data unavailable'}
          </p>
        </div>

        {/* KPI 5: Productivity Score */}
        <div className="group rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:border-purple-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-purple-700">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 dark:text-slate-400">Productivity Score</span>
            <div className="rounded-xl bg-purple-50 p-2.5 text-purple-600 transition-transform duration-300 group-hover:scale-110 dark:bg-purple-950/60 dark:text-purple-400">
              <TrendingUp className="h-4 w-4" />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span className="text-2xl font-black text-slate-900 dark:text-white">{metrics.productivityScore ?? 'N/A'}</span>
            <span className="text-[10px] font-bold text-slate-500 dark:text-slate-400">{metrics.productivityScore ? 'Live score' : 'Unavailable'}</span>
          </div>
          <p className="mt-1 text-[11px] text-slate-500 dark:text-slate-400">
            Workforce productivity signal from current data
          </p>
        </div>
      </div>

      {/* AI Intelligence Briefing Banner */}
      <div className="group flex flex-col items-start justify-between gap-4 rounded-2xl border border-purple-200/80 bg-gradient-to-r from-purple-50 via-indigo-50/50 to-white p-4.5 shadow-sm transition-all duration-300 hover:shadow-md hover:border-purple-300 md:flex-row md:items-center dark:border-purple-900/50 dark:from-purple-950/40 dark:via-indigo-950/30 dark:to-slate-900">
        <div className="flex items-start gap-3">
          <div className="mt-0.5 rounded-xl bg-purple-600 p-2.5 text-white shadow-md shadow-purple-500/20 transition-transform duration-300 group-hover:scale-105">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-xs font-extrabold text-purple-950 dark:text-purple-200 tracking-wide">
                AI PREDICTIVE WORKFORCE BRIEFING (GEMINI 3.6 FLASH)
              </h3>
              <span className="rounded-full bg-purple-200 px-2 py-0.5 text-[9px] font-bold text-purple-800 dark:bg-purple-900 dark:text-purple-200">
                RAG Engine
              </span>
            </div>
            <p className="mt-1 text-xs text-slate-700 dark:text-slate-300 font-medium">
              {pendingShiftRequests > 0 || attritionRiskCount > 0
                ? `${pendingShiftRequests} shift review item(s) are pending and ${attritionRiskCount} employee(s) are flagged by the predictive model.`
                : 'The current workforce snapshot is stable. No additional action items require review from the live backend signal.'}
            </p>
          </div>
        </div>
        <button
          onClick={() => onNavigate('ai_planning')}
          className="whitespace-nowrap rounded-xl bg-purple-600 px-4 py-2.5 text-xs font-bold text-white shadow-sm transition-all duration-200 hover:bg-purple-700 hover:shadow-md"
        >
          View Workforce Analytics
        </button>
      </div>

      {/* Main Analytics Grid */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Simplified & Clean Departmental Attendance */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md lg:col-span-2 dark:border-slate-800/80 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                Departmental Attendance Overview
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Simplified live attendance rates across organization units
              </p>
            </div>
            <button
              onClick={() => onNavigate('attendance')}
              className="text-xs font-bold text-indigo-600 transition-colors hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              View Full Logs →
            </button>
          </div>

          <div className="mt-5 space-y-4">
            {attendance && attendance.length > 0 ? (
              <div className="group rounded-xl border border-slate-100 bg-slate-50/60 p-3.5 transition-all duration-200 hover:border-indigo-200 hover:bg-indigo-50/20 dark:border-slate-800/60 dark:bg-slate-800/30 dark:hover:border-indigo-800/50">
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-900 dark:text-white">Live attendance snapshot</span>
                    <span className="text-[10px] text-slate-400">({attendance.length} records)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-emerald-600 dark:text-emerald-400 text-xs">{attendanceLiveRate} Present</span>
                  </div>
                </div>

                <div className="mt-2.5 flex items-center gap-3">
                  <div className="h-2 w-full overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-800">
                    <div
                      style={{ width: attendanceLiveRate === 'N/A' ? '0%' : attendanceLiveRate }}
                      className="h-full rounded-full bg-indigo-600 transition-all duration-500 group-hover:bg-indigo-500"
                    />
                  </div>
                  <span className="text-[10px] font-medium text-slate-500 whitespace-nowrap">
                    {attendanceSummary.late > 0 ? `${attendanceSummary.late} late` : 'No late entries'}
                  </span>
                </div>
              </div>
            ) : (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800/40 dark:text-slate-300">
                Attendance data is not available yet for the selected period.
              </div>
            )}
          </div>

          {/* Attendance status highlights */}
          <div className="mt-5 grid grid-cols-3 gap-3 rounded-xl border border-slate-100 bg-slate-50/80 p-3 text-center dark:border-slate-800/60 dark:bg-slate-800/40">
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Present</div>
              <div className="mt-0.5 text-sm font-black text-slate-900 dark:text-white">{attendanceSummary.present || 0}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Late</div>
              <div className="mt-0.5 text-sm font-black text-slate-900 dark:text-white">{attendanceSummary.late || 0}</div>
            </div>
            <div>
              <div className="text-[10px] font-bold text-slate-400 uppercase">Absent / Leave</div>
              <div className="mt-0.5 text-sm font-black text-slate-900 dark:text-white">{(attendanceSummary.absent || 0) + (attendanceSummary.leave || 0)}</div>
            </div>
          </div>
        </div>

        {/* Top Performing Workforce Spotlight */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
            <div>
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
                Top Performers
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400">
                Current workforce snapshot
              </p>
            </div>
            <span className="rounded-full bg-indigo-100 px-2.5 py-0.5 text-[10px] font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
              Live Directory
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {employees
              .slice(0, 3)
              .map((emp, idx) => {
                const rowKey = emp?.empId || `emp-${idx}`;
                const locationPart = typeof emp?.location === 'string' && emp.location.trim() !== ''
                  ? emp.location.split('-')[0]
                  : (emp?.location || 'N/A');

                const avatar = emp?.avatar && typeof emp.avatar === 'string' && emp.avatar.trim() !== '' ? emp.avatar : null;

                return (
                <div
                  key={rowKey}
                  className="group rounded-xl border border-slate-100 bg-slate-50/50 p-3 transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-sm dark:border-slate-800/60 dark:bg-slate-800/30 dark:hover:border-indigo-800"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      {avatar ? (
                        <img src={avatar} alt={emp?.firstName || ''} className="h-9 w-9 rounded-full object-cover ring-2 ring-indigo-500/20" />
                      ) : (
                        <div className="h-9 w-9 rounded-full bg-indigo-100 flex items-center justify-center font-bold text-indigo-700">{emp?.firstName?.[0] || emp?.empId?.slice(-2) || 'NA'}</div>
                      )}
                      <div>
                        <div className="text-xs font-bold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                          {emp?.firstName || ''} {emp?.lastName || ''}
                        </div>
                        <div className="text-[10px] text-slate-500 dark:text-slate-400">
                          {emp?.jobRole || '—'} • {emp?.department || '—'}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-xs font-black text-slate-700 dark:text-slate-200">
                        {emp?.employmentStatus || emp?.EmploymentStatus || 'Active'}
                      </div>
                      <div className="text-[10px] text-slate-400">{locationPart}</div>
                    </div>
                  </div>
                </div>
                );
              })}
          </div>

          <button
            onClick={() => onNavigate('employees')}
            className="mt-4 w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-center text-xs font-bold text-slate-700 transition-all hover:border-indigo-300 hover:bg-indigo-50/50 hover:text-indigo-700 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-700"
          >
            View All Directory →
          </button>
        </div>
      </div>

      {/* Quick Actions & Recent Requests */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
            <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">
              Pending Approvals Queue ({pendingApprovalQueue.length})
            </h3>
            <button onClick={() => onNavigate('leave')} className="text-xs font-bold text-indigo-600 transition-colors hover:text-indigo-700 dark:text-indigo-400">
              View All →
            </button>
          </div>

          <div className="mt-4 space-y-3">
            {pendingApprovalQueue.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800/40 dark:text-slate-300">
                No pending approvals at the moment.
              </div>
            ) : pendingApprovalQueue.map((item, idx) => (
              <div
                key={item.id || `${item.type}-${idx}`}
                className="group flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/70 p-3.5 transition-all duration-200 hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-sm dark:border-slate-800/60 dark:bg-slate-800/40 dark:hover:border-amber-900"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded-xl bg-amber-100 p-2.5 text-amber-600 transition-transform duration-200 group-hover:scale-110 dark:bg-amber-950 dark:text-amber-400">
                    {item.type === 'Shift' ? <Zap className="h-4 w-4" /> : item.type === 'Payroll' ? <DollarSign className="h-4 w-4" /> : <Calendar className="h-4 w-4" />}
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900 dark:text-white">
                      <span className="truncate">{item.label || 'Employee'}</span>
                      <span className="rounded-full bg-slate-200 px-1.5 py-0.5 text-[9px] uppercase tracking-wide text-slate-600 dark:bg-slate-700 dark:text-slate-200">{item.type}</span>
                    </div>
                    <div className="mt-1 text-[11px] text-slate-500 dark:text-slate-300">
                      {item.detail}
                    </div>
                    <div className="mt-1 text-[10px] uppercase tracking-[0.12em] text-slate-400">
                      {item.status}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => onNavigate(item.route || 'leave')}
                    className="rounded-lg bg-emerald-600 px-3 py-1.5 text-[11px] font-bold text-white shadow-sm transition-all hover:bg-emerald-700 hover:shadow"
                  >
                    Review
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 dark:border-slate-800">
              <h3 className="text-sm font-extrabold text-slate-900 dark:text-white">Upcoming Holidays</h3>
              <button onClick={() => onNavigate('attendance')} className="text-xs font-bold text-indigo-600 transition-colors hover:text-indigo-700 dark:text-indigo-400">
                Calendar →
              </button>
            </div>

            <div className="mt-4 space-y-3">
              {holidaysLoading ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800/40 dark:text-slate-300">
                  Loading holiday schedule...
                </div>
              ) : holidaysError ? (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200">
                  {holidaysError}
                </div>
              ) : upcomingHolidays.length === 0 ? (
                <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800/40 dark:text-slate-300">
                  No upcoming holidays scheduled.
                </div>
              ) : upcomingHolidays.map((holiday) => (
                <div key={`${holiday.label}-${holiday.dateText}`} className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50/70 p-3 dark:border-slate-800/60 dark:bg-slate-800/40">
                  <div>
                    <div className="text-xs font-bold text-slate-900 dark:text-white">{holiday.label}</div>
                    <div className="mt-1 text-[10px] uppercase tracking-[0.14em] text-slate-400">{holiday.dateText}</div>
                  </div>
                  <div className="rounded-full bg-emerald-100 px-2 py-1 text-[10px] font-bold text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
                    Upcoming
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900">
            <h3 className="border-b border-slate-100 pb-3.5 text-sm font-extrabold text-slate-900 dark:border-slate-800 dark:text-white">
              Automated HR Shortcuts
            </h3>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <button
                onClick={() => onNavigate('employees')}
                className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-400 hover:bg-indigo-50/40 hover:shadow-sm dark:border-slate-800/80 dark:bg-slate-800/50 dark:hover:border-indigo-700"
              >
                <div className="rounded-xl bg-indigo-100 p-2.5 text-indigo-600 transition-transform duration-200 group-hover:scale-110 dark:bg-indigo-950 dark:text-indigo-300">
                  <UserPlus className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Onboard Staff</div>
                  <div className="text-[10px] text-slate-500">Lifecycle & RBAC</div>
                </div>
              </button>

              <button
                onClick={() => onNavigate('payroll')}
                className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-blue-400 hover:bg-blue-50/40 hover:shadow-sm dark:border-slate-800/80 dark:bg-slate-800/50 dark:hover:border-blue-700"
              >
                <div className="rounded-xl bg-blue-100 p-2.5 text-blue-600 transition-transform duration-200 group-hover:scale-110 dark:bg-blue-950 dark:text-blue-300">
                  <DollarSign className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Run Payroll</div>
                  <div className="text-[10px] text-slate-500">Auto OT & Deductions</div>
                </div>
              </button>

              <button
                onClick={() => onNavigate('shifts')}
                className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-purple-400 hover:bg-purple-50/40 hover:shadow-sm dark:border-slate-800/80 dark:bg-slate-800/50 dark:hover:border-purple-700"
              >
                <div className="rounded-xl bg-purple-100 p-2.5 text-purple-600 transition-transform duration-200 group-hover:scale-110 dark:bg-purple-950 dark:text-purple-300">
                  <Zap className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Rotational Shifts</div>
                  <div className="text-[10px] text-slate-500">Swap & Overtime</div>
                </div>
              </button>

              <button
                onClick={() => onNavigate('reports')}
                className="group flex items-center gap-3 rounded-xl border border-slate-200/80 bg-slate-50/80 p-3.5 text-left transition-all duration-200 hover:-translate-y-0.5 hover:border-emerald-400 hover:bg-emerald-50/40 hover:shadow-sm dark:border-slate-800/80 dark:bg-slate-800/50 dark:hover:border-emerald-700"
              >
                <div className="rounded-xl bg-emerald-100 p-2.5 text-emerald-600 transition-transform duration-200 group-hover:scale-110 dark:bg-emerald-950 dark:text-emerald-300">
                  <FileSpreadsheet className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-900 dark:text-white">Analytics Center</div>
                  <div className="text-[10px] text-slate-500">Snowflake Exports</div>
                </div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
