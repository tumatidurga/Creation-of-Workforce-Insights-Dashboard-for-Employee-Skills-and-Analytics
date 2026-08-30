import React, { useMemo, useRef, useState } from 'react';
import { api } from '../../services/api';
import {
  ArrowUpRight,
  Briefcase,
  Building2,
  CalendarDays,
  CheckCircle2,
  Eye,
  Filter,
  Mail,
  MapPin,
  PencilLine,
  Phone,
  Plus,
  Search,
  ShieldCheck,
  UserPlus,
  Users,
  X
} from 'lucide-react';

const emptyForm = {
  firstName: '',
  lastName: '',
  email: '',
  phone: '',
  department: 'Engineering',
  jobRole: '',
  location: '',
  monthlyIncome: '',
  status: 'Active',
};

const toDisplayName = (emp = {}) => {
  const first = emp.firstName || emp.FirstName || emp.first_name || '';
  const last = emp.lastName || emp.LastName || emp.last_name || '';
  const fallback = emp.name || emp.EmployeeName || emp.employeeName || '';
  if (first || last) return `${first} ${last}`.trim();
  return fallback || 'Unassigned employee';
};

const toStatus = (emp = {}) => {
  const value = emp.status || emp.Status || emp.employmentStatus || emp.EmploymentStatus || 'Active';
  return value ? String(value).trim() : 'Active';
};

const toDepartment = (emp = {}) => emp.department || emp.Department || 'Unassigned';
const toRole = (emp = {}) => emp.jobRole || emp.JobRole || 'Not assigned';
const toEmpId = (emp = {}) => emp.empId || emp.EmpID || emp.EmpId || emp.employeeId || '—';
const toInitials = (emp = {}) => {
  const name = toDisplayName(emp);
  return name
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() || '')
    .join('') || 'NA';
};

const formatDate = (value) => {
  if (!value) return '—';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(date);
};

const formatCurrency = (value) => {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return '—';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(numeric);
};

const statusClasses = (status) => {
  const normalized = String(status || '').toLowerCase();
  if (normalized.includes('active') || normalized.includes('present')) return 'bg-emerald-50 text-emerald-700 ring-1 ring-emerald-200 dark:bg-emerald-950/50 dark:text-emerald-300 dark:ring-emerald-900';
  if (normalized.includes('inactive') || normalized.includes('suspended') || normalized.includes('terminated')) return 'bg-rose-50 text-rose-700 ring-1 ring-rose-200 dark:bg-rose-950/50 dark:text-rose-300 dark:ring-rose-900';
  if (normalized.includes('leave')) return 'bg-amber-50 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-950/50 dark:text-amber-300 dark:ring-amber-900';
  return 'bg-slate-100 text-slate-700 ring-1 ring-slate-200 dark:bg-slate-800 dark:text-slate-200 dark:ring-slate-700';
};

