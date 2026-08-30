import React, { useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  CalendarClock,
  CalendarDays,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Filter,
  MapPin,
  Search,
  Sparkles,
  TrendingUp,
  Users,
  X,
} from 'lucide-react';

const toText = (...values) => {
  for (const value of values) {
    if (value === null || value === undefined) continue;
    const text = String(value).trim();
    if (text && text !== 'null' && text !== 'undefined' && text !== 'N/A' && text !== 'n/a') {
      return text;
    }
  }
  return '';
};

const toNumber = (value) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : 0;
};

const getEmployeeId = (record) => toText(record?.empId, record?.EmpID, record?.EmpId, record?.employeeId);
const getDepartment = (record) => toText(record?.department, record?.Department, record?.dept, 'Unassigned');

const getEmployeeName = (record, employees = []) => {
  const recordEmpId = getEmployeeId(record);
  const employee = (employees || []).find((item) => {
    const id = toText(item?.empId, item?.EmpID, item?.EmpId, item?.employeeId);
    return id && recordEmpId && id.toLowerCase() === recordEmpId.toLowerCase();
  });

  if (employee) {
    const composed = `${toText(employee?.firstName, employee?.FirstName)} ${toText(employee?.lastName, employee?.LastName)}`.trim();
    if (composed) return composed;
  }

  const first = toText(record?.empName, record?.EmployeeName, record?.employeeName);
  if (first) return first;
  return recordEmpId || 'Employee';
};

const getInitials = (record) => {
  const name = getEmployeeName(record);
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('') || 'NA';
};

