import React, { useState } from 'react';
import { FileSpreadsheet, Plus, CheckCircle2, Clock, DollarSign, AlertCircle } from 'lucide-react';



export const TimesheetManagement = ({
  employees = [],
  selectedEmployeeId = '',
  onSelectEmployee,
  timesheets = [],
  timesheetsLoading = false,
  timesheetsError = null,
  onAddTimesheet,
  onApproveTimesheet,
  onRejectTimesheet
}) => {
  const [showModal, setShowModal] = useState(false);
  const [projectName, setProjectName] = useState('Enterprise AI Portal Core');
  const [taskDescription, setTaskDescription] = useState('');
  const [hoursLogged, setHoursLogged] = useState(8);
  const [isBillable, setIsBillable] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  const selectedEmployee = employees.find((employee) => employee.empId === selectedEmployeeId) || null;
  const safeTimesheets = Array.isArray(timesheets) ? timesheets : [];
  const totalHours = safeTimesheets.reduce((acc, t) => acc + Number(t?.hoursLogged || 0), 0);
  const billableHours = safeTimesheets
    .filter((t) => Boolean(t?.isBillable) || Number(t?.clientBillingHours || 0) > 0)
    .reduce((acc, t) => acc + Number(t?.hoursLogged || 0), 0);

  const pendingEntries = safeTimesheets.filter((t) => String(t.status || 'Pending').toLowerCase() === 'pending' || String(t.status || 'Pending').toLowerCase() === 'submitted');
  const approvedEntries = safeTimesheets.filter((t) => String(t.status || '').toLowerCase() === 'approved');
  const rejectedEntries = safeTimesheets.filter((t) => String(t.status || '').toLowerCase() === 'rejected');

  const filteredTimesheets = safeTimesheets.filter((t) => {
    const haystack = [t.empName, t.empId, t.projectName, t.taskDescription, t.status].filter(Boolean).join(' ').toLowerCase();
    const matchesSearch = !searchQuery || haystack.includes(searchQuery.toLowerCase());
    const statusValue = String(t.status || 'Pending').toUpperCase();
    const matchesStatus = statusFilter === 'ALL' || statusValue === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const summaryMetrics = [
    { label: 'Pending review', value: pendingEntries.length, tone: 'amber', icon: Clock },
    { label: 'Approved', value: approvedEntries.length, tone: 'emerald', icon: CheckCircle2 },
    { label: 'Rejected', value: rejectedEntries.length, tone: 'rose', icon: AlertCircle },
    { label: 'Billable hours', value: `${billableHours} hrs`, tone: 'violet', icon: DollarSign },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!selectedEmployeeId) {
      alert('Please select an employee before submitting a timesheet.');
      return;
    }

    const newEntry = {
      empId: selectedEmployeeId,
      date: new Date().toISOString().split('T')[0],
      projectName,
      hoursLogged: Number(hoursLogged),
      isBillable,
      status: 'Submitted'
    };

    await onAddTimesheet(newEntry);
    setShowModal(false);
    setTaskDescription('');
  };

  return (
    <div className="space-y-6">
      <div className="rounded-3xl border border-slate-200 bg-gradient-to-r from-slate-900 via-indigo-950 to-violet-950 p-6 text-white shadow-xl shadow-indigo-950/15 dark:border-slate-800">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 font-bold uppercase tracking-[0.18em] text-indigo-100">
              <FileSpreadsheet className="h-3.5 w-3.5 text-indigo-200" />
              Time & billing
            </div>
            <h2 className="mt-4 text-2xl font-bold tracking-[-0.04em] text-white">
              Daily Timesheets & Client Billing Tracker
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              Project allocation hours, client billable ratio calculations, and manager sign-off across active delivery workstreams.
            </p>
          </div>

          <button
            onClick={() => setShowModal(true)}
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-white px-4 py-2.5 text-xs font-bold text-slate-900 shadow-lg shadow-slate-950/15 transition hover:bg-slate-100"
          >
            <Plus className="h-4 w-4" />
            Log Time Entry
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summaryMetrics.map((metric) => {
          const Icon = metric.icon;
          const toneClasses = {
            amber: 'border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/40 dark:text-amber-300',
            emerald: 'border-emerald-200 bg-emerald-50 text-emerald-700 dark:border-emerald-900/60 dark:bg-emerald-950/40 dark:text-emerald-300',
            rose: 'border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/60 dark:bg-rose-950/40 dark:text-rose-300',
            violet: 'border-violet-200 bg-violet-50 text-violet-700 dark:border-violet-900/60 dark:bg-violet-950/40 dark:text-violet-300',
          }[metric.tone];

          return (
            <div key={metric.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm transition hover:-translate-y-0.5 hover:border-indigo-200 hover:shadow-md dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-500">
                <span>{metric.label}</span>
                <span className={`rounded-full border p-2 ${toneClasses}`}>
                  <Icon className="h-3.5 w-3.5" />
                </span>
              </div>
              <div className="mt-3 text-2xl font-black text-slate-900 dark:text-white">{metric.value}</div>
            </div>
          );
        })}
      </div>

      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="flex flex-col gap-3 border-b border-slate-100 pb-4 dark:border-slate-800 lg:flex-row lg:items-center lg:justify-between">
          <h3 className="text-sm font-bold text-slate-900 dark:text-white">
            Logged Timesheet Entries
          </h3>
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search employee or project"
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] text-slate-700 outline-none transition focus:border-indigo-300 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-[11px] text-slate-700 outline-none transition focus:border-indigo-300 focus:bg-white dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              <option value="ALL">All statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="APPROVED">Approved</option>
              <option value="REJECTED">Rejected</option>
              <option value="PENDING">Pending</option>
            </select>
          </div>
        </div>

        {timesheetsLoading && (
          <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-5 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400">Loading timesheets...</div>
        )}

        {!timesheetsLoading && timesheetsError && (
          <div className="mt-4 rounded-lg border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700">
            {timesheetsError}
          </div>
        )}

        {!timesheetsLoading && !timesheetsError && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-400 uppercase font-semibold text-[10px] dark:border-slate-800">
                  <th className="py-3 px-2">Date</th>
                  <th className="py-3 px-2">Employee</th>
                  <th className="py-3 px-2">Project</th>
                  <th className="py-3 px-2">Task Deliverable</th>
                  <th className="py-3 px-2">Hours Logged</th>
                  <th className="py-3 px-2">Billable Status</th>
                  <th className="py-3 px-2">Approval</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {filteredTimesheets.map((t, index) => {
                  const statusText = t.status || 'Pending';
                  const canAct = Boolean(t.id) && !['Approved', 'Rejected'].includes(statusText);

                  return (
                    <tr key={t.id || `${t.empId || 'unknown'}-${t.date || 'date'}-${index}`} className="hover:bg-slate-50 dark:hover:bg-slate-800/50">
                      <td className="py-3 px-2 text-slate-500 font-mono">{t.date || 'N/A'}</td>
                      <td className="py-3 px-2 font-bold text-slate-900 dark:text-white">{t.empName || t.empId || 'Unknown employee'}</td>
                      <td className="py-3 px-2 font-semibold text-indigo-600 dark:text-indigo-400">{t.projectName || 'Unspecified project'}</td>
                      <td className="py-3 px-2 text-slate-600 dark:text-slate-300 max-w-xs truncate">{t.taskDescription || 'No task description provided'}</td>
                      <td className="py-3 px-2 font-bold text-slate-900 dark:text-white">{Number(t.hoursLogged || 0)} hrs</td>
                      <td className="py-3 px-2">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                            Boolean(t.isBillable) || Number(t.clientBillingHours || 0) > 0 ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' : 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300'
                          }`}
                        >
                          {Boolean(t.isBillable) || Number(t.clientBillingHours || 0) > 0 ? 'Client Billable' : 'Internal Non-Billable'}
                        </span>
                      </td>
                      <td className="py-3 px-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className={`rounded-full px-2.5 py-0.5 text-[10px] font-bold ${
                            statusText === 'Approved' ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300' :
                            statusText === 'Rejected' ? 'bg-rose-100 text-rose-800 dark:bg-rose-950 dark:text-rose-300' :
                            'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                          }`}>
                            {statusText}
                          </span>
                          {canAct && (
                            <>
                              <button
                                type="button"
                                onClick={() => onApproveTimesheet?.(t.id)}
                                className="rounded bg-emerald-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-emerald-700"
                              >
                                Approve
                              </button>
                              <button
                                type="button"
                                onClick={() => onRejectTimesheet?.(t.id)}
                                className="rounded bg-rose-600 px-2 py-1 text-[10px] font-bold text-white hover:bg-rose-700"
                              >
                                Reject
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl dark:bg-slate-900 dark:text-white">
            <h3 className="text-base font-bold border-b border-slate-100 pb-3 dark:border-slate-800">
              Log Project Hours
            </h3>

            <form onSubmit={handleSubmit} className="mt-4 space-y-3 text-xs">
              <div>
               <label className="font-semibold block mb-1">Employee</label>
               <select
                 value={selectedEmployeeId}
                 onChange={(e) => onSelectEmployee(e.target.value)}
                 className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800"
                 required
               >
                 <option value="">Select an employee</option>
                 {employees.map((employee) => {
                   const fullName = [employee.firstName, employee.lastName].filter(Boolean).join(' ') || employee.employeeName || employee.name || employee.empId;
                   return (
                     <option key={employee.empId} value={employee.empId}>
                       {fullName} ({employee.empId})
                     </option>
                   );
                 })}
               </select>
             </div>

             <div>
               <label className="font-semibold block mb-1">Project Name</label>
               <input
                 type="text"
                 value={projectName}
                 onChange={(e) => setProjectName(e.target.value)}
                 className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800"
               />
             </div>

             <div>
               <label className="font-semibold block mb-1">Task Deliverable</label>
               <textarea
                 required
                 rows={2}
                 value={taskDescription}
                 onChange={(e) => setTaskDescription(e.target.value)}
                 placeholder="Describe task progress..."
                 className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800"
               />
             </div>

             <div className="grid grid-cols-2 gap-3">
               <div>
                 <label className="font-semibold block mb-1">Hours Logged</label>
                 <input
                   type="number"
                   step="0.5"
                   value={hoursLogged}
                   onChange={(e) => setHoursLogged(Number(e.target.value))}
                   className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 dark:border-slate-800 dark:bg-slate-800"
                 />
               </div>
               <div className="flex items-center pt-5">
                 <label className="flex items-center gap-2 cursor-pointer">
                   <input
                     type="checkbox"
                     checked={isBillable}
                     onChange={(e) => setIsBillable(e.target.checked)}
                     className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-500"
                   />
                   <span className="font-semibold text-xs">Is Client Billable?</span>
                 </label>
               </div>
             </div>

             <div className="mt-6 flex justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800">
               <button
                 type="button"
                 onClick={() => setShowModal(false)}
                 className="rounded-lg border border-slate-200 px-4 py-2 font-semibold hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800"
               >
                 Cancel
               </button>
               <button type="submit" className="rounded-lg bg-indigo-600 px-4 py-2 font-bold text-white hover:bg-indigo-700">
                 Submit Timesheet
               </button>
             </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