export const EmployeeManagement = ({
  employees = [],
  employeePagination = { total: 0, page: 1, size: 50, pages: 1 },
  onRequestEmployees = null,
  onAddEmployee,
  onUpdateEmployee,
  employeesLoading = false,
  employeesError = null
}) => {
  const [search, setSearch] = useState('');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [selectedStatus, setSelectedStatus] = useState('ALL');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [formState, setFormState] = useState(emptyForm);
  const [formError, setFormError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const searchTimerRef = useRef(null);

  const empList = Array.isArray(employees) ? employees : [];
  const employeePaginationMeta = employeePagination && typeof employeePagination === 'object'
    ? employeePagination
    : { total: 0, page: 1, size: 50, pages: 1 };
  const pageSize = Number(employeePaginationMeta.size) || 50;
  const currentPage = Number(employeePaginationMeta.page) || 1;
  const totalEmployees = Number(employeePaginationMeta.total) || empList.length || 0;

  const departments = useMemo(() => {
    const unique = [...new Set(empList.map((emp) => toDepartment(emp)).filter(Boolean))];
    return ['ALL', ...unique];
  }, [empList]);

  const summary = useMemo(() => {
    const total = totalEmployees || empList.length || 0;
    const active = empList.filter((emp) => {
      const value = String(toStatus(emp)).toLowerCase();
      return value.includes('active') || value.includes('present');
    }).length;
    const inactive = empList.filter((emp) => {
      const value = String(toStatus(emp)).toLowerCase();
      return value.includes('inactive') || value.includes('terminated') || value.includes('suspended');
    }).length;
    const uniqueDepartments = new Set(empList.map((emp) => toDepartment(emp)).filter(Boolean)).size;
    const recentJoiners = empList.filter((emp) => {
      const raw = emp.joiningDate || emp.JoiningDate || emp.joinDate || emp.createdAt || emp.CreatedAt;
      if (!raw) return false;
      const date = new Date(raw);
      if (Number.isNaN(date.getTime())) return false;
      const diffDays = (Date.now() - date.getTime()) / (1000 * 60 * 60 * 24);
      return diffDays >= 0 && diffDays <= 180;
    }).length;
    return { total, active, inactive, uniqueDepartments, recentJoiners, activeRate: total > 0 ? Math.round((active / total) * 100) : 0 };
  }, [empList, totalEmployees]);

  React.useEffect(() => {
    if (!onRequestEmployees) return;
    if (searchTimerRef.current) clearTimeout(searchTimerRef.current);
    const timer = setTimeout(() => {
      const params = { page: 1, size: pageSize };
      if (search && search.trim()) params.search = search.trim();
      if (selectedDept && selectedDept !== 'ALL') params.department = selectedDept;
      if (selectedStatus && selectedStatus !== 'ALL') params.status = selectedStatus;
      onRequestEmployees(params);
    }, 350);
    searchTimerRef.current = timer;
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, selectedDept, selectedStatus, pageSize]);

  const visibleEmployees = useMemo(() => {
    const q = search.trim().toLowerCase();
    return empList.filter((emp) => {
      const name = toDisplayName(emp).toLowerCase();
      const id = String(toEmpId(emp)).toLowerCase();
      const email = String(emp.email || emp.Email || '').toLowerCase();
      const department = String(toDepartment(emp)).toLowerCase();
      const role = String(toRole(emp)).toLowerCase();
      const status = String(toStatus(emp)).toLowerCase();
      const matchesSearch = !q || name.includes(q) || id.includes(q) || email.includes(q) || department.includes(q) || role.includes(q) || status.includes(q);
      const matchesDept = selectedDept === 'ALL' || department === selectedDept.toLowerCase();
      const matchesStatus = selectedStatus === 'ALL' || status === selectedStatus.toLowerCase();
      return matchesSearch && matchesDept && matchesStatus;
    });
  }, [empList, search, selectedDept, selectedStatus]);

  const handleOpenAddModal = () => {
    setFormError('');
    setFormState(emptyForm);
    setShowAddModal(true);
  };

  const handleOpenEditModal = (emp) => {
    setFormError('');
    setFormState({
      firstName: emp.firstName || emp.FirstName || '',
      lastName: emp.lastName || emp.LastName || '',
      email: emp.email || emp.Email || '',
      phone: emp.phone || emp.Phone || '',
      department: toDepartment(emp),
      jobRole: toRole(emp),
      location: emp.location || emp.Location || '',
      monthlyIncome: emp.monthlyIncome ?? emp.MonthlyIncome ?? '',
      status: toStatus(emp),
    });
    setSelectedEmployee(emp);
    setShowEditModal(true);
  };

  const handleCreateEmployee = async (event) => {
    event.preventDefault();
    setFormError('');
    if (!formState.firstName || !formState.lastName || !formState.email || !formState.department) {
      setFormError('First name, last name, email, and department are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        firstName: formState.firstName,
        lastName: formState.lastName,
        email: formState.email,
        phone: formState.phone || '',
        department: formState.department,
        jobRole: formState.jobRole || 'Employee',
        location: formState.location || '',
        status: formState.status || 'Active',
        monthlyIncome: formState.monthlyIncome === '' ? undefined : Number(formState.monthlyIncome),
      };
      if (onAddEmployee) await onAddEmployee(payload);
      setShowAddModal(false);
      setFormState(emptyForm);
    } catch (err) {
      setFormError(err?.response?.data?.detail || err.message || 'Unable to create employee.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateEmployee = async (event) => {
    event.preventDefault();
    setFormError('');
    const employeeId = selectedEmployee?.empId || selectedEmployee?.EmpID || selectedEmployee?.EmpId || null;
    if (!employeeId) {
      setFormError('Employee ID is required to update the record.');
      return;
    }
    if (!formState.firstName || !formState.lastName || !formState.email) {
      setFormError('First name, last name, and email are required.');
      return;
    }
    setIsSubmitting(true);
    try {
      const payload = {
        empId: employeeId,
        firstName: formState.firstName,
        lastName: formState.lastName,
        email: formState.email,
        phone: formState.phone || '',
        department: formState.department,
        jobRole: formState.jobRole || 'Employee',
        location: formState.location || '',
        status: formState.status || 'Active',
        monthlyIncome: formState.monthlyIncome === '' ? undefined : Number(formState.monthlyIncome),
      };
      if (onUpdateEmployee) await onUpdateEmployee(payload);
      setShowEditModal(false);
      setSelectedEmployee(null);
    } catch (err) {
      setFormError(err?.response?.data?.detail || err.message || 'Unable to update employee.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenEmployeeDetails = async (emp) => {
    try {
      const empId = toEmpId(emp);
      if (empId && empId !== '—') {
        const fullEmployee = await api.getEmployeeById(empId);
        setSelectedEmployee(fullEmployee || emp);
      } else {
        setSelectedEmployee(emp);
      }
    } catch (error) {
      console.warn('Failed to fetch full employee profile; using list record instead.', error);
      setSelectedEmployee(emp);
    }
  };

  return (
    <div className="space-y-6">
      <section className="overflow-hidden rounded-3xl bg-gradient-to-r from-indigo-900 via-blue-800 to-indigo-700 p-6 text-white shadow-xl shadow-indigo-900/20 ring-1 ring-white/10">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1.5 text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-100 ring-1 ring-white/10">
              <Users className="h-3.5 w-3.5" />
              Workforce Management
            </div>
            <h2 className="mt-4 text-3xl font-black tracking-tight text-white">
              Employee Directory
            </h2>
            <p className="mt-2 max-w-xl text-sm text-indigo-100/80">
              HR and administrators can view, manage, and organize the workforce with a live view of employee health, role coverage, and department structure.
            </p>

            <div className="mt-5 flex flex-wrap gap-3">
              <button
                type="button"
                onClick={handleOpenAddModal}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-indigo-700 shadow-lg shadow-indigo-950/10 transition hover:-translate-y-0.5 hover:bg-indigo-50"
              >
                <UserPlus className="h-4 w-4" />
                Add Employee
              </button>
            </div>
          </div>

          <div className="grid w-full max-w-lg grid-cols-1 gap-3 sm:grid-cols-3">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Active rate</div>
              <div className="mt-2 text-2xl font-black text-white">{summary.activeRate}%</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Recent joins</div>
              <div className="mt-2 text-2xl font-black text-white">{summary.recentJoiners}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.16em] text-indigo-100/80">Departments</div>
              <div className="mt-2 text-2xl font-black text-white">{summary.uniqueDepartments}</div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between"> 
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Total employees</span>
            <div className="rounded-xl bg-indigo-50 p-2 text-indigo-600 dark:bg-indigo-950/60 dark:text-indigo-300"><Users className="h-4 w-4" /></div>
          </div>
          <div className="mt-4 text-3xl font-black text-slate-900 dark:text-white">{summary.total}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Synced from the live backend directory</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Active</span>
            <div className="rounded-xl bg-emerald-50 p-2 text-emerald-600 dark:bg-emerald-950/60 dark:text-emerald-300"><CheckCircle2 className="h-4 w-4" /></div>
          </div>
          <div className="mt-4 text-3xl font-black text-slate-900 dark:text-white">{summary.active}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Currently active records</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Inactive</span>
            <div className="rounded-xl bg-rose-50 p-2 text-rose-600 dark:bg-rose-950/60 dark:text-rose-300"><ShieldCheck className="h-4 w-4" /></div>
          </div>
          <div className="mt-4 text-3xl font-black text-slate-900 dark:text-white">{summary.inactive}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Archived or non-active records</p>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Departments</span>
            <div className="rounded-xl bg-sky-50 p-2 text-sky-600 dark:bg-sky-950/60 dark:text-sky-300"><Building2 className="h-4 w-4" /></div>
          </div>
          <div className="mt-4 text-3xl font-black text-slate-900 dark:text-white">{summary.uniqueDepartments}</div>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Distinct organizational units</p>
        </div>
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-3.5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Search by name, employee ID, email, department, or role"
              className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-9 pr-3 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-100"
            />
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800">
            <Filter className="h-4 w-4 text-slate-400" />
            <select
              value={selectedDept}
              onChange={(event) => setSelectedDept(event.target.value)}
              className="bg-transparent text-sm text-slate-700 outline-none dark:text-slate-200"
            >
              {departments.map((department) => (
                <option key={department} value={department}>{department === 'ALL' ? 'All departments' : department}</option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 dark:border-slate-700 dark:bg-slate-800">
            <Briefcase className="h-4 w-4 text-slate-400" />
            <select
              value={selectedStatus}
              onChange={(event) => setSelectedStatus(event.target.value)}
              className="bg-transparent text-sm text-slate-700 outline-none dark:text-slate-200"
            >
              {['ALL', 'Active', 'Inactive', 'Leave', 'Terminated', 'Pending'].map((status) => (
                <option key={status} value={status}>{status === 'ALL' ? 'All status' : status}</option>
              ))}
            </select>
          </div>
        </div>

        <div className="mt-3 flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
          <span>
            {employeesLoading ? 'Loading employees…' : `${visibleEmployees.length} employee records`}
          </span>
          {totalEmployees > 0 && (
            <span>
              Page {currentPage} of {Math.max(1, Number(employeePaginationMeta.pages) || 1)}
            </span>
          )}
        </div>
      </div>

      {employeesError && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
          Unable to load employee directory: {employeesError}
          <button
            type="button"
            onClick={() => onRequestEmployees && onRequestEmployees({ page: 1, size: pageSize })}
            className="ml-2 font-bold underline underline-offset-2"
          >
            Retry
          </button>
        </div>
      )}

      {employeesLoading ? (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="space-y-3">
            {[...Array(5)].map((_, index) => (
              <div key={index} className="animate-pulse flex items-center gap-4 rounded-xl bg-slate-100 p-3 dark:bg-slate-800">
                <div className="h-10 w-10 rounded-xl bg-slate-200 dark:bg-slate-700" />
                <div className="flex-1 space-y-2">
                  <div className="h-3 w-1/3 rounded bg-slate-200 dark:bg-slate-700" />
                  <div className="h-3 w-2/3 rounded bg-slate-200 dark:bg-slate-700" />
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : visibleEmployees.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center shadow-sm dark:border-slate-700 dark:bg-slate-900">
          <Users className="mx-auto h-10 w-10 text-slate-400" />
          <h3 className="mt-4 text-lg font-bold text-slate-900 dark:text-white">No employees match this view</h3>
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
            Try a different search, clear the filters, or add a new employee to the directory.
          </p>
          <button
            type="button"
            onClick={handleOpenAddModal}
            className="mt-5 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-600 dark:bg-indigo-600 dark:hover:bg-indigo-500"
          >
            <Plus className="h-4 w-4" />
            Add Employee
          </button>
        </div>
      ) : (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-[11px] font-bold uppercase tracking-[0.12em] text-slate-500 dark:border-slate-800 dark:bg-slate-800/80 dark:text-slate-400">
                <tr>
                  <th className="px-4 py-3.5">Employee</th>
                  <th className="px-4 py-3.5">Department</th>
                  <th className="px-4 py-3.5">Role</th>
                  <th className="px-4 py-3.5">Location</th>
                  <th className="px-4 py-3.5">Status</th>
                  <th className="px-4 py-3.5">Joined</th>
                  <th className="px-4 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                {visibleEmployees.map((emp) => (
                  <tr key={toEmpId(emp)} className="transition hover:bg-slate-50 dark:hover:bg-slate-800/80">
                    <td className="px-4 py-3.5">
                      <button
                        type="button"
                        onClick={() => handleOpenEmployeeDetails(emp)}
                        className="flex items-center gap-3 text-left"
                      >
                        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-indigo-600 text-xs font-black text-white shadow-sm shadow-indigo-500/20">
                          {toInitials(emp)}
                        </div>
                        <div>
                          <div className="font-bold text-slate-900 dark:text-white">{toDisplayName(emp)}</div>
                          <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                            <span className="font-mono text-[11px] text-indigo-600 dark:text-indigo-400">{toEmpId(emp)}</span>
                            <span className="hidden sm:inline">•</span>
                            <span className="hidden sm:inline">{emp.email || emp.Email || 'No email'}</span>
                          </div>
                        </div>
                      </button>
                    </td>
                    <td className="px-4 py-3.5 text-slate-700 dark:text-slate-200">{toDepartment(emp)}</td>
                    <td className="px-4 py-3.5 text-slate-700 dark:text-slate-200">{toRole(emp)}</td>
                    <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{emp.location || emp.Location || '—'}</td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-flex rounded-full px-2.5 py-1 text-[10px] font-bold ${statusClasses(toStatus(emp))}`}>
                        {toStatus(emp)}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-slate-600 dark:text-slate-300">{formatDate(emp.joiningDate || emp.JoiningDate || emp.joinedAt || emp.createdAt)}</td>
                    <td className="px-4 py-3.5">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => handleOpenEmployeeDetails(emp)}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-700"
                        >
                          <Eye className="h-3.5 w-3.5" />
                          View
                        </button>
                        <button
                          type="button"
                          onClick={() => handleOpenEditModal(emp)}
                          className="inline-flex items-center gap-1 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 transition hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-700"
                        >
                          <PencilLine className="h-3.5 w-3.5" />
                          Edit
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="text-xs text-slate-500 dark:text-slate-400">
          {visibleEmployees.length > 0 ? `Showing ${visibleEmployees.length} visible records` : 'No records visible'}
        </div>
        <div className="flex items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => onRequestEmployees && onRequestEmployees({ page: Math.max(1, currentPage - 1), size: pageSize, search: search || undefined, department: selectedDept !== 'ALL' ? selectedDept : undefined, status: selectedStatus !== 'ALL' ? selectedStatus : undefined })}
            disabled={currentPage <= 1 || !onRequestEmployees}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            Previous
          </button>
          <span className="rounded-lg bg-slate-100 px-2.5 py-1.5 font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-200">
            {currentPage}
          </span>
          <button
            type="button"
            onClick={() => onRequestEmployees && onRequestEmployees({ page: currentPage + 1, size: pageSize, search: search || undefined, department: selectedDept !== 'ALL' ? selectedDept : undefined, status: selectedStatus !== 'ALL' ? selectedStatus : undefined })}
            disabled={currentPage >= (Number(employeePaginationMeta.pages) || 1) || !onRequestEmployees}
            className="rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-700 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
          >
            Next
          </button>
        </div>
      </div>

      {selectedEmployee && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4 backdrop-blur-sm">
          <div className="max-h-[90vh] w-full max-w-3xl overflow-y-auto rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-start justify-between gap-4 border-b border-slate-200 pb-4 dark:border-slate-800">
              <div className="flex items-center gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-blue-600 text-lg font-black text-white shadow-lg shadow-indigo-500/20">
                  {toInitials(selectedEmployee)}
                </div>
                <div>
                  <h3 className="text-xl font-black text-slate-900 dark:text-white">{toDisplayName(selectedEmployee)}</h3>
                  <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {toRole(selectedEmployee)} • {toDepartment(selectedEmployee)}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-indigo-50 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
                      ID {toEmpId(selectedEmployee)}
                    </span>
                    <span className={`rounded-full px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] ${statusClasses(toStatus(selectedEmployee))}`}>
                      {toStatus(selectedEmployee)}
                    </span>
                  </div>
                </div>
              </div>
              <button type="button" onClick={() => setSelectedEmployee(null)} className="rounded-xl border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  <Mail className="h-3.5 w-3.5" />
                  Contact
                </div>
                <div className="mt-3 space-y-3 text-sm text-slate-700 dark:text-slate-200">
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Email</span>
                    <span className="font-medium text-right">{selectedEmployee.email || selectedEmployee.Email || '—'}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Phone</span>
                    <span className="font-medium text-right">{selectedEmployee.phone || selectedEmployee.Phone || '—'}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Location</span>
                    <span className="font-medium text-right">{selectedEmployee.location || selectedEmployee.Location || '—'}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-slate-200 p-4 dark:border-slate-800">
                <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500 dark:text-slate-400">
                  <Building2 className="h-3.5 w-3.5" />
                  Employment
                </div>
                <div className="mt-3 space-y-3 text-sm text-slate-700 dark:text-slate-200">
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Department</span>
                    <span className="font-medium text-right">{toDepartment(selectedEmployee)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Role</span>
                    <span className="font-medium text-right">{toRole(selectedEmployee)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-2 dark:border-slate-800">
                    <span className="text-slate-500 dark:text-slate-400">Joined</span>
                    <span className="font-medium text-right">{formatDate(selectedEmployee.joiningDate || selectedEmployee.JoiningDate || selectedEmployee.joinedAt)}</span>
                  </div>
                  <div className="flex items-center justify-between gap-2 pb-1">
                    <span className="text-slate-500 dark:text-slate-400">Compensation</span>
                    <span className="font-medium text-right">{formatCurrency(selectedEmployee.monthlyIncome || selectedEmployee.MonthlyIncome)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-3 border-t border-slate-200 pt-4 dark:border-slate-800">
              <button type="button" onClick={() => setSelectedEmployee(null)} className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {(showAddModal || showEditModal) && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/70 p-4 backdrop-blur-sm">
          <div className="w-full max-w-2xl rounded-3xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center justify-between border-b border-slate-200 pb-4 dark:border-slate-800">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-600 dark:text-indigo-300">{showAddModal ? 'Onboard employee' : 'Update employee'}</div>
                <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">{showAddModal ? 'Add a new team member' : 'Edit employee record'}</h3>
              </div>
              <button type="button" onClick={() => { setShowAddModal(false); setShowEditModal(false); setFormError(''); }} className="rounded-xl border border-slate-200 p-2 text-slate-500 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800">
                <X className="h-4 w-4" />
              </button>
            </div>

            <form onSubmit={showAddModal ? handleCreateEmployee : handleUpdateEmployee} className="mt-5 space-y-4">
              {formError && (
                <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/30 dark:text-rose-200">
                  {formError}
                </div>
              )}

              <div className="grid gap-4 md:grid-cols-2">
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">First name</label>
                  <input value={formState.firstName} onChange={(event) => setFormState((prev) => ({ ...prev, firstName: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" required />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Last name</label>
                  <input value={formState.lastName} onChange={(event) => setFormState((prev) => ({ ...prev, lastName: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" required />
                </div>
                <div className="md:col-span-2">
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Email address</label>
                  <input type="email" value={formState.email} onChange={(event) => setFormState((prev) => ({ ...prev, email: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" required />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Phone</label>
                  <input value={formState.phone} onChange={(event) => setFormState((prev) => ({ ...prev, phone: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Department</label>
                  <select value={formState.department} onChange={(event) => setFormState((prev) => ({ ...prev, department: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white">
                    {['Engineering', 'Human Resources', 'Finance & Payroll', 'Product Management', 'Operations'].map((department) => (
                      <option key={department} value={department}>{department}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Job role</label>
                  <input value={formState.jobRole} onChange={(event) => setFormState((prev) => ({ ...prev, jobRole: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" placeholder="Employee" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Location</label>
                  <input value={formState.location} onChange={(event) => setFormState((prev) => ({ ...prev, location: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Monthly income</label>
                  <input type="number" value={formState.monthlyIncome} onChange={(event) => setFormState((prev) => ({ ...prev, monthlyIncome: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-bold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Status</label>
                  <select value={formState.status} onChange={(event) => setFormState((prev) => ({ ...prev, status: event.target.value }))} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-900 outline-none transition focus:border-indigo-500 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-white">
                    {['Active', 'Inactive', 'Leave', 'Terminated'].map((option) => (
                      <option key={option} value={option}>{option}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-3 border-t border-slate-200 pt-4 dark:border-slate-800">
                <button type="button" onClick={() => { setShowAddModal(false); setShowEditModal(false); setFormError(''); }} className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">
                  Cancel
                </button>
                <button type="submit" disabled={isSubmitting} className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white shadow-lg shadow-indigo-500/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-60">
                  {isSubmitting ? 'Saving...' : showAddModal ? 'Create Employee' : 'Save Changes'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
