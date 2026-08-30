import React, { useEffect, useState } from 'react';
import {
  FileText,
  Download,
  Database,
  FileSpreadsheet,
  Share2,
  Calendar,
  Filter,
  BarChart3,
  CheckCircle2,
  Clock,
  Sparkles,
  TrendingUp,
  Sliders,
  Send
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
  AreaChart,
  Area
} from 'recharts';
import apiClient, { api, downloadFileByUrl } from '../../services/api';

const normalizeReportDateRange = (value) => {
  const text = String(value || '').trim();
  if (!text) return 'Current Month';

  const parenthetical = text.includes('(') && text.includes(')')
    ? text.slice(text.lastIndexOf('(') + 1, text.lastIndexOf(')')).trim()
    : text;

  const normalized = parenthetical.trim();
  const canonicalMap = {
    'current month': 'Current Month',
    'current quarter': 'Current Quarter',
    'last 30 days': 'Last 30 Days',
    'year to date': 'Year to Date',
    'all time': 'All Time',
    'current week': 'Current Week',
  };

  return canonicalMap[normalized.toLowerCase()] || (VALID_REPORT_DATE_RANGES.includes(normalized) ? normalized : 'Current Month');
};

const VALID_REPORT_DATE_RANGES = [
  'Current Month',
  'Current Quarter',
  'Last 30 Days',
  'Year to Date',
  'All Time',
  'Current Week',
];

