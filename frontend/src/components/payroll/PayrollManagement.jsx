import React, { useEffect, useMemo, useState } from 'react';
import { Banknote, FileText, CheckCircle2, Calculator } from 'lucide-react';
import { api } from '../../services/api';

const currency = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
});

const formatMoney = (value) => currency.format(Number(value || 0));

const getTimeGreeting = (name = 'Employee') => {
  const hour = new Date().getHours();

  if (hour < 12) return `Good morning, ${name} 👋`;
  if (hour < 17) return `Good afternoon, ${name} 👋`;
  return `Good evening, ${name} 👋`;
};

const getCurrentDateLabel = () =>
  new Intl.DateTimeFormat('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date());

const getCurrentTimeLabel = () =>
  new Intl.DateTimeFormat('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date());

export const PayrollManagement = ({
  payrollRecords = [],
  payrollLoading = false,
  payrollError = null,
  userRole = 'EMPLOYEE',
  currentEmpId = null,
  currentEmpName = 'Employee',
}) => {
  const [selectedPayslip, setSelectedPayslip] = useState(null);
  const [animatedNetPay, setAnimatedNetPay] = useState(0);

  const safePayrollRecords = Array.isArray(payrollRecords) ? payrollRecords : [];
  const isHrAdmin = userRole === 'HR_ADMIN';
  const visiblePayrollRecords = isHrAdmin
    ? safePayrollRecords
    : safePayrollRecords.filter((record) => {
        const recordEmpId = record?.empId || record?.EmpID || record?.EmpId || record?.employeeId || null;
        return recordEmpId && currentEmpId && String(recordEmpId) === String(currentEmpId);
      });

  const summary = useMemo(() => {
    const latestRecord = [...visiblePayrollRecords].sort((a, b) => {
      const left = a?.PayrollMonth || a?.payrollMonth || a?.month || '0000-00';
      const right = b?.PayrollMonth || b?.payrollMonth || b?.month || '0000-00';
      return String(right).localeCompare(String(left));
    })[0] || null;

    const baseSalary = visiblePayrollRecords.reduce((acc, p) => acc + Number(p?.baseSalary ?? p?.BasicSalary ?? 0), 0);
    const overtimePay = visiblePayrollRecords.reduce((acc, p) => acc + Number(p?.overtimePay ?? p?.OvertimePay ?? 0), 0);
    const performanceBonus = visiblePayrollRecords.reduce((acc, p) => acc + Number(p?.performanceBonus ?? p?.bonus ?? p?.Bonus ?? 0), 0);
    const taxDeductions = visiblePayrollRecords.reduce((acc, p) => acc + Number(p?.taxDeductions ?? p?.tax ?? p?.Tax ?? 0), 0);
    const totalNet = visiblePayrollRecords.reduce((acc, p) => acc + Number(p?.netPay ?? p?.NetSalary ?? p?.netSalary ?? 0), 0);
    const currentNet = Number(latestRecord?.netPay ?? latestRecord?.NetSalary ?? latestRecord?.netSalary ?? (totalNet || 0));

    return {
      latestRecord,
      baseSalary,
      overtimePay,
      performanceBonus,
      taxDeductions,
      totalNet,
      currentNet,
    };
  }, [visiblePayrollRecords]);

  useEffect(() => {
    const targetValue = Number(summary.currentNet || summary.totalNet || 0);
    if (!targetValue) {
      setAnimatedNetPay(0);
      return undefined;
    }

    let frameId = null;
    const startTime = performance.now();
    const duration = 700;

    const animate = (now) => {
      const progress = Math.min((now - startTime) / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedNetPay(Math.round(targetValue * eased));

      if (progress < 1) {
        frameId = requestAnimationFrame(animate);
      }
    };

    frameId = requestAnimationFrame(animate);
    return () => {
      if (frameId) cancelAnimationFrame(frameId);
    };
  }, [summary.currentNet, summary.totalNet]);

  const totalEarnings = summary.baseSalary + summary.overtimePay + summary.performanceBonus;
  const totalDeductions = summary.taxDeductions || 0;
  const netPayValue = Number(summary.currentNet || summary.totalNet || 0);
  const payrollPeriodLabel = summary.latestRecord
    ? summary.latestRecord?.PayrollMonth || summary.latestRecord?.payrollMonth || summary.latestRecord?.month || 'Current Payroll Period'
    : 'Current Payroll Period';

  const employeeName = currentEmpName || 'Employee';
  const greeting = getTimeGreeting(employeeName);
  const currentDateLabel = getCurrentDateLabel();
  const currentTimeLabel = getCurrentTimeLabel();

  return (
    <div className="space-y-5">
      <div className="payroll-hero relative overflow-hidden rounded-[24px] border border-indigo-200/60 bg-gradient-to-br from-indigo-950 via-violet-950 to-slate-950 p-4 text-white shadow-[0_20px_60px_-30px_rgba(79,70,229,0.8)] dark:border-indigo-900/80">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(147,197,253,0.18),_transparent_30%),radial-gradient(circle_at_bottom_right,_rgba(45,212,191,0.14),_transparent_25%)]" />
        <div className="relative z-10 grid gap-4 xl:grid-cols-[1.5fr_0.85fr] xl:items-end">
          <div className="space-y-3">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.2em] text-indigo-100 backdrop-blur-sm">
              <Banknote className="h-3.5 w-3.5" />
              Payroll & Compensation
            </div>
            <div className="space-y-2">
              <h2 className="text-[1.75rem] font-bold tracking-[-0.04em] text-white sm:text-[2.1rem]">
                {greeting}
              </h2>
              <p className="max-w-xl text-sm text-indigo-100/80">
                Track your salary, earnings, deductions and payslips in one place.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-2 text-[10px] text-indigo-100/80">
              <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1">
                {currentEmpId ? `Employee ID • ${currentEmpId}` : 'Employee profile'}
              </span>
              <span className="rounded-full border border-white/15 bg-white/5 px-2.5 py-1">{currentDateLabel}</span>
              <span className="rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2.5 py-1 text-emerald-200">
                {payrollPeriodLabel}
              </span>
            </div>
          </div>

          <div className="grid gap-2 sm:grid-cols-2 xl:grid-cols-1">
            <div className="rounded-[18px] border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-100/70">Current time</div>
              <div className="mt-1 text-lg font-bold text-white">{currentTimeLabel}</div>
            </div>
            <div className="rounded-[18px] border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-100/70">Status</div>
              <div className="mt-1 inline-flex items-center gap-1 rounded-full border border-emerald-400/30 bg-emerald-500/10 px-2 py-1 text-[10px] font-bold uppercase tracking-[0.14em] text-emerald-200">
                <CheckCircle2 className="h-3 w-3" />
                {isHrAdmin ? 'Approved' : 'Current'}
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="payroll-card rounded-[24px] border border-slate-200 bg-white p-5 shadow-[0_25px_70px_-40px_rgba(15,23,42,0.35)] dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Net Pay</div>
              <div className="payroll-value mt-2 text-4xl font-black tracking-[-0.05em] text-slate-900 dark:text-white md:text-5xl">
                {formatMoney(animatedNetPay)}
              </div>
            </div>
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-300">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {isHrAdmin ? 'Approved' : 'Current'}
            </span>
          </div>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 dark:border-slate-700 dark:bg-slate-800/80">{payrollPeriodLabel}</span>
            <span className="rounded-full border border-slate-200 bg-slate-50 px-2.5 py-1 dark:border-slate-700 dark:bg-slate-800/80">{currentEmpId ? `Emp ID ${currentEmpId}` : 'Employee profile'}</span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-1">
          <div className="payroll-card rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_35px_-24px_rgba(79,70,229,0.5)] dark:border-slate-800 dark:bg-slate-900">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Gross Earnings</div>
            <div className="mt-2 text-2xl font-black tracking-[-0.04em] text-slate-900 dark:text-white">{formatMoney(totalEarnings)}</div>
            <div className="mt-1 text-[11px] text-slate-500">Base + overtime + bonus</div>
          </div>
          <div className="payroll-card rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_35px_-24px_rgba(79,70,229,0.5)] dark:border-slate-800 dark:bg-slate-900">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Overtime Earnings</div>
            <div className="mt-2 text-2xl font-black tracking-[-0.04em] text-indigo-600 dark:text-indigo-300">{formatMoney(summary.overtimePay)}</div>
            <div className="mt-1 text-[11px] text-emerald-600">Approved overtime</div>
          </div>
          <div className="payroll-card rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_35px_-24px_rgba(79,70,229,0.5)] dark:border-slate-800 dark:bg-slate-900">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Total Deductions</div>
            <div className="mt-2 text-2xl font-black tracking-[-0.04em] text-rose-600 dark:text-rose-300">-{formatMoney(totalDeductions)}</div>
            <div className="mt-1 text-[11px] text-slate-500">Tax and deductions</div>
          </div>
          <div className="payroll-card rounded-[20px] border border-slate-200 bg-white p-4 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-[0_18px_35px_-24px_rgba(79,70,229,0.5)] dark:border-slate-800 dark:bg-slate-900">
            <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Performance Bonus</div>
            <div className="mt-2 text-2xl font-black tracking-[-0.04em] text-emerald-600 dark:text-emerald-300">{formatMoney(summary.performanceBonus)}</div>
            <div className="mt-1 text-[11px] text-slate-500">Incentives & variable pay</div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="payroll-card rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 dark:border-slate-800">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Breakdown</div>
              <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Earnings and deductions</h3>
            </div>
            <div className="rounded-full bg-indigo-50 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-700 dark:bg-indigo-950/60 dark:text-indigo-300">
              Salary flow
            </div>
          </div>

          <div className="mt-4 space-y-3">
            <div className="rounded-[18px] border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Earnings</div>
                <div className="text-sm font-bold text-slate-900 dark:text-white">{formatMoney(totalEarnings)}</div>
              </div>
              <div className="mt-3 space-y-2 text-sm">
                <div className="flex items-center justify-between gap-3 text-slate-700 dark:text-slate-200">
                  <span>Base Salary</span>
                  <span className="font-semibold">{formatMoney(summary.baseSalary)}</span>
                </div>
                <div className="flex items-center justify-between gap-3 text-slate-700 dark:text-slate-200">
                  <span>Overtime Pay</span>
                  <span className="font-semibold">{formatMoney(summary.overtimePay)}</span>
                </div>
                <div className="flex items-center justify-between gap-3 text-slate-700 dark:text-slate-200">
                  <span>Performance Bonus</span>
                  <span className="font-semibold">{formatMoney(summary.performanceBonus)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-[18px] border border-rose-100 bg-rose-50 p-3 dark:border-rose-900/60 dark:bg-rose-950/20">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-rose-600">Deductions</div>
                <div className="text-sm font-bold text-rose-700 dark:text-rose-300">-{formatMoney(totalDeductions)}</div>
              </div>
              <div className="mt-3 space-y-2 text-sm text-slate-700 dark:text-slate-200">
                <div className="flex items-center justify-between gap-3">
                  <span>Tax deductions</span>
                  <span className="font-semibold">-{formatMoney(totalDeductions)}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>Other deductions</span>
                  <span className="font-semibold">-{formatMoney(0)}</span>
                </div>
              </div>
            </div>

            <div className="rounded-[18px] border border-emerald-100 bg-emerald-50 p-3 dark:border-emerald-900/60 dark:bg-emerald-950/20">
              <div className="flex items-center justify-between gap-3">
                <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-emerald-600">Net Pay</div>
                <div className="text-sm font-black text-emerald-700 dark:text-emerald-300">{formatMoney(netPayValue)}</div>
              </div>
            </div>
          </div>
        </div>

        <div className="payroll-card rounded-[24px] border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
          <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3 dark:border-slate-800">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">Summary</div>
              <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Payroll metrics</h3>
            </div>
            <Calculator className="h-4 w-4 text-indigo-500" />
          </div>

          <div className="mt-4 space-y-3">
            <div className="rounded-[18px] border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800/50">
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Gross Earnings</div>
              <div className="mt-1 text-xl font-black text-slate-900 dark:text-white">{formatMoney(totalEarnings)}</div>
            </div>
            <div className="rounded-[18px] border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800/50">
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Overtime Earnings</div>
              <div className="mt-1 text-xl font-black text-indigo-600 dark:text-indigo-300">{formatMoney(summary.overtimePay)}</div>
            </div>
            <div className="rounded-[18px] border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-800/50">
              <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Net Pay</div>
              <div className="mt-1 text-xl font-black text-emerald-600 dark:text-emerald-300">{formatMoney(netPayValue)}</div>
            </div>
          </div>
        </div>
      </div>

      <div className="payroll-card rounded-[24px] border border-slate-200/80 bg-white p-5 shadow-sm dark:border-slate-800/80 dark:bg-slate-900">
        <div className="flex flex-col gap-3 pb-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <div className="text-[10px] font-bold uppercase tracking-[0.2em] text-slate-500">History</div>
            <h3 className="mt-1 text-lg font-bold text-slate-900 dark:text-white">Payslip history</h3>
          </div>
        </div>

        {payrollLoading && <div className="mt-4 text-sm text-slate-500">Loading payroll...</div>}
        {!payrollLoading && payrollError && (
          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            {payrollError}
          </div>
        )}

        {!payrollLoading && !payrollError && (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-[0.14em] dark:border-slate-700">
                  <th className="px-2 py-3 font-bold">Payroll Month</th>
                  <th className="px-2 py-3 font-bold">Base Salary</th>
                  <th className="px-2 py-3 font-bold">Overtime</th>
                  <th className="px-2 py-3 font-bold">Bonus</th>
                  <th className="px-2 py-3 font-bold">Deductions</th>
                  <th className="px-2 py-3 font-bold">Net Pay</th>
                  <th className="px-2 py-3 text-right font-bold">Payslip</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {visiblePayrollRecords.length === 0 ? (
                  <tr>
                    <td colSpan="7" className="px-2 py-8 text-center text-sm text-slate-500">No payroll records available.</td>
                  </tr>
                ) : (
                  visiblePayrollRecords.map((p) => {
                    const monthDisplay = p?.PayrollMonth || p?.payrollMonth || p?.month || 'N/A';
                    const baseSalary = Number(p?.baseSalary ?? p?.BasicSalary ?? 0);
                    const overtimePay = Number(p?.overtimePay ?? p?.OvertimePay ?? 0);
                    const performanceBonus = Number(p?.performanceBonus ?? p?.bonus ?? p?.Bonus ?? 0);
                    const taxDeductions = Number(p?.taxDeductions ?? p?.tax ?? p?.Tax ?? 0);
                    const netPay = Number(p?.netPay ?? p?.NetSalary ?? p?.netSalary ?? 0);

                    return (
                      <tr key={p?.id || `${p?.empId || 'unknown'}-${monthDisplay}`} className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800/50">
                        <td className="px-2 py-3 font-bold text-slate-900 dark:text-white">{monthDisplay}</td>
                        <td className="px-2 py-3 text-slate-700 dark:text-slate-200">{formatMoney(baseSalary)}</td>
                        <td className="px-2 py-3 text-slate-700 dark:text-slate-200">{formatMoney(overtimePay)}</td>
                        <td className="px-2 py-3 font-semibold text-emerald-600 dark:text-emerald-300">+{formatMoney(performanceBonus)}</td>
                        <td className="px-2 py-3 font-medium text-rose-600 dark:text-rose-300">-{formatMoney(taxDeductions)}</td>
                        <td className="px-2 py-3 font-black text-slate-900 dark:text-white">{formatMoney(netPay)}</td>
                        <td className="px-2 py-3 text-right">
                          <button
                            onClick={() => setSelectedPayslip(p)}
                            className="inline-flex items-center gap-2 rounded-xl bg-indigo-50 px-3 py-2 text-[11px] font-bold uppercase tracking-[0.12em] text-indigo-700 transition-colors hover:bg-indigo-100 dark:bg-indigo-950/60 dark:text-indigo-300 dark:hover:bg-indigo-900"
                          >
                            <FileText className="h-3.5 w-3.5" />
                            View Payslip
                          </button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {selectedPayslip && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4 backdrop-blur-sm">
          <div className="w-full max-w-lg rounded-[24px] bg-white p-6 shadow-2xl dark:bg-slate-900 dark:text-white">
            <div className="flex items-center justify-between border-b border-slate-100 pb-4 dark:border-slate-800">
              <div>
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">Payslip</div>
                <h3 className="mt-1 text-base font-bold text-slate-900 dark:text-white">NEXUS ENTERPRISE PAYSLIP</h3>
                <p className="mt-1 text-xs text-slate-500">Pay Period: {selectedPayslip.PayrollMonth || selectedPayslip.payrollMonth || selectedPayslip.month || 'N/A'}</p>
              </div>
              <button onClick={() => setSelectedPayslip(null)} className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-700 dark:border-slate-700 dark:text-slate-200">Close</button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="grid grid-cols-2 gap-2 rounded-[18px] bg-slate-50 p-3 dark:bg-slate-800/60">
                <div>
                  <span className="block text-slate-500">Employee</span>
                  <span className="mt-1 block text-sm font-bold text-slate-900 dark:text-white">{selectedPayslip.empName || selectedPayslip.empId || currentEmpName || 'N/A'}</span>
                </div>
                <div>
                  <span className="block text-slate-500">Designation</span>
                  <span className="mt-1 block font-bold text-slate-900 dark:text-white">{selectedPayslip.designation || '-'}</span>
                </div>
              </div>

              <div>
                <h4 className="mb-2 border-b border-slate-200 pb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-emerald-600 dark:border-slate-700 dark:text-emerald-300">Earnings</h4>
                <div className="space-y-1.5">
                  <div className="flex justify-between gap-3"><span>Base Salary</span><span className="font-semibold">{formatMoney(selectedPayslip.baseSalary ?? selectedPayslip.BasicSalary ?? 0)}</span></div>
                  <div className="flex justify-between gap-3"><span>Overtime Pay</span><span className="font-semibold">{formatMoney(selectedPayslip.overtimePay ?? selectedPayslip.OvertimePay ?? 0)}</span></div>
                  <div className="flex justify-between gap-3"><span>Performance Bonus</span><span className="font-semibold">{formatMoney(selectedPayslip.performanceBonus ?? selectedPayslip.bonus ?? selectedPayslip.Bonus ?? 0)}</span></div>
                </div>
              </div>

              <div>
                <h4 className="mb-2 border-b border-slate-200 pb-1 text-[10px] font-bold uppercase tracking-[0.18em] text-rose-600 dark:border-slate-700 dark:text-rose-300">Deductions</h4>
                <div className="space-y-1.5">
                  <div className="flex justify-between gap-3"><span>Income Tax</span><span className="font-semibold text-rose-600">-{formatMoney(selectedPayslip.taxDeductions ?? selectedPayslip.tax ?? selectedPayslip.Tax ?? 0)}</span></div>
                  <div className="flex justify-between gap-3"><span>Other deductions</span><span className="font-semibold text-rose-600">-{formatMoney(0)}</span></div>
                </div>
              </div>

              <div className="rounded-[18px] bg-indigo-50 p-3 dark:bg-indigo-950/60">
                <div className="flex items-center justify-between gap-3">
                  <span className="text-[10px] font-bold uppercase tracking-[0.18em] text-indigo-700 dark:text-indigo-200">Total Net Pay</span>
                  <span className="text-lg font-black text-indigo-700 dark:text-indigo-300">{formatMoney(selectedPayslip.netPay ?? selectedPayslip.NetSalary ?? selectedPayslip.netSalary ?? 0)}</span>
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                onClick={async () => {
                  try {
                    const empId = selectedPayslip?.empId || selectedPayslip?.EmpID || selectedPayslip?.EmpId || selectedPayslip?.employeeId;
                    const month = selectedPayslip?.PayrollMonth || selectedPayslip?.payrollMonth || selectedPayslip?.month || 'current';
                    if (!empId) {
                      alert('Unable to determine employee ID for this payslip.');
                      return;
                    }
                    const blob = await api.downloadPayslip(empId, month);
                    const url = window.URL.createObjectURL(blob);
                    const filename = `Nexus_Payslip_${empId}_${String(month).replace(/\s+/g, '_')}.pdf`;
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    a.remove();
                    window.URL.revokeObjectURL(url);
                  } catch (err) {
                    console.error('Payslip download failed', err);
                    alert('Failed to download payslip. Please try again or contact support.');
                  }
                }}
                className="rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold uppercase tracking-[0.12em] text-white hover:bg-indigo-700"
              >
                Download PDF
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