const toISODateLocal = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const formatDate = (value) => {
  const text = toText(value);
  if (!text) return '—';
  const parsed = new Date(`${text}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return text;
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(parsed);
};

const formatTime = (value) => {
  const text = toText(value);
  if (!text) return '—';
  if (text.length <= 5 && text.includes(':')) return text;
  const parsed = new Date(text);
  if (!Number.isNaN(parsed.getTime())) {
    return parsed.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    });
  }
  return text;
};

const formatHours = (value) => {
  const numeric = toNumber(value);
  if (numeric <= 0 && value !== 0 && value !== '0') return '—';
  return `${numeric.toFixed(numeric % 1 === 0 ? 0 : 2)} hrs`;
};

const normalizeHolidayDate = (value) => {
  const text = toText(value);
  if (!text) return null;
  const parsed = new Date(`${text}T00:00:00`);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed;
};

const toDateKey = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const parseLocalDateKey = (value) => {
  const parsed = normalizeHolidayDate(value);
  if (!parsed) return null;
  return toDateKey(parsed);
};

const getAttendanceStatus = (record) => {
  const raw = toText(record?.status, record?.AttendanceStatus, record?.attendanceStatus, record?.Status).toLowerCase();
  const isLate = record?.LateArrival === true || record?.lateArrival === true || raw === 'late';
  const hasCheckIn = Boolean(record?.checkIn || record?.CheckIn || record?.checkin || record?.CheckInTime);
  const hasCheckOut = Boolean(record?.checkOut || record?.CheckOut || record?.checkout);

  if (isLate) return 'Late';
  if (raw === 'present' || raw === 'checked out' || raw === 'day completed' || raw === 'complete') return 'Present';
  if (raw === 'working' || raw === 'currently working' || raw === 'in progress') return 'Working';
  if (raw === 'absent' || raw === 'not checked in' || raw === 'no show' || raw === 'no-show') return 'Absent';
  if (hasCheckIn && !hasCheckOut) return 'Working';
  if (hasCheckIn && hasCheckOut) return 'Present';
  return 'Absent';
};

const getStatusClasses = (status) => {
  const value = (status || 'Absent').toLowerCase();
  if (value === 'present') {
    return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-900';
  }
  if (value === 'late') {
    return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-900';
  }
  if (value === 'working') {
    return 'bg-sky-50 text-sky-700 ring-1 ring-sky-200 dark:bg-sky-950/50 dark:text-sky-300 dark:ring-sky-900';
  }
  return 'bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:ring-rose-900';
};

const DetailBlock = ({ label, value, tone = 'text-slate-700 dark:text-slate-200' }) => (
  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-3 dark:border-slate-800 dark:bg-slate-950/60">
    <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">{label}</div>
    <div className={`mt-1 text-sm font-semibold ${tone}`}>{value}</div>
  </div>
);

export const AttendanceManagement = ({
  attendanceRecords = [],
  attendanceLoading = false,
  attendanceError = null,
  attendancePagination = null,
  attendanceSummary = null,
  employees = [],
  holidays = [],
  holidaysLoading = false,
  holidaysError = null,
  selectedEmployeeId,
  userRole = 'HR_ADMIN',
  gpsStatus = { state: 'idle', message: 'Location check will run before attendance is recorded.', distance: null },
  onAttendanceFiltersChange = null,
  onResetAttendanceFilters = null,
  attendanceFilters = {},
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRecord, setSelectedRecord] = useState(null);

  const normalizedList = useMemo(() => {
    const records = Array.isArray(attendanceRecords) ? attendanceRecords : [];
    return records
      .filter((record) => Boolean(toText(record?.date, record?.Date, record?.workDate)))
      .sort((left, right) => {
        const leftDate = toText(left?.date, left?.Date, left?.workDate);
        const rightDate = toText(right?.date, right?.Date, right?.workDate);
        return rightDate.localeCompare(leftDate);
      });
  }, [attendanceRecords]);

  const departmentOptions = useMemo(() => {
    const values = new Set();
    normalizedList.forEach((record) => {
      const department = getDepartment(record);
      if (department && department !== 'Unassigned') values.add(department);
    });
    (employees || []).forEach((employee) => {
      const department = toText(employee?.department, employee?.Department);
      if (department) values.add(department);
    });
    return Array.from(values).sort();
  }, [normalizedList, employees]);

  const filteredRecords = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();
    const selectedStatus = (attendanceFilters?.status || 'ALL').toString();
    const selectedDepartment = toText(attendanceFilters?.department || 'ALL');
    const startDate = toText(attendanceFilters?.startDate);
    const endDate = toText(attendanceFilters?.endDate);

    return normalizedList.filter((record) => {
      const employeeName = getEmployeeName(record, employees).toLowerCase();
      const employeeId = getEmployeeId(record).toLowerCase();
      const department = getDepartment(record).toLowerCase();
      const recordDate = toText(record?.date, record?.Date).toLowerCase();
      const status = getAttendanceStatus(record);
      const hasAttendance = Boolean(toText(record?.checkIn, record?.CheckIn, record?.checkin, record?.CheckInTime));

      const matchesSearch =
        !query ||
        employeeName.includes(query) ||
        employeeId.includes(query) ||
        department.includes(query) ||
        status.toLowerCase().includes(query);

      const matchesDepartment = selectedDepartment === 'ALL' || department === selectedDepartment.toLowerCase();
      const matchesStatus = selectedStatus === 'ALL' || status === selectedStatus;
      const matchesStart = !startDate || recordDate >= startDate;
      const matchesEnd = !endDate || recordDate <= endDate;

      return hasAttendance && matchesSearch && matchesDepartment && matchesStatus && matchesStart && matchesEnd;
    });
  }, [normalizedList, employees, searchQuery, attendanceFilters]);

  const metricsTodayKey = toISODateLocal(new Date());
  const todayRecords = useMemo(
    () => filteredRecords.filter((record) => {
      const recordDate = toText(record?.date, record?.Date, record?.workDate).slice(0, 10);
      return recordDate === metricsTodayKey;
    }),
    [filteredRecords, metricsTodayKey]
  );

  const uniqueTodayRecords = useMemo(() => {
    const byEmployee = new Map();
    todayRecords.forEach((record) => {
      const employeeId = getEmployeeId(record);
      if (!employeeId) return;
      const current = byEmployee.get(employeeId);
      if (!current) {
        byEmployee.set(employeeId, record);
        return;
      }
      // Prefer the most actionable status when duplicate same-day records exist.
      const priority = { Late: 3, Working: 2, Present: 1 };
      if ((priority[getAttendanceStatus(record)] || 0) > (priority[getAttendanceStatus(current)] || 0)) {
        byEmployee.set(employeeId, record);
      }
    });
    return Array.from(byEmployee.values());
  }, [todayRecords]);

  const totalEmployeeCount = useMemo(() => {
    const employeeList = Array.isArray(employees) ? employees : [];
    if (employeeList.length > 0) return employeeList.length;
    if (attendancePagination && Number.isFinite(attendancePagination.total)) return attendancePagination.total;
    const uniqueIds = new Set();
    normalizedList.forEach((record) => {
      const id = getEmployeeId(record);
      if (id) uniqueIds.add(id);
    });
    return uniqueIds.size || normalizedList.length || 0;
  }, [employees, attendancePagination, normalizedList]);

  // The server rollup is computed over the entire filtered result set. The page-derived counts
  // below only see the rows the table requested (50 by default), which is less than a single day
  // for a mid-sized team, so they under-report. Prefer the rollup, and fall back to the page when
  // it is missing or when a client-side search is narrowing the view: the server cannot know
  // about the search box, so letting it answer then would ignore the user's filter.
  const summaryToday = useMemo(() => {
    if (searchQuery.trim()) return null;
    const today = attendanceSummary?.today;
    if (!today || typeof today.attended !== 'number') return null;
    return today;
  }, [attendanceSummary, searchQuery]);

  const presentCount = useMemo(
    () => (summaryToday
      // The rollup counts late arrivals inside `present`; the cards show them separately.
      ? Math.max(0, (summaryToday.present || 0) - (summaryToday.late || 0))
      : uniqueTodayRecords.filter((record) => getAttendanceStatus(record) === 'Present').length),
    [summaryToday, uniqueTodayRecords]
  );
  const lateCount = useMemo(
    () => (summaryToday
      ? (summaryToday.late || 0)
      : uniqueTodayRecords.filter((record) => getAttendanceStatus(record) === 'Late').length),
    [summaryToday, uniqueTodayRecords]
  );
  const workingCount = summaryToday
    ? (summaryToday.currentlyWorking || 0)
    : uniqueTodayRecords.filter((record) => getAttendanceStatus(record) === 'Working').length;
  const absentCount = Math.max(0, totalEmployeeCount - presentCount - workingCount - lateCount);
  const attendanceRate = totalEmployeeCount > 0 ? ((presentCount + workingCount + lateCount) / totalEmployeeCount) * 100 : 0;
  const attendanceRateText = `${Math.min(100, Math.max(0, attendanceRate)).toFixed(0)}%`;

  const checkInCompletionRate = attendanceRate;
  const reviewQueueCount = Math.max(0, absentCount + lateCount); 

  const chartData = [
    { label: 'Present', value: presentCount, color: '#10b981' },
    { label: 'Working', value: workingCount, color: '#38bdf8' },
    { label: 'Late', value: lateCount, color: '#f59e0b' },
    { label: 'Absent', value: absentCount, color: '#ef4444' },
  ].filter((item) => item.value > 0 || item.label === 'Absent');

  const totalChartValue = Math.max(1, chartData.reduce((sum, item) => sum + item.value, 0));
  const donutGradient = (() => {
    let current = 0;
    const segments = chartData.map((segment) => {
      const start = current;
      const percent = (segment.value / totalChartValue) * 100;
      current += percent;
      return `${segment.color} ${start}% ${current}%`;
    });
    return `conic-gradient(${segments.join(', ')})`;
  })();

  const trendData = useMemo(() => {
    const formatLabel = (date) => {
      const parsed = new Date(`${String(date).slice(0, 10)}T00:00:00`);
      if (Number.isNaN(parsed.getTime())) return String(date);
      return parsed.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    // Prefer the server's per-day rollup: it spans every attendance day in the filtered set,
    // whereas the page fallback below can only ever see the newest 50 records.
    const serverTrend = Array.isArray(attendanceSummary?.dailyTrend) ? attendanceSummary.dailyTrend : null;
    if (serverTrend && serverTrend.length > 0 && !searchQuery.trim()) {
      return serverTrend
        .slice(-7)
        .map((point) => ({
          label: formatLabel(point?.date),
          value: Number(point?.attended) || 0,
          present: Number(point?.present) || 0,
          late: Number(point?.late) || 0,
          working: Number(point?.working) || 0,
        }));
    }

    const counts = new Map();
    normalizedList.forEach((record) => {
      const date = toText(record?.date, record?.Date);
      if (!date) return;
      const status = getAttendanceStatus(record);
      if (status === 'Present' || status === 'Working' || status === 'Late') {
        counts.set(date, (counts.get(date) || 0) + 1);
      }
    });

    return Array.from(counts.entries())
      .sort(([a], [b]) => new Date(a) - new Date(b))
      .slice(-7)
      .map(([date, value]) => ({
        label: formatLabel(date),
        value,
      }));
  }, [normalizedList, attendanceSummary, searchQuery]);

  const maxTrendValue = Math.max(...trendData.map((point) => point.value), 1);

  const departmentData = useMemo(() => {
    // Same reasoning as the trend: the server counts every record in the filtered set, the page
    // fallback only the rows currently loaded.
    const serverMix = Array.isArray(attendanceSummary?.departmentBreakdown) ? attendanceSummary.departmentBreakdown : null;
    if (serverMix && serverMix.length > 0 && !searchQuery.trim()) {
      return serverMix
        .slice(0, 5)
        .map((entry) => ({ label: toText(entry?.department) || 'Unassigned', value: Number(entry?.count) || 0 }));
    }

    const counts = new Map();
    normalizedList.forEach((record) => {
      const department = getDepartment(record);
      if (department && department !== 'Unassigned') counts.set(department, (counts.get(department) || 0) + 1);
    });
    return Array.from(counts.entries())
      .map(([label, value]) => ({ label, value }))
      .sort((a, b) => b.value - a.value)
      .slice(0, 5);
  }, [normalizedList, attendanceSummary, searchQuery]);

  const maxDeptValue = Math.max(...departmentData.map((item) => item.value), 1);

  const automationSignals = useMemo(() => {
    const anomalies = uniqueTodayRecords.filter((record) => record?.isAnomaly || record?.anomalyReason || record?.AnomalyReason || getAttendanceStatus(record) === 'Late');
    return anomalies.slice(0, 3).map((record) => ({
      title: 'Attendance anomaly',
      tag: 'AI',
      tone: 'bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300',
      message: toText(record?.anomalyReason, record?.AnomalyReason, `${getEmployeeName(record, employees)} requires review for irregular check-in or check-out behavior.`),
    }));
  }, [uniqueTodayRecords, employees]);

  const metrics = [
    { label: 'Total Employees', value: totalEmployeeCount, delta: 'Live', accent: 'bg-indigo-50 text-indigo-600 dark:bg-indigo-950/50 dark:text-indigo-300', icon: <Users className="h-4 w-4" /> },
    { label: 'Present Today', value: presentCount, delta: 'Today', accent: 'bg-emerald-50 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-300', icon: <CheckCircle2 className="h-4 w-4" /> },
    { label: 'Absent Today', value: absentCount, delta: 'Review', accent: 'bg-rose-50 text-rose-600 dark:bg-rose-950/50 dark:text-rose-300', icon: <AlertTriangle className="h-4 w-4" /> },
    { label: 'Late Arrivals', value: lateCount, delta: 'Alert', accent: 'bg-amber-50 text-amber-600 dark:bg-amber-950/50 dark:text-amber-300', icon: <Clock3 className="h-4 w-4" /> },
  ];

  const today = new Date();
  const todayKey = toDateKey(new Date(today.getFullYear(), today.getMonth(), today.getDate()));

  const holidayEntries = useMemo(() => {
    const list = Array.isArray(holidays) ? holidays : [];
    return [...list]
      .map((holiday) => {
        const name = toText(holiday?.name, holiday?.Name, 'Holiday');
        const date = toText(holiday?.date, holiday?.Date, holiday?.day, holiday?.holidayDate);
        const normalizedDate = parseLocalDateKey(date);
        const type = toText(holiday?.type, holiday?.Type, holiday?.category, 'public');
        return {
          ...holiday,
          id: toText(holiday?.id, holiday?._id, `${date || 'holiday'}-${name}`),
          name,
          date: normalizedDate || date,
          type: type.toLowerCase(),
          isOptional: Boolean(holiday?.isOptional ?? holiday?.is_optional ?? (type.toLowerCase() === 'optional')),
          isWorkingDayOverride: Boolean(holiday?.isWorkingDayOverride ?? holiday?.is_working_day_override ?? false),
        };
      })
      .filter((holiday) => holiday.date)
      .sort((a, b) => {
        const first = normalizeHolidayDate(a.date)?.getTime() ?? 0;
        const second = normalizeHolidayDate(b.date)?.getTime() ?? 0;
        return first - second;
      });
  }, [holidays, today, todayKey]);

  const [calendarMonth, setCalendarMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [selectedCalendarDate, setSelectedCalendarDate] = useState(new Date(today.getFullYear(), today.getMonth(), today.getDate()));

  const holidaysForSelectedMonth = useMemo(() => {
    const year = calendarMonth.getFullYear();
    const monthIndex = calendarMonth.getMonth();
    return holidayEntries.filter((holiday) => {
      const parsed = normalizeHolidayDate(holiday.date);
      return parsed && parsed.getFullYear() === year && parsed.getMonth() === monthIndex;
    });
  }, [calendarMonth, holidayEntries]);

  const holidayToday = useMemo(() => {
    return holidayEntries.find((holiday) => parseLocalDateKey(holiday.date) === todayKey) || null;
  }, [holidayEntries, todayKey]);

  const calendarHolidayMarkers = useMemo(() => {
    const map = new Map();
    holidayEntries.forEach((holiday) => {
      const date = parseLocalDateKey(holiday.date);
      if (date) map.set(date, holiday);
    });
    return map;
  }, [holidayEntries]);

  const holidayMap = calendarHolidayMarkers;

  const selectedCalendarKey = useMemo(() => {
    const year = selectedCalendarDate.getFullYear();
    const month = String(selectedCalendarDate.getMonth() + 1).padStart(2, '0');
    const day = String(selectedCalendarDate.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  }, [selectedCalendarDate]);

  const selectedDayStats = useMemo(() => {
    const records = normalizedList.filter((record) => {
      const date = toText(record?.date, record?.Date);
      return date === selectedCalendarKey;
    });
    const present = records.filter((record) => ['Present', 'Working'].includes(getAttendanceStatus(record))).length;
    const late = records.filter((record) => getAttendanceStatus(record) === 'Late').length;
    const absent = records.filter((record) => getAttendanceStatus(record) === 'Absent').length;
    const holiday = holidayMap.get(selectedCalendarKey) || null;
    const isWeekend = [0, 6].includes(selectedCalendarDate.getDay());
    return {
      records,
      present,
      late,
      absent,
      holiday,
      isWeekend,
    };
  }, [normalizedList, selectedCalendarKey, holidayMap, selectedCalendarDate]);

  const calendarDays = useMemo(() => {
    const monthStart = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
    const startOffset = (monthStart.getDay() + 6) % 7;
    const startDate = new Date(monthStart);
    startDate.setDate(monthStart.getDate() - startOffset);

    const cells = [];
    for (let index = 0; index < 42; index += 1) {
      const date = new Date(startDate);
      date.setDate(startDate.getDate() + index);
      const iso = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
      const isCurrentMonth = date.getMonth() === calendarMonth.getMonth();
      const isToday = iso === todayKey;
      const isSelected = iso === selectedCalendarKey;
      const holiday = holidayMap.get(iso) || null;
      const weekend = [0, 6].includes(date.getDay());
      const hasAttendance = normalizedList.some((record) => toText(record?.date, record?.Date) === iso);
      cells.push({ date, iso, isCurrentMonth, isToday, isSelected, holiday, weekend, hasAttendance });
    }
    return cells;
  }, [calendarMonth, holidayMap, normalizedList, selectedCalendarKey, todayKey]);

  const upcomingHolidays = useMemo(() => {
    return [...holidayEntries]
      .filter((holiday) => {
        const holidayKey = normalizeHolidayDate(holiday.date) ? toDateKey(normalizeHolidayDate(holiday.date)) : null;
        return Boolean(holidayKey && holidayKey > todayKey);
      })
      .sort((a, b) => {
        const aKey = normalizeHolidayDate(a.date) ? toDateKey(normalizeHolidayDate(a.date)) : '9999-12-31';
        const bKey = normalizeHolidayDate(b.date) ? toDateKey(normalizeHolidayDate(b.date)) : '9999-12-31';
        return aKey.localeCompare(bKey);
      })
      .slice(0, 5);
  }, [holidayEntries, todayKey]);

  const insights = useMemo(() => {
    const items = [];
    if (trendData.length > 1) {
      const peak = trendData.reduce((best, entry) => (entry.value > best.value ? entry : best), trendData[0]);
      items.push(`Attendance was strongest on ${peak.label} with ${peak.value} tracked check-ins.`);
    }
    if (lateCount > 0) {
      items.push(`Late arrival alerts are active for ${lateCount} attendance record${lateCount === 1 ? '' : 's'} in the loaded data.`);
    }
    if (holidayToday) {
      items.push(`Today is ${holidayToday.name} (${holidayToday.type || 'holiday'}).`);
    }
    if (upcomingHolidays.length > 0) {
      const nextHoliday = upcomingHolidays[0];
      items.push(`The next company holiday is ${nextHoliday?.name || 'Holiday'} on ${formatDate(nextHoliday?.date || nextHoliday?.Date)}.`);
    }
    if (items.length === 0) {
      items.push('No additional attendance insights are available from the current loaded dataset.');
    }
    return items;
  }, [trendData, lateCount, upcomingHolidays, holidayToday]);

  const hasFilterHandler = Boolean(onAttendanceFiltersChange || onResetAttendanceFilters);

  const handleViewTodaysAttendance = () => {
    const today = new Date();
    const normalizedToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    setCalendarMonth(new Date(normalizedToday.getFullYear(), normalizedToday.getMonth(), 1));
    setSelectedCalendarDate(normalizedToday);
    const target = document.getElementById('attendance-calendar-panel');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleAttendanceReport = () => {
    const target = document.getElementById('attendance-report-panel');
    target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  return (
    <div className="space-y-6">
      {attendanceError ? (
        <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-300">
          <div className="font-bold">Attendance data could not be loaded.</div>
          <div className="mt-1">{attendanceError}</div>
        </div>
      ) : null}

      <section className="overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900 via-blue-800 to-indigo-700 p-6 text-white shadow-xl shadow-indigo-900/20 ring-1 ring-white/10">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-100 ring-1 ring-white/10">
              <CalendarClock className="h-3.5 w-3.5" />
              Workforce Operations
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-white">
              Attendance Management
            </h2>
            <p className="mt-2 max-w-xl text-sm text-indigo-100/80">
              Administrators can monitor attendance, workforce presence, and operational exceptions across the organization in real time.
            </p>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleViewTodaysAttendance}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-indigo-700 shadow-lg shadow-indigo-950/10 transition hover:-translate-y-0.5 hover:bg-indigo-50"
              >
                <CalendarClock className="h-4 w-4" />
                View Today's Attendance
              </button>
              <button
                type="button"
                onClick={handleAttendanceReport}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/15 bg-white/5 px-4 py-2.5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-white/10"
              >
                <TrendingUp className="h-4 w-4" />
                Attendance Report
              </button>
            </div>
          </div>

          <div className="grid w-full max-w-lg grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Attendance rate</div>
              <div className="mt-2 text-2xl font-black text-white">{attendanceRateText}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Check-in completion</div>
              <div className="mt-2 text-2xl font-black text-white">{Math.min(100, Math.max(0, checkInCompletionRate)).toFixed(0)}%</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Review queue</div>
              <div className="mt-2 text-2xl font-black text-white">{reviewQueueCount}</div>
            </div>
          </div>
        </div>
      </section>

      {!attendanceLoading && !attendanceError && (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
          {metrics.map((metric) => (
            <div key={metric.label} className="group rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between">
                <div className={`rounded-xl p-2 ${metric.accent}`}>{metric.icon}</div>
                <span className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500">{metric.delta}</span>
              </div>
              <div className="mt-4 text-3xl font-black tracking-tight text-slate-900 dark:text-white">{metric.value}</div>
              <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">{metric.label}</div>
            </div>
          ))}
        </div>
      )}

      {!attendanceLoading && !attendanceError && (
        <div id="attendance-report-panel" className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Distribution</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Attendance status</h3>
              </div>
              <div className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-indigo-700 dark:bg-indigo-950/50 dark:text-indigo-300">Live</div>
            </div>

            <div className="flex flex-col gap-4 md:flex-row md:items-center">
              <div className="relative mx-auto flex h-32 w-32 items-center justify-center rounded-full" style={{ background: donutGradient }}>
                <div className="flex h-20 w-20 items-center justify-center rounded-full bg-white text-center shadow-inner dark:bg-slate-900">
                  <div>
                    <div className="text-lg font-black text-slate-900 dark:text-white">{attendanceRateText}</div>
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500">Rate</div>
                  </div>
                </div>
              </div>

              <div className="flex-1 space-y-3">
                {chartData.map((item) => (
                  <div key={item.label} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="flex items-center gap-2">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="text-sm font-medium text-slate-700 dark:text-slate-200">{item.label}</span>
                    </div>
                    <span className="text-sm font-bold text-slate-900 dark:text-white">{item.value}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Operations</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Automation signals</h3>
              </div>
              <AlertTriangle className="h-5 w-5 text-amber-500" />
            </div>

            <div className="space-y-3">
              {automationSignals.length > 0 ? (
                automationSignals.map((signal, idx) => (
                    <div key={signal.id || `${signal.title}-${signal.message}-${idx}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm font-semibold text-slate-900 dark:text-white">{signal.title}</div>
                      <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-[0.1em] ${signal.tone}`}>{signal.tag}</span>
                    </div>
                    <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{signal.message}</div>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">
                  No active automation signals were returned by the live attendance data.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!attendanceLoading && !attendanceError && (
        <div className="grid gap-4 xl:grid-cols-[1.1fr_0.9fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Trend</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Recent attendance</h3>
              </div>
              <TrendingUp className="h-5 w-5 text-emerald-600" />
            </div>

            {trendData.length > 0 ? (
              <div className="flex h-40 items-stretch gap-2">
                {trendData.map((point) => {
                  const percent = maxTrendValue > 0 ? (point.value / maxTrendValue) * 100 : 0;
                  const breakdown = [
                    point.present !== undefined ? `${point.present} present` : null,
                    point.late ? `${point.late} late` : null,
                    point.working ? `${point.working} currently working` : null,
                  ].filter(Boolean).join(' · ');
                  return (
                    <div key={point.label} className="flex flex-1 flex-col items-center gap-2">
                      <div className="text-[10px] font-bold text-slate-600 dark:text-slate-300">{point.value}</div>
                      {/* The track must be flex-1 inside a fixed-height column: a percentage height
                          only resolves against a definite parent height, so without it the bar
                          collapses to nothing and the chart renders as bare axis labels. */}
                      <div className="flex w-full flex-1 items-end" title={breakdown ? `${point.label}: ${breakdown}` : `${point.label}: ${point.value} attended`}>
                        {point.value > 0 ? (
                          <div
                            className="w-full rounded-t-2xl bg-gradient-to-t from-indigo-600 to-indigo-300"
                            style={{ height: `${Math.max(6, percent)}%` }}
                          />
                        ) : (
                          // A zero day gets a flat baseline rather than a floor-height bar, so it
                          // reads as "nobody attended" instead of a small non-zero value.
                          <div className="h-[3px] w-full rounded-full bg-slate-200 dark:bg-slate-700" />
                        )}
                      </div>
                      <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">{point.label}</div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-slate-300 bg-slate-50 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">
                No historical attendance trend is available in the current data subset.
              </div>
            )}
          </div>

          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Department mix</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Department attendance</h3>
              </div>
              <Users className="h-5 w-5 text-sky-600" />
            </div>

            <div className="space-y-3">
              {departmentData.length > 0 ? (
                departmentData.map((item) => (
                  <div key={item.label}>
                    <div className="mb-1 flex items-center justify-between text-xs text-slate-600 dark:text-slate-300">
                      <span>{item.label}</span>
                      <span className="font-semibold">{item.value}</span>
                    </div>
                    <div className="h-2.5 rounded-full bg-slate-100 dark:bg-slate-800">
                      <div className="h-2.5 rounded-full bg-gradient-to-r from-indigo-500 to-violet-400" style={{ width: `${Math.max(8, (item.value / maxDeptValue) * 100)}%` }} />
                    </div>
                  </div>
                ))
              ) : (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">
                  Department-level attendance breakdown is not available in the current dataset.
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {!attendanceLoading && !attendanceError && (
        <div id="attendance-calendar-panel" className="grid gap-4 xl:grid-cols-[1.3fr_0.7fr]">
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between gap-3">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Calendar</p>
                <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Holiday & working-day view</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() - 1, 1))}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-600 transition hover:border-indigo-200 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  aria-label="Previous month"
                >
                  <ChevronLeft className="h-4 w-4" />
                </button>
                <button
                  type="button"
                  onClick={() => {
                    const next = new Date(today.getFullYear(), today.getMonth(), today.getDate());
                    setCalendarMonth(new Date(next.getFullYear(), next.getMonth(), 1));
                    setSelectedCalendarDate(next);
                  }}
                  className="rounded-xl border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                >
                  Today
                </button>
                <button
                  type="button"
                  onClick={() => setCalendarMonth(new Date(calendarMonth.getFullYear(), calendarMonth.getMonth() + 1, 1))}
                  className="rounded-xl border border-slate-200 bg-slate-50 p-2 text-slate-600 transition hover:border-indigo-200 hover:text-indigo-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  aria-label="Next month"
                >
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mb-4 flex items-center justify-between rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-800 dark:bg-slate-950/60">
              <div className="text-sm font-bold text-slate-900 dark:text-white">
                {new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' }).format(calendarMonth)}
              </div>
              <div className="text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
                {holidaysForSelectedMonth.length} holiday{holidaysForSelectedMonth.length === 1 ? '' : 's'}
              </div>
            </div>

            <div className="grid grid-cols-7 gap-2 text-center text-[10px] font-bold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">
              {['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].map((day) => (
                <div key={day} className="py-2">{day}</div>
              ))}
            </div>

            <div className="grid grid-cols-7 gap-2">
              {calendarDays.map(({ date, iso, isCurrentMonth, isToday, isSelected, holiday, weekend, hasAttendance }) => (
                <button
                  type="button"
                  key={iso}
                  onClick={() => setSelectedCalendarDate(date)}
                  className={[
                    'relative min-h-[88px] rounded-2xl border p-2 text-left transition-all duration-200',
                    isCurrentMonth ? 'border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900' : 'border-slate-100 bg-slate-50 text-slate-400 dark:border-slate-800 dark:bg-slate-950/30 dark:text-slate-500',
                    isSelected ? 'border-indigo-300 bg-indigo-50 shadow-sm dark:border-indigo-700 dark:bg-indigo-950/40' : 'hover:border-indigo-200 hover:bg-indigo-50/60 dark:hover:border-indigo-800 dark:hover:bg-slate-800/80',
                    isToday ? 'ring-2 ring-indigo-200 dark:ring-indigo-800' : '',
                  ].join(' ')}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={['text-sm font-bold', isSelected ? 'text-indigo-700 dark:text-indigo-300' : 'text-slate-700 dark:text-slate-200'].join(' ')}>
                      {date.getDate()}
                    </span>
                    {holiday && (
                      <span className="h-2.5 w-2.5 rounded-full bg-rose-500" title={holiday.name || 'Holiday'} />
                    )}
                  </div>
                  <div className="mt-2 space-y-1">
                    {holiday ? (
                      <div className="rounded-full bg-rose-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                        {holiday.name || 'Holiday'}
                      </div>
                    ) : null}
                    {weekend && !holiday ? (
                      <div className="rounded-full bg-slate-100 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                        Weekend
                      </div>
                    ) : null}
                    {hasAttendance && !holiday ? (
                      <div className="rounded-full bg-emerald-50 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-[0.08em] text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
                        Active
                      </div>
                    ) : null}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Selected date</p>
                  <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">{formatDate(selectedCalendarKey)}</h3>
                </div>
                <CalendarDays className="h-5 w-5 text-indigo-600" />
              </div>

              <div className="mt-4 space-y-2">
                {selectedDayStats.holiday ? (
                  <div className="rounded-2xl border border-rose-200 bg-rose-50 p-3 dark:border-rose-900/70 dark:bg-rose-950/20">
                    <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-rose-700 dark:text-rose-300">Holiday</div>
                    <div className="mt-1 text-sm font-bold text-rose-800 dark:text-rose-200">{selectedDayStats.holiday.name}</div>
                    <div className="text-xs text-rose-700/80 dark:text-rose-200/80">{selectedDayStats.holiday.type || 'Company holiday'}</div>
                  </div>
                ) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Working day</div>
                    <div className="mt-1 text-sm font-bold text-slate-800 dark:text-slate-200">{selectedDayStats.isWeekend ? 'Weekend' : 'Regular working day'}</div>
                  </div>
                )}

                <div className="grid grid-cols-3 gap-2">
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Present</div>
                    <div className="mt-1 text-lg font-black text-slate-900 dark:text-white">{selectedDayStats.present}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Late</div>
                    <div className="mt-1 text-lg font-black text-amber-600 dark:text-amber-300">{selectedDayStats.late}</div>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-center dark:border-slate-800 dark:bg-slate-950/60">
                    <div className="text-[10px] uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Absent</div>
                    <div className="mt-1 text-lg font-black text-rose-600 dark:text-rose-300">{selectedDayStats.absent}</div>
                  </div>
                </div>

                {selectedDayStats.records.length === 0 ? (
                  <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-3 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">
                    No attendance activity is available for this date.
                  </div>
                ) : (
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300">
                    <span className="font-semibold text-slate-900 dark:text-white">{selectedDayStats.records.length}</span> attendance record{selectedDayStats.records.length === 1 ? '' : 's'} matched the selected date.
                  </div>
                )}
              </div>
            </div>

            <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Insights</p>
                  <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Operational signals</h3>
                </div>
                <Sparkles className="h-5 w-5 text-violet-500" />
              </div>

              <div className="mt-4 space-y-2">
                {insights.map((insight) => (
                  <div key={insight} className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-950/60 dark:text-slate-300">
                    {insight}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {!attendanceLoading && !attendanceError && (() => {
        const visibleHolidays = upcomingHolidays;
        return (
          <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="mb-4 flex items-center justify-between">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Company calendar</p>
                <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Upcoming holidays</h3>
              </div>
              <div className="rounded-full bg-rose-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-rose-700 dark:bg-rose-950/40 dark:text-rose-300">
                {visibleHolidays.length} scheduled
              </div>
            </div>

            {(visibleHolidays.length === 0) ? (
              <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-950/60 dark:text-slate-400">
                No company holiday records are currently available from the live holiday data source.
              </div>
            ) : (
              <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                {visibleHolidays.map((holiday, index) => {
                  const dateLabel = formatDate(holiday?.date || holiday?.Date);
                  return (
                    <div key={`${holiday?.date || holiday?.Date || 'holiday'}-${index}`} className="rounded-2xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-800 dark:bg-slate-950/60">
                      <div className="text-[10px] font-bold uppercase tracking-[0.12em] text-rose-700 dark:text-rose-300">{holiday?.type || 'Holiday'}</div>
                      <div className="mt-2 text-base font-black text-slate-900 dark:text-white">{holiday?.name || 'Company holiday'}</div>
                      <div className="mt-1 text-sm text-slate-600 dark:text-slate-300">{dateLabel}</div>
                      {holiday?.description && (
                        <div className="mt-2 text-xs text-slate-500 dark:text-slate-400">{holiday.description}</div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        );
      })()}

      <div className="rounded-3xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Directory</p>
            <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Attendance records</h3>
          </div>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <div className="relative">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Search employee or ID"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100 sm:w-56"
              />
            </div>

            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800">
              <Filter className="h-4 w-4 text-slate-400" />
              <select
                value={attendanceFilters?.status || 'ALL'}
                onChange={(event) => hasFilterHandler && onAttendanceFiltersChange({ status: event.target.value })}
                className="bg-transparent text-sm text-slate-700 outline-none dark:text-slate-200"
              >
                <option value="ALL">All statuses</option>
                <option value="Present">Present</option>
                <option value="Working">Working</option>
                <option value="Late">Late</option>
                <option value="Absent">Absent</option>
              </select>
            </div>
          </div>
        </div>

        <div className="mb-4 grid gap-3 md:grid-cols-3 xl:grid-cols-4">
          <label className="flex flex-col gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
            Department
            <select
              value={attendanceFilters?.department || 'ALL'}
              onChange={(event) => hasFilterHandler && onAttendanceFiltersChange({ department: event.target.value })}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="ALL">All departments</option>
              {departmentOptions.map((department) => (
                <option key={department} value={department}>{department}</option>
              ))}
            </select>
          </label>

          <label className="flex flex-col gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
            Start date
            <input
              type="date"
              value={attendanceFilters?.startDate || ''}
              onChange={(event) => hasFilterHandler && onAttendanceFiltersChange({ startDate: event.target.value })}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
          </label>

          <label className="flex flex-col gap-1.5 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
            End date
            <input
              type="date"
              value={attendanceFilters?.endDate || ''}
              onChange={(event) => hasFilterHandler && onAttendanceFiltersChange({ endDate: event.target.value })}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-700 outline-none transition focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
          </label>

          <div className="flex items-end">
            <button
              type="button"
              onClick={() => onResetAttendanceFilters && onResetAttendanceFilters()}
              className="w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm font-semibold text-slate-700 transition hover:border-indigo-200 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              Clear filters
            </button>
          </div>
        </div>

        {attendanceLoading ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, index) => (
              <div key={index} className="h-16 animate-pulse rounded-2xl bg-slate-100 dark:bg-slate-800" />
            ))}
          </div>
        ) : filteredRecords.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center dark:border-slate-700 dark:bg-slate-950/60">
            <div className="text-lg font-bold text-slate-800 dark:text-slate-200">No attendance records match the active filters</div>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">Adjust the filters or clear them to review the current attendance workspace.</p>
            <button
              type="button"
              onClick={() => onResetAttendanceFilters && onResetAttendanceFilters()}
              className="mt-4 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-600 dark:bg-indigo-600 dark:hover:bg-indigo-500"
            >
              Clear filters
            </button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-800">
            <div className="overflow-x-auto">
              <table className="min-w-full text-left text-sm">
                <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:border-slate-800 dark:bg-slate-800/80 dark:text-slate-400">
                  <tr>
                    <th className="px-4 py-3.5">Employee</th>
                    <th className="px-4 py-3.5">Department</th>
                    <th className="px-4 py-3.5">Date</th>
                    <th className="px-4 py-3.5">Check In</th>
                    <th className="px-4 py-3.5">Check Out</th>
                    <th className="px-4 py-3.5">Hours</th>
                    <th className="px-4 py-3.5">Status</th>
                    <th className="px-4 py-3.5 text-right">View</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                  {filteredRecords.map((record) => {
                    const status = getAttendanceStatus(record);
                    return (
                      <tr key={`${getEmployeeId(record)}-${toText(record?.date, record?.Date)}`} className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/70">
                        <td className="px-4 py-3.5">
                          <div className="flex items-center gap-3">
                            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-indigo-500 to-violet-500 text-xs font-black text-white">{getInitials(record)}</div>
                            <div>
                              <div className="font-bold text-slate-900 dark:text-white">{getEmployeeName(record, employees)}</div>
                              <div className="text-[11px] text-slate-500 dark:text-slate-400">{getEmployeeId(record) || '—'}</div>
                            </div>
                          </div>
                        </td>
                        <td className="px-4 py-3.5 text-slate-700 dark:text-slate-200">{getDepartment(record)}</td>
                        <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{formatDate(toText(record?.date, record?.Date))}</td>
                        <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{formatTime(toText(record?.checkIn, record?.CheckIn))}</td>
                        <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{formatTime(toText(record?.checkOut, record?.CheckOut))}</td>
                        <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{formatHours(toText(record?.workingHours, record?.WorkingHours))}</td>
                        <td className="px-4 py-3.5">
                          <span className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold ${getStatusClasses(status)}`}>{status}</span>
                        </td>
                        <td className="px-4 py-3.5 text-right">
                          <button
                            type="button"
                            onClick={() => setSelectedRecord(record)}
                            className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                          >
                            View
                            <ChevronRight className="h-3.5 w-3.5" />
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {selectedRecord && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-violet-500 text-sm font-black text-white">{getInitials(selectedRecord)}</div>
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">{getEmployeeName(selectedRecord, employees)}</h3>
                  <p className="text-sm text-slate-500 dark:text-slate-400">{getEmployeeId(selectedRecord) || 'Employee record'}</p>
                </div>
              </div>
              <button type="button" onClick={() => setSelectedRecord(null)} className="rounded-xl border border-slate-200 p-2 text-slate-500 hover:text-slate-700 dark:border-slate-700 dark:text-slate-300">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <DetailBlock label="Attendance date" value={formatDate(toText(selectedRecord?.date, selectedRecord?.Date))} />
              <DetailBlock label="Department" value={getDepartment(selectedRecord)} />
              <DetailBlock label="Check-in" value={formatTime(toText(selectedRecord?.checkIn, selectedRecord?.CheckIn))} />
              <DetailBlock label="Check-out" value={formatTime(toText(selectedRecord?.checkOut, selectedRecord?.CheckOut))} />
              <DetailBlock label="Working hours" value={formatHours(toText(selectedRecord?.workingHours, selectedRecord?.WorkingHours))} />
              <DetailBlock label="Status" value={getAttendanceStatus(selectedRecord)} tone={selectedRecord?.LateArrival === true || selectedRecord?.lateArrival === true ? 'text-amber-700 dark:text-amber-300' : 'text-slate-700 dark:text-slate-200'} />
              <DetailBlock label="Late arrival" value={selectedRecord?.LateArrival === true || selectedRecord?.lateArrival === true ? 'Yes' : 'No'} />
              <DetailBlock label="GPS verified" value={selectedRecord?.gpsVerified === true || selectedRecord?.GPSVerified === true ? 'Verified' : 'Not verified'} />
            </div>

            {(selectedRecord?.latitude || selectedRecord?.longitude || selectedRecord?.distanceFromOffice !== undefined) && (
              <div className="mt-5 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-950/60">
                <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-[0.15em] text-slate-500 dark:text-slate-400">
                  <MapPin className="h-3.5 w-3.5" />
                  Location signal
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <DetailBlock label="Latitude" value={toText(selectedRecord?.latitude, selectedRecord?.Latitude, '—')} />
                  <DetailBlock label="Longitude" value={toText(selectedRecord?.longitude, selectedRecord?.Longitude, '—')} />
                  <DetailBlock label="Distance" value={selectedRecord?.distanceFromOffice != null ? `${selectedRecord.distanceFromOffice} m` : '—'} />
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