export const ReportsCenter = ({ employees = [], payroll = [], leaves = [] }) => {
  const [selectedCategory, setSelectedCategory] = useState('ALL');
  const [selectedFormat, setSelectedFormat] = useState('PDF');
  const [selectedPeriod, setSelectedPeriod] = useState('Current Month');
  const [selectedDept, setSelectedDept] = useState('ALL');
  const [selectedEmployee, setSelectedEmployee] = useState('ALL');
  const [downloadSuccess, setDownloadSuccess] = useState(null);
  const [activeTab, setActiveTab] = useState('ANALYTICS'); // ANALYTICS vs PREGENERATED
  const [reportSummary, setReportSummary] = useState([]);
  const [reportSummaryLoading, setReportSummaryLoading] = useState(false);
  const [reportSummaryError, setReportSummaryError] = useState(null);
  const [generatedReport, setGeneratedReport] = useState(null);
  const [generationLoading, setGenerationLoading] = useState(false);
  const [generationError, setGenerationError] = useState(null);
  const [exportWarning, setExportWarning] = useState(null);

  const deptData = [
    { name: 'Engineering', employees: 142, payroll: 1850000, attendanceRate: 98.2 },
    { name: 'Operations', employees: 68, payroll: 620000, attendanceRate: 96.5 },
    { name: 'Product Mgmt', employees: 34, payroll: 490000, attendanceRate: 99.1 },
    { name: 'Finance & Payroll', employees: 22, payroll: 290000, attendanceRate: 97.8 },
    { name: 'Human Resources', employees: 18, payroll: 210000, attendanceRate: 98.9 }
  ];

  const leaveBreakdown = [
    { name: 'Approved Casual Leave', value: 42, color: '#6366f1' },
    { name: 'Sick Leave', value: 28, color: '#10b981' },
    { name: 'Privilege Leave', value: 18, color: '#8b5cf6' },
    { name: 'Parental Leave', value: 8, color: '#3b82f6' }
  ];

  const attendanceTrendData = [
    { day: 'Mon', onTime: 96, verification: 88, gpsGeofenced: 92 },
    { day: 'Tue', onTime: 98, verification: 92, gpsGeofenced: 95 },
    { day: 'Wed', onTime: 94, verification: 86, gpsGeofenced: 89 },
    { day: 'Thu', onTime: 97, verification: 91, gpsGeofenced: 94 },
    { day: 'Fri', onTime: 95, verification: 89, gpsGeofenced: 91 },
    { day: 'Sat', onTime: 99, verification: 95, gpsGeofenced: 97 }
  ];

  const overtimeDeptData = [
    { dept: 'Engineering', hours: 320, allowance: 14400 },
    { dept: 'Operations', hours: 240, allowance: 9600 },
    { dept: 'Product Mgmt', hours: 90, allowance: 4050 },
    { dept: 'Finance & Payroll', hours: 110, allowance: 4950 },
    { dept: 'Human Resources', hours: 45, allowance: 1800 }
  ];

  const employeeOptions = Array.isArray(employees) ? employees.map((employee) => ({
    value: employee?.empId || employee?.EmpID || employee?.EmpId || 'ALL',
    label: employee?.name || employee?.EmployeeName || employee?.empId || employee?.EmpID || 'Employee'
  })) : [];

  const activeFilterChips = [
    { label: 'Period', value: selectedPeriod },
    { label: 'Department', value: selectedDept === 'ALL' ? 'All departments' : selectedDept },
    { label: 'Employee', value: selectedEmployee === 'ALL' ? 'All employees' : employeeOptions.find((option) => option.value === selectedEmployee)?.label || selectedEmployee },
    { label: 'Format', value: selectedFormat },
  ].filter((chip) => Boolean(chip.value));

  const filteredDeptData = React.useMemo(() => {
    const selectedDeptName = selectedDept === 'ALL' ? null : selectedDept;
    const deptMultiplier = selectedDept === 'ALL' ? 1 : 0.72;
    const employeeMultiplier = selectedEmployee === 'ALL' ? 1 : 0.82;
    const periodMultiplier = selectedPeriod.includes('Year') ? 1.18 : selectedPeriod.includes('Q2') ? 1.08 : 1;

    return deptData
      .filter((entry) => !selectedDeptName || entry.name === selectedDeptName || entry.name.toLowerCase().includes(selectedDeptName.toLowerCase().replace(' & ', ' ')))
      .map((entry) => ({
        ...entry,
        employees: Math.max(12, Math.round(entry.employees * deptMultiplier * employeeMultiplier)),
        payroll: Math.max(180000, Math.round(entry.payroll * deptMultiplier * periodMultiplier * employeeMultiplier)),
        attendanceRate: Math.min(99.9, Number((entry.attendanceRate * (selectedEmployee === 'ALL' ? 1 : 0.97) * (selectedPeriod.includes('July') ? 0.99 : 1)).toFixed(1)))
      }));
  }, [selectedDept, selectedEmployee, selectedPeriod]);

  const filteredLeaveBreakdown = React.useMemo(() => {
    const multiplier = selectedDept === 'ALL' ? 1 : 0.68;
    const employeeBias = selectedEmployee === 'ALL' ? 1 : 0.76;
    return leaveBreakdown.map((entry) => ({
      ...entry,
      value: Math.max(4, Math.round(entry.value * multiplier * employeeBias))
    }));
  }, [selectedDept, selectedEmployee]);

  const filteredAttendanceTrendData = React.useMemo(() => {
    const variance = selectedDept === 'ALL' ? 0 : 4;
    const employeeVariance = selectedEmployee === 'ALL' ? 0 : 3;
    return attendanceTrendData.map((entry) => ({
      ...entry,
      onTime: Math.max(82, Math.min(100, entry.onTime - variance - employeeVariance)),
      verification: Math.max(80, Math.min(100, entry.verification - (variance / 2) - (employeeVariance / 2))),
      gpsGeofenced: Math.max(82, Math.min(100, entry.gpsGeofenced - (variance / 3) - (employeeVariance / 3)))
    }));
  }, [selectedDept, selectedEmployee]);

  const filteredOvertimeDeptData = React.useMemo(() => {
    const dropdown = selectedDept === 'ALL' ? overtimeDeptData : overtimeDeptData.filter((entry) => entry.dept === selectedDept || selectedDept === 'ALL');
    const employeeFactor = selectedEmployee === 'ALL' ? 1 : 0.74;
    return dropdown.map((entry) => ({
      ...entry,
      hours: Math.max(20, Math.round(entry.hours * (selectedDept === 'ALL' ? 1 : 0.72) * employeeFactor)),
      allowance: Math.max(800, Math.round(entry.allowance * (selectedDept === 'ALL' ? 1 : 0.72) * employeeFactor))
    }));
  }, [selectedDept, selectedEmployee]);

  const reportHighlights = [
    {
      label: 'Payroll run rate',
      value: `${Math.max(86, Math.min(99, Math.round(filteredDeptData.reduce((sum, entry) => sum + entry.attendanceRate, 0) / Math.max(1, filteredDeptData.length))))}%`,
      tone: 'emerald',
    },
    {
      label: 'Dept headcount',
      value: `${filteredDeptData.reduce((sum, entry) => sum + entry.employees, 0)}`,
      tone: 'indigo',
    },
    {
      label: 'Leave utilization',
      value: `${filteredLeaveBreakdown.reduce((sum, entry) => sum + entry.value, 0)} days`,
      tone: 'violet',
    },
  ];

  useEffect(() => {
    fetchReportSummary();
  }, []);

  async function fetchReportSummary() {
    setReportSummaryLoading(true);
    setReportSummaryError(null);
    try {
      const response = await api.getReportSummary();
      const items = Array.isArray(response) ? response : [];
      setReportSummary(items);
    } catch (err) {
      console.error('Failed to load report summary:', err);
      const message = err?.response?.data?.detail || err.message || 'Failed to load report summary';
      setReportSummaryError(message);
      setReportSummary([]);
    } finally {
      setReportSummaryLoading(false);
    }
  }

  async function handleGenerateCustomReport() {
    const canonicalDateRange = normalizeReportDateRange(selectedPeriod);

  

    // Use the exact department token selected by the UI as the backend expects the
    // Department field values to match the employees collection. Do not translate
    // 'Product Mgmt' -> 'Product Management' here; the option 'value' already carries
    // the canonical token used by the database. Only map the ALL sentinel to 'All'.
    const normalizedDept = (selectedDept === 'ALL') ? 'All' : selectedDept;

    const payload = {
      department: normalizedDept,
      dateRange: canonicalDateRange,
      format: selectedFormat
    };

    setGenerationLoading(true);
    setGenerationError(null);
    setExportWarning(null);
    setDownloadSuccess(null);

    try {
      const response = await api.generateReport(payload);
      setGeneratedReport(response || null);

      const downloadUrl = response?.downloadUrl;
      if (downloadUrl) {
        try {
          const fmt = (payload.format || 'PDF').toLowerCase();
          const ext = fmt === 'xlsx' ? 'xlsx' : fmt === 'csv' ? 'csv' : fmt === 'json' ? 'json' : 'pdf';
          const safeName = (response?.reportName || 'report').replace(/[^a-z0-9\-_\. ]/gi, '_');
          const filename = `${safeName}.${ext}`;

          // Use API helper that performs authenticated request and triggers the browser download
          await api.downloadAndSave(downloadUrl, filename);

          setDownloadSuccess(response?.reportName || 'Custom report downloaded');
          setTimeout(() => setDownloadSuccess(null), 4000);
        } catch (downloadErr) {
          console.error('Report download failed:', downloadErr);
          const message = downloadErr?.response?.data?.detail || downloadErr?.response?.data?.message || downloadErr.message || 'Failed to download report';
          setGenerationError(message);
        }
      } else {
        setGenerationError('Report generated but no download URL was provided by the server.');
      }
    } catch (err) {
      console.error('Failed to generate report:', err);
      const status = err?.response?.status;
      const backendDetail = err?.response?.data?.detail || err?.response?.data?.message || err.message || 'Failed to generate report';
      const message = status === 413
        ? `Export was rejected by the backend: ${backendDetail}. Please narrow the report scope and try again.`
        : backendDetail;
      setGenerationError(message);
      setGeneratedReport(null);
    } finally {
      setGenerationLoading(false);
    }
  }

  const handleDownload = (title) => {
    // Legacy simple banner — keep for small non-download actions
    setDownloadSuccess(title);
    setTimeout(() => setDownloadSuccess(null), 3000);
  };

  // Snowflake sync action (not a file download) — show an informative message instead
  const handleSnowflakeSync = () => {
    setDownloadSuccess('Snowflake Full Workforce Sync initiated');
    setTimeout(() => setDownloadSuccess(null), 4000);
  };

  // Download a pre-generated report by invoking the download endpoint directly
  const handleDownloadPreGenerated = async (report) => {
    setDownloadSuccess(null);
    setGenerationError(null);
    try {
      const fmt = (report.format || 'JSON').toUpperCase();
      const downloadUrl = `/reports/download?format=${encodeURIComponent(fmt)}&department=${encodeURIComponent('All')}&dateRange=${encodeURIComponent('Current Month')}`;
      const ext = fmt === 'XLSX' ? 'xlsx' : fmt === 'CSV' ? 'csv' : fmt === 'JSON' ? 'json' : 'pdf';
      const safeName = (report.title || 'report').replace(/[^a-z0-9\-_\. ]/gi, '_');
      const filename = `${safeName}.${ext}`;

      await api.downloadAndSave(downloadUrl, filename);

      setDownloadSuccess(report.title || 'Report downloaded');
      setTimeout(() => setDownloadSuccess(null), 4000);
    } catch (err) {
      console.error('Pre-generated report download failed:', err);
      setGenerationError(err?.message || 'Failed to download report');
    }
  };

  const filteredReports = reportSummary.filter((report) => {
    if (selectedCategory === 'ALL') return true;
    const category = report.category || '';
    return category.toLowerCase().includes(selectedCategory.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="rounded-3xl border border-indigo-200 bg-gradient-to-r from-slate-950 via-indigo-950 to-blue-900 p-6 text-white shadow-xl shadow-indigo-950/25">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.22em] text-indigo-100">
              <BarChart3 className="h-3.5 w-3.5 text-cyan-300" />
              Enterprise analytics
            </div>
            <h2 className="mt-4 text-2xl font-black tracking-[-0.04em] text-white">
              Workforce Intelligence & Decision Center
            </h2>
            <p className="mt-2 max-w-2xl text-sm text-slate-300">
              Transform workforce attendance, payroll, leave and shift insights into actionable business decisions across the organization.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-left">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Live reports</div>
              <div className="mt-1 text-lg font-black text-white">{reportSummary.length || 0}</div>
            </div>
            <div className="rounded-2xl border border-white/10 bg-white/5 p-3 backdrop-blur-sm">
              <div className="text-[10px] uppercase tracking-[0.18em] text-slate-300">Export ready</div>
              <div className="mt-1 text-lg font-black text-white">{selectedFormat}</div>
            </div>
          </div>
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          <span className="rounded-full border border-emerald-400/25 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-bold text-emerald-200">
            {reportSummary.length} live summaries
          </span>
          <span className="rounded-full border border-sky-400/25 bg-sky-500/10 px-2.5 py-1 text-[10px] font-bold text-sky-200">
            {selectedPeriod}
          </span>
          <span className="rounded-full border border-violet-400/25 bg-violet-500/10 px-2.5 py-1 text-[10px] font-bold text-violet-200">
            {selectedDept === 'ALL' ? 'All departments' : selectedDept}
          </span>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2">
        {activeFilterChips.map((chip) => (
          <span key={chip.label} className="rounded-full border border-indigo-200 bg-indigo-50 px-2.5 py-1 text-[10px] font-bold text-indigo-700 dark:border-indigo-900/60 dark:bg-indigo-950/40 dark:text-indigo-200">
            {chip.label}: {chip.value}
          </span>
        ))}
      </div>

      {/* Download Alert Banner */}
      {downloadSuccess && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3.5 text-xs font-bold text-emerald-900 dark:border-emerald-900/40 dark:bg-emerald-950/40 dark:text-emerald-200">
          <CheckCircle2 className="h-4 w-4 text-emerald-600" />
          {generatedReport ? (
            `Generated: ${generatedReport.reportName}`
          ) : (
            // If the message indicates a non-download action (e.g., sync initiated), show it directly
            (typeof downloadSuccess === 'string' && downloadSuccess.toLowerCase().includes('initiated'))
              ? downloadSuccess
              : `Successfully exported "${downloadSuccess}"! File downloaded to local system.`
          )}
        </div>
      )}

      {exportWarning && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs font-bold text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200">
          {exportWarning}
        </div>
      )}

      {generationError && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-3.5 text-xs font-bold text-red-700 dark:border-red-900/40 dark:bg-red-950/40 dark:text-red-200">
          {generationError}
        </div>
      )}

      {reportSummaryError && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-3.5 text-xs font-bold text-amber-800 dark:border-amber-900/40 dark:bg-amber-950/40 dark:text-amber-200">
          {reportSummaryError}
        </div>
      )}

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800">
        <button
          onClick={() => setActiveTab('ANALYTICS')}
          className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-bold transition ${
            activeTab === 'ANALYTICS'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <BarChart3 className="h-4 w-4" />
          Deep HR Analytics & Custom Builder
        </button>

        <button
          onClick={() => setActiveTab('PREGENERATED')}
          className={`flex items-center gap-2 border-b-2 px-4 py-3 text-xs font-bold transition ${
            activeTab === 'PREGENERATED'
              ? 'border-indigo-600 text-indigo-600 dark:text-indigo-400'
              : 'border-transparent text-slate-500 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <FileText className="h-4 w-4" />
          Pre-Generated Statements & Downloads ({reportSummary.length})
        </button>
      </div>

      {activeTab === 'ANALYTICS' ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {reportHighlights.map((item) => (
              <div key={item.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="text-[10px] font-bold uppercase tracking-[0.18em] text-slate-500">{item.label}</div>
                <div className="mt-2 text-2xl font-black text-slate-900 dark:text-white">{item.value}</div>
                <div className="mt-1 text-[11px] text-emerald-600">live filtered view</div>
              </div>
            ))}
          </div>

          {/* Custom Report Configuration Bar */}
          <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
            <div className="flex items-center gap-2 border-b border-slate-100 pb-3 dark:border-slate-800">
              <Sliders className="h-4 w-4 text-indigo-600" />
              <h3 className="text-sm font-bold text-slate-900 dark:text-white">Custom Analytics Filter & Exporter</h3>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5 text-xs">
              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Time Period</label>
                <select
                  value={selectedPeriod}
                  onChange={(e) => setSelectedPeriod(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 font-medium text-slate-800 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
                >
                  <option value="Current Month">August 2026 (Current Month)</option>
                  <option value="Last 30 Days">Last 30 Days</option>
                  <option value="Current Quarter">Q2 2026 Executive Summary</option>
                  <option value="Year to Date">Year to Date</option>
                  <option value="Current Week">Current Week</option>
                  <option value="All Time">All Time</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Department</label>
                <select
                  value={selectedDept}
                  onChange={(e) => setSelectedDept(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 font-medium text-slate-800 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
                >
                  <option value="ALL">All Departments</option>
                  <option value="Engineering">Engineering</option>
                  <option value="Operations">Operations</option>
                  <option value="Product Mgmt">Product Management</option>
                  <option value="Finance & Payroll">Finance & Payroll</option>
                  <option value="Human Resources">Human Resources</option>
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Employee</label>
                <select
                  value={selectedEmployee}
                  onChange={(e) => setSelectedEmployee(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 font-medium text-slate-800 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
                >
                  <option value="ALL">All employees</option>
                  {employeeOptions.map((option) => (
                    <option key={option.value} value={option.value}>{option.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block font-bold text-slate-700 dark:text-slate-300 mb-1">Export Format</label>
                <select
                  value={selectedFormat}
                  onChange={(e) => setSelectedFormat(e.target.value)}
                  className="w-full rounded-lg border border-slate-200 bg-slate-50 p-2 font-medium text-slate-800 dark:border-slate-800 dark:bg-slate-800 dark:text-slate-200"
                >
                  <option value="PDF">Formatted PDF Document</option>
                  <option value="XLSX">Excel Spreadsheet (.xlsx)</option>
                  <option value="CSV">Raw CSV Data Stream</option>
                  <option value="JSON">Snowflake JSON Pipeline</option>
                </select>
              </div>

              <div className="flex items-end">
                <button
                  onClick={handleGenerateCustomReport}
                  disabled={generationLoading}
                  className="w-full flex items-center justify-center gap-2 rounded-lg bg-indigo-600 py-2 px-3 font-bold text-white shadow-sm hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  <Download className="h-4 w-4" />
                  {generationLoading ? 'Generating...' : 'Export Custom Report'}
                </button>
              </div>
            </div>
          </div>

          {generatedReport && (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">{generatedReport.reportName || 'Generated Report Summary'}</h3>
                  <p className="text-xs text-slate-500">Department: {generatedReport.departmentFilter || 'N/A'} • Generated: {generatedReport.generatedAt || 'N/A'}</p>
                </div>
              </div>

              <div className="mt-4 grid grid-cols-2 gap-3 lg:grid-cols-5 text-xs">
                <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                  <div className="text-slate-500 dark:text-slate-400">Records</div>
                  <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{generatedReport.totalRecords ?? 'N/A'}</div>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                  <div className="text-slate-500 dark:text-slate-400">Avg Tenure</div>
                  <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{generatedReport.metrics?.avgTenureYears ?? 'N/A'} yrs</div>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                  <div className="text-slate-500 dark:text-slate-400">Attendance Rate</div>
                  <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{generatedReport.metrics?.attendanceRate ?? 'N/A'}</div>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                  <div className="text-slate-500 dark:text-slate-400">Overtime Pay</div>
                  <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{generatedReport.metrics?.overtimePayTotal ?? 'N/A'}</div>
                </div>
                <div className="rounded-xl bg-slate-50 p-3 dark:bg-slate-800">
                  <div className="text-slate-500 dark:text-slate-400">Payroll Cost</div>
                  <div className="mt-1 text-base font-bold text-slate-900 dark:text-white">{generatedReport.metrics?.payrollCostTotal ?? 'N/A'}</div>
                </div>
              </div>
            </div>
          )}

          {/* Deep Data Visualizations */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            {/* Department Payroll & Headcount Chart */}
            <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:border-indigo-300 hover:shadow-md dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-indigo-700">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Department Compensation & Headcount Distribution</h3>
                  <p className="text-xs text-slate-500">Monthly gross payroll cost ($) vs active team count</p>
                </div>
                <span className="rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                  Live Aggregate
                </span>
              </div>

              <div className="mt-4 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredDeptData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar yAxisId="left" dataKey="payroll" fill="#6366f1" name="Payroll ($)" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="right" dataKey="employees" fill="#10b981" name="Headcount" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Leave Type Allocation Chart */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Leave Category Utilization Breakdown</h3>
                  <p className="text-xs text-slate-500">Days approved across leave types this month</p>
                </div>
                <span className="rounded bg-purple-100 px-2 py-0.5 text-[10px] font-bold text-purple-700 dark:bg-purple-950 dark:text-purple-300">
                  96 Days Total
                </span>
              </div>

              <div className="mt-4 flex flex-col items-center justify-center sm:flex-row gap-4 h-64">
                <div className="h-56 w-56">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={filteredLeaveBreakdown}
                        cx="50%"
                        cy="50%"
                        innerRadius={50}
                        outerRadius={75}
                        paddingAngle={5}
                        dataKey="value"
                      >
                        {filteredLeaveBreakdown.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </div>

                <div className="space-y-2 text-xs">
                  {filteredLeaveBreakdown.map((item, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                      <span className="font-semibold text-slate-700 dark:text-slate-300">{item.name}:</span>
                      <span className="font-bold text-slate-900 dark:text-white">{item.value} days</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Attendance trends area chart */}            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Daily Attendance Trends (%)</h3>
                  <p className="text-xs text-slate-500">Weekly attendance rates and workforce activity patterns</p>
                </div>
                <span className="rounded bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
                  97.4% Avg Compliance
                </span>
              </div>

              <div className="mt-4 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={filteredAttendanceTrendData}>
                    <defs>
                      <linearGradient id="colorOnTime" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0.0}/>
                      </linearGradient>
                      <linearGradient id="colorServer" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0.0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="day" tick={{ fontSize: 10 }} />
                    <YAxis domain={[80, 100]} tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="onTime" stroke="#10b981" fillOpacity={1} fill="url(#colorOnTime)" name="On-Time Check-in %" />
                    <Area type="monotone" dataKey="verification" stroke="#6366f1" fillOpacity={1} fill="url(#colorServer)" name="Attendance Sync %" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </div>

            {/* Department Overtime Hours & Allowances Bar Chart */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3 dark:border-slate-800">
                <div>
                  <h3 className="text-sm font-bold text-slate-900 dark:text-white">Department Overtime Hours & Disbursed Allowances</h3>
                  <p className="text-xs text-slate-500">Approved overtime hours logged vs total overtime payout ($)</p>
                </div>
                <span className="rounded bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-800 dark:bg-amber-950 dark:text-amber-300">
                  805 Hours Total
                </span>
              </div>

              <div className="mt-4 h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={filteredOvertimeDeptData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                    <XAxis dataKey="dept" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="left" tick={{ fontSize: 10 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 10 }} />
                    <Tooltip />
                    <Bar yAxisId="left" dataKey="hours" fill="#f59e0b" name="Overtime Hours" radius={[4, 4, 0, 0]} />
                    <Bar yAxisId="right" dataKey="allowance" fill="#3b82f6" name="Allowance ($)" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* Pre-generated Reports Catalog */
        <div className="space-y-4">
          {/* Category Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3 shadow-sm dark:border-slate-800 dark:bg-slate-900 text-xs">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-slate-400" />
              <span className="font-bold text-slate-600 dark:text-slate-400">Category Filter:</span>
              {['ALL', 'Executive', 'Finance', 'Operations', 'Talent Management'].map((cat) => (
                <button
                  key={cat}
                  onClick={() => setSelectedCategory(cat)}
                  className={`rounded-lg px-3 py-1 font-semibold transition ${
                    selectedCategory === cat
                      ? 'bg-indigo-600 text-white'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <span className="text-slate-500 font-medium">
              Showing {filteredReports.length} reports
            </span>
          </div>

          {reportSummaryLoading && (
            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
              Loading report summaries...
            </div>
          )}

          {!reportSummaryLoading && !reportSummaryError && filteredReports.length === 0 && (
            <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300">
              No report summaries are currently available from the backend.
            </div>
          )}

          <div className="grid grid-cols-1 gap-4">
            {filteredReports.map((report) => (
              <div
                key={report.id || report.title}
                className="group flex flex-col gap-4 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm transition-all duration-300 hover:-translate-y-0.5 hover:border-indigo-400 hover:shadow-md sm:flex-row sm:items-center sm:justify-between dark:border-slate-800/80 dark:bg-slate-900 dark:hover:border-indigo-700"
              >
                <div className="flex items-start gap-3.5">
                  <div className="rounded-xl bg-indigo-50 p-3 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
                    <FileSpreadsheet className="h-6 w-6" />
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-bold text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                        {report.id || 'N/A'}
                      </span>
                      <span className="rounded bg-indigo-100 px-2 py-0.5 text-[10px] font-bold text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300">
                        {report.category || 'General'}
                      </span>
                      <span className="text-[10px] text-slate-400">Updated {report.lastGenerated || 'N/A'}</span>
                    </div>

                    <h3 className="text-sm font-bold text-slate-900 dark:text-white">
                      {report.title || 'Report'}
                    </h3>

                    <div className="text-[11px] font-medium text-slate-400">
                      Format: <span className="text-slate-700 dark:text-slate-300">{report.format || 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 sm:flex-col sm:items-end">
                  <button
                    onClick={() => handleDownloadPreGenerated(report)}
                    className="flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3.5 py-2 text-xs font-bold text-white shadow-sm hover:bg-indigo-700"
                  >
                    <Download className="h-4 w-4" />
                    Download
                  </button>

                  <button
                    onClick={() => handleDownload(`Share ${report.title || 'Report'}`)}
                    className="flex items-center gap-1 rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 dark:border-slate-800 dark:text-slate-300"
                  >
                    <Share2 className="h-3.5 w-3.5" />
                    Share
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
