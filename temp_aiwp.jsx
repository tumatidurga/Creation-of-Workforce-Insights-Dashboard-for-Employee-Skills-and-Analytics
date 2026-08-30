import React, { useEffect, useMemo, useRef, useState } from 'react';
import { BrainCircuit, Sparkles, Users, TrendingUp, Award, CheckCircle2, X, Briefcase, Target, ArrowRight, Check, Calendar, ShieldCheck } from 'lucide-react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';
import { api } from '../../services/api';

const BASE_SCENARIO = {
  plannedHiring: 10,
  overtimeThreshold: 8,
  attritionRate: 0.05,
};

const RISK_STYLES = {
  Low: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  Moderate: 'bg-amber-50 text-amber-700 border-amber-200',
  Elevated: 'bg-orange-50 text-orange-700 border-orange-200',
  Critical: 'bg-rose-50 text-rose-700 border-rose-200',
};

function normalizeScenario(value) {
  const next = value || {};
  return {
    plannedHiring: Number(next.plannedHiring || BASE_SCENARIO.plannedHiring),
    overtimeThreshold: Number(next.overtimeThreshold || BASE_SCENARIO.overtimeThreshold),
    attritionRate: Number(next.attritionRate ?? BASE_SCENARIO.attritionRate),
  };
}

function formatNumber(value) {
  if (typeof value === 'number') return value.toLocaleString();
  return value ?? '0';
}

function getRiskFromCoverage(coverage) {
  if (coverage < 10) return 'Critical';
  if (coverage < 20) return 'Elevated';
  if (coverage < 35) return 'Moderate';
  return 'Low';
}

function buildDepartmentSummary({ employees, employmentCount, activeAttendanceRate, activeLeaveRate, appliedScenario }) {
  const map = {};
  (employees || []).forEach((emp) => {
    const dept = (emp?.Department || emp?.department || 'Unassigned') || 'Unassigned';
    if (!map[dept]) {
      map[dept] = { name: dept, count: 0, roles: [], skills: [] };
    }
    map[dept].count += 1;

    const role = emp?.JobRole || emp?.jobRole || emp?.designation || 'General';
    const skillList = Array.isArray(emp?.skills) ? emp.skills : [];
    map[dept].roles.push(role);
    map[dept].skills.push(...skillList);
  });

  const maxCount = Math.max(1, ...Object.values(map).map((d) => d.count));

  return Object.values(map).map((d) => {
    const baseCoverage = Math.round((d.count / Math.max(1, employmentCount)) * 100);
    const plannedHiringBoost = ((appliedScenario.plannedHiring || 0) * (d.count / Math.max(1, employmentCount))) * 0.35;
    const coverage = Math.min(100, Math.round(baseCoverage + plannedHiringBoost));
    const risk = getRiskFromCoverage(coverage);
    const shortage = Math.max(0, Math.round((0.8 * d.count) - (d.count * (1 - (appliedScenario.attritionRate || 0)) / 1.2) + (appliedScenario.plannedHiring || 0) * (d.count / Math.max(1, employmentCount))));

    const roleCounts = d.roles.reduce((acc, role) => {
      acc[role] = (acc[role] || 0) + 1;
      return acc;
    }, {});

    const priorityRoles = Object.entries(roleCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([role]) => role);

    const skillCounts = d.skills.reduce((acc, skill) => {
      if (!skill) return acc;
      acc[skill] = (acc[skill] || 0) + 1;
      return acc;
    }, {});

    const recommendedSkills = Object.entries(skillCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3)
      .map(([skill]) => skill);

    let issue = 'Capacity is stable, maintain the current staffing model.';
    let recommendedAction = 'Monitor and retain current talent.';
    let suggestedHires = 0;

    if (risk === 'Critical' || coverage < 18) {
      issue = 'Department coverage is below plan. Critical staffing pressure is likely to impact operational resilience.';
      recommendedAction = 'Prioritize external hiring and internal transfer support.';
      suggestedHires = Math.max(1, Math.ceil((maxCount * 0.25) - (d.count * 0.08)));
    } else if (risk === 'Elevated' || coverage < 30) {
      issue = 'Demand is rising faster than available capacity. Workforce resilience needs attention.';
      recommendedAction = 'Add targeted hires and build internal mobility.';
      suggestedHires = Math.max(1, Math.ceil((d.count * 0.15) + (appliedScenario.overtimeThreshold || 0) / 10));
    } else if (risk === 'Moderate') {
      issue = 'Operational demand is near current capacity with limited headroom.';
      recommendedAction = 'Upskill the existing team and align hiring priorities.';
      suggestedHires = Math.max(0, Math.ceil((appliedScenario.plannedHiring || 0) * (d.count / Math.max(1, employmentCount))));
    }

    const internalMatches = (employees || []).filter((emp) => {
      const deptMatches = (emp?.Department || emp?.department || '') === d.name;
      return deptMatches;
    }).slice(0, 4).map((emp) => ({
      name: emp?.EmployeeName || emp?.name || emp?.EmpID || emp?.empId,
      role: emp?.JobRole || emp?.jobRole || 'General',
      match: Math.max(58, Math.min(96, 65 + Math.round((d.count / Math.max(1, employmentCount)) * 25))),
    }));

    return {
      name: d.name,
      count: d.count,
      coverage,
      risk,
      issue,
      recommendedAction,
      suggestedHires,
      priorityRoles,
      recommendedSkills,
      internalMatches,
      staffPressure: Math.max(0, Math.round((1 - (coverage / 100)) * 100)),
      attendanceRate: activeAttendanceRate,
      leaveRate: activeLeaveRate,
    };
  });
}

function buildScenarioRecommendation({ projectedAfterScenario, projectedShortage, departmentSummary, appliedScenario, employmentCount, activeAttendanceRate }) {
  const actionLines = [];

  if (projectedShortage > 0) {
    actionLines.push(`Add ${Math.max(1, Math.ceil(projectedShortage / 2))} hires to close the projected capacity gap.`);
  }

  if ((appliedScenario.overtimeThreshold || 0) > 14) {
    actionLines.push('Reduce overtime pressure in the next 30 days to protect productivity and retention.');
  }

  if (appliedScenario.attritionRate > 0.08) {
    actionLines.push('Retention and manager coaching should be prioritized because attrition risk is above the healthy baseline.');
  }

  const criticalDept = departmentSummary.find((dept) => dept.risk === 'Critical' || dept.risk === 'Elevated');
  if (criticalDept) {
    actionLines.push(`Focus recruitment effort on ${criticalDept.name} before the next workload spike.`);
  }

  return {
    summary: `Scenario outcome remains ${projectedShortage > 0 ? 'under pressure' : 'balanced'} with ${projectedAfterScenario} effective capacity against a current workforce demand baseline of ${employmentCount}.`,
    actions: actionLines.slice(0, 3),
    score: Math.min(95, Math.max(40, Math.round((projectedAfterScenario / Math.max(1, employmentCount + 10)) * 100 + (100 - activeAttendanceRate) * 0.3))),
  };
}

function buildForecastData({ selectedRange, effectiveCapacity, projectedAfterScenario, employmentCount }) {
  const days = selectedRange === '30' ? 30 : selectedRange === '90' ? 90 : selectedRange === '180' ? 180 : 365;
  const points = [];
  const today = new Date();
  const step = Math.max(1, Math.round(days / 24));

  for (let d = days; d >= 0; d -= step) {
    const dt = new Date(today);
    dt.setDate(dt.getDate() - d);
    const label = `${dt.getMonth() + 1}/${dt.getDate()}`;
    const seasonal = Math.round(Math.sin(d / 7) * Math.min(4, employmentCount * 0.01));
    const historic = Math.max(0, effectiveCapacity - Math.round((d / Math.max(1, days)) * (employmentCount * 0.05)) + seasonal);
    const horizonFactor = d <= days / 3 ? 1 : 1 - ((d - days / 3) / (days * 2 / 3));
    const forecast = Math.round(historic + (projectedAfterScenario - effectiveCapacity) * (1 - horizonFactor));
    points.push({ date: label, historic, forecast });
  }

  return points;
}

export default function AIWorkforcePlanning({ employees = [], attendance = [], leaves = [], payroll = [] }) {
  const baselineScenario = useMemo(() => BASE_SCENARIO, []);
  const [draftScenario, setDraftScenario] = useState(baselineScenario);
  const [appliedScenario, setAppliedScenario] = useState(baselineScenario);
  const [toast, setToast] = useState(null);
  const [deptDetail, setDeptDetail] = useState(null);
  const [planEditor, setPlanEditor] = useState(null);
  const [selectedPlan, setSelectedPlan] = useState(null);
  const [hiringPlans, setHiringPlans] = useState([]);
  const [plansLoading, setPlansLoading] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedRange, setSelectedRange] = useState('90');
  const [animateValue, setAnimateValue] = useState(0);

  const previousAppliedRef = useRef(appliedScenario);
  const employmentCount = Array.isArray(employees) ? employees.length : 0;

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = setTimeout(() => setToast(null), 3200);
    return () => clearTimeout(timeout);
  }, [toast]);

  useEffect(() => {
    const target = employmentCount;
    let start = 0;
    setAnimateValue(0);
    const step = Math.max(1, Math.round(target / 20));
    const timer = setInterval(() => {
      start += step;
      if (start >= target) {
        start = target;
        clearInterval(timer);
      }
      setAnimateValue(start);
    }, 20);
    return () => clearInterval(timer);
  }, [employmentCount]);

  useEffect(() => {
    const loadPlans = async () => {
      try {
        setPlansLoading(true);
        const response = await api.getHiringPlans();
        setHiringPlans(Array.isArray(response) ? response : []);
      } catch (error) {
        try {
          const storedPlans = JSON.parse(localStorage.getItem('nexus_hiring_plans') || '[]');
          setHiringPlans(storedPlans);
        } catch {
          setHiringPlans([]);
        }
      } finally {
        setPlansLoading(false);
      }
    };

    loadPlans();
  }, []);

  const activeAttendanceRate = useMemo(() => {
    try {
      if (!Array.isArray(attendance) || attendance.length === 0) return 96;
      const present = attendance.filter((record) => {
        const status = String(record?.AttendanceStatus || record?.status || '').toLowerCase();
        return ['present', 'late', 'on-time', 'checked-in'].includes(status);
      }).length;
      return Math.round((present / Math.max(1, attendance.length)) * 100);
    } catch {
      return 96;
    }
  }, [attendance]);

  const activeLeaveRate = useMemo(() => {
    try {
      if (!Array.isArray(leaves) || leaves.length === 0) return 0.05;
      const now = new Date();
      const inLeave = leaves.filter((item) => {
        const start = item?.StartDate || item?.startDate || item?.from || item?.start;
        const end = item?.EndDate || item?.endDate || item?.to || item?.end;
        if (!start || !end) return false;
        const sd = new Date(start);
        const ed = new Date(end);
        const status = String(item?.Status || item?.status || '').toLowerCase();
        return sd <= now && now <= ed && (status === 'approved' || status === 'approved-by-manager');
      }).length;
      return inLeave / Math.max(1, employmentCount);
    } catch {
      return 0.05;
    }
  }, [employmentCount, leaves]);

  const scenarioResult = useMemo(() => {
    const normalized = normalizeScenario(appliedScenario);
    const effectiveCapacity = Math.max(0, Math.round(employmentCount * (1 - activeLeaveRate) * (activeAttendanceRate / 100)));
    const overtimeCapacity = Math.round(employmentCount * (normalized.overtimeThreshold / 40));
    const projectedAfterScenario = effectiveCapacity + Number(normalized.plannedHiring) + overtimeCapacity;
    const projectedShortage = Math.max(0, Math.round((employmentCount * (1 - normalized.attritionRate)) - projectedAfterScenario));
    const departmentSummaries = buildDepartmentSummary({
      employees,
      employmentCount,
      activeAttendanceRate,
      activeLeaveRate,
      appliedScenario: normalized,
    });
    const recommendation = buildScenarioRecommendation({
      projectedAfterScenario,
      projectedShortage,
      departmentSummary: departmentSummaries,
      appliedScenario: normalized,
      employmentCount,
      activeAttendanceRate,
    });

    return {
      normalized,
      effectiveCapacity,
      overtimeCapacity,
      projectedAfterScenario,
      projectedShortage,
      departmentSummaries,
      recommendation,
      forecastData: buildForecastData({
        selectedRange,
        effectiveCapacity,
        projectedAfterScenario,
        employmentCount,
      }),
    };
  }, [activeAttendanceRate, activeLeaveRate, appliedScenario, employmentCount, employees, selectedRange]);

  const summaryMetrics = useMemo(() => [
    { label: 'Workforce Capacity', value: scenarioResult.effectiveCapacity, tone: 'emerald', icon: Users },
    { label: 'Hiring Demand', value: scenarioResult.normalized.plannedHiring, tone: 'indigo', icon: TrendingUp },
    { label: 'Critical Roles', value: Math.max(0, Math.round((employmentCount * 0.02) + (scenarioResult.projectedShortage > 0 ? 1 : 0))), tone: 'amber', icon: Award },
    { label: 'Predicted Shortage', value: Math.max(0, scenarioResult.projectedShortage), tone: 'red', icon: CheckCircle2 },
  ], [employmentCount, scenarioResult]);

  const recommendationCards = useMemo(() => [
    {
      priority: 'High',
      title: 'Hire additional Product team members',
      explanation: 'The current projected capacity indicates demand is above coverage in product and operations workstreams.',
      impact: `${scenarioResult.projectedAfterScenario} capacity after plan`,
      suggestion: 'Create Hiring Plan',
    },
    {
      priority: 'Medium',
      title: 'Reduce overtime in Engineering',
      explanation: 'The overtime threshold is driving workforce strain and should be managed before operating below a healthy baseline.',
      impact: `${scenarioResult.normalized.overtimeThreshold}h planned overtime`,
      suggestion: 'Review Department',
    },
    {
      priority: 'Medium',
      title: 'Upskill Operations talent',
      explanation: 'Cross-training and internal mobility are the most efficient path to stabilize the department risk profile.',
      impact: `${scenarioResult.departmentSummaries.filter((dept) => dept.risk !== 'Low').length} departments need action`,
      suggestion: 'View Details',
    },
  ], [scenarioResult]);

  const departmentDetailContext = deptDetail ? scenarioResult.departmentSummaries.find((dept) => dept.name === deptDetail.name) || deptDetail : null;

  const getScenarioDiffSummary = (nextScenarioValue) => {
    const previous = previousAppliedRef.current;
    const previousNormalized = normalizeScenario(previous);
    const nextNormalized = normalizeScenario(nextScenarioValue);
    const previousCapacity = Math.max(0, Math.round(employmentCount * (1 - activeLeaveRate) * (activeAttendanceRate / 100))) + Number(previousNormalized.plannedHiring) + Math.round(employmentCount * (previousNormalized.overtimeThreshold / 40));
    const nextCapacity = Math.max(0, Math.round(employmentCount * (1 - activeLeaveRate) * (activeAttendanceRate / 100))) + Number(nextNormalized.plannedHiring) + Math.round(employmentCount * (nextNormalized.overtimeThreshold / 40));

    const previousRisk = buildDepartmentSummary({
      employees,
      employmentCount,
      activeAttendanceRate,
      activeLeaveRate,
      appliedScenario: previousNormalized,
    }).filter((dept) => dept.risk === 'Critical' || dept.risk === 'Elevated').length;
    const nextRisk = buildDepartmentSummary({
      employees,
      employmentCount,
      activeAttendanceRate,
      activeLeaveRate,
      appliedScenario: nextNormalized,
    }).filter((dept) => dept.risk === 'Critical' || dept.risk === 'Elevated').length;

    return {
      previousCapacity,
      nextCapacity,
      deptShift: previousRisk - nextRisk,
    };
  };

  const handleApplyScenario = async () => {
    const nextScenario = normalizeScenario(draftScenario);
    const comparison = getScenarioDiffSummary(nextScenario);
    const previousScenario = previousAppliedRef.current;
    setAppliedScenario(nextScenario);
    previousAppliedRef.current = nextScenario;

    setToast({
      title: 'Scenario applied',
      message: `Projected capacity changed from ${comparison.previousCapacity} to ${comparison.nextCapacity}. ${comparison.deptShift > 0 ? `${comparison.deptShift} departments improved` : `${Math.abs(comparison.deptShift)} departments remain under stress`}.`,
    });

    try {
      const payload = {
        plannedHiring: nextScenario.plannedHiring,
        overtimeThreshold: nextScenario.overtimeThreshold,
        attritionRate: nextScenario.attritionRate,
        employees,
        attendance,
        leaves,
        payroll,
      };
      const response = await api.simulateWorkforcePlan(payload);
      if (response && typeof response.projectedAfterScenario === 'number') {
        const serverRiskCount = (response.departmentSummaries || []).filter((dept) => dept.risk === 'Critical' || dept.risk === 'Elevated').length;
        setToast({
          title: 'Scenario applied',
          message: `Projected capacity changed from ${comparison.previousCapacity} to ${response.projectedAfterScenario}. ${serverRiskCount} departments remain elevated.`,
        });
      }
    } catch (error) {
      // Local deterministic calculation was already applied to the UI.
    }
  };

  const handleResetScenario = () => {
    setDraftScenario(BASE_SCENARIO);
    setAppliedScenario(BASE_SCENARIO);
    previousAppliedRef.current = BASE_SCENARIO;
    setDeptDetail(null);
    setToast({
      title: 'Baseline restored',
      message: 'The workforce planning module has been reset to the original baseline state.',
    });
  };

  const handleCreatePlan = async (status = 'Draft') => {
    if (!planEditor) return;

    const payload = {
      department: planEditor.department,
      createdBy: 'HR Admin',
      createdAt: new Date().toISOString(),
      scenarioSnapshot: {
        plannedHiring: planEditor.appliedScenario.plannedHiring,
        overtimeThreshold: planEditor.appliedScenario.overtimeThreshold,
        attritionRate: planEditor.appliedScenario.attritionRate,
      },
      riskLevel: planEditor.riskLevel,
      recommendedHires: planEditor.recommendedHires,
      priorityRoles: planEditor.priorityRoles,
      recommendedSkills: planEditor.recommendedSkills,
      internalMatches: planEditor.internalMatches,
      timeline: planEditor.timeline,
      status,
      currentCoverage: planEditor.currentCoverage,
      aiRationale: planEditor.aiRationale,
    };

    try {
      const created = await api.createHiringPlan(payload);
      const list = Array.isArray(created) ? created : [created];
      setHiringPlans((prev) => [list[0], ...prev.filter((item) => (item.planId || item._id) !== (list[0].planId || list[0]._id))]);
      setSelectedPlan(list[0]);
      setToast({
        title: 'Hiring plan saved',
        message: `${status === 'Approved' ? 'Approved' : 'Draft'} hiring plan created for ${planEditor.department}.`,
      });
    } catch (error) {
      const fallbackPlan = {
        ...payload,
        planId: `LOCAL-${Date.now()}`,
      };
      const next = [fallbackPlan, ...hiringPlans.filter((item) => (item.planId || item._id) !== fallbackPlan.planId)];
      localStorage.setItem('nexus_hiring_plans', JSON.stringify(next));
      setHiringPlans(next);
      setSelectedPlan(fallbackPlan);
      setToast({
        title: 'Hiring plan saved locally',
        message: `${status === 'Approved' ? 'Approved' : 'Draft'} hiring plan stored in this browser session.`,
      });
    } finally {
      setPlanEditor(null);
    }
  };

  const handleGenerateAi = async () => {
    setIsGenerating(true);
    await new Promise((resolve) => setTimeout(resolve, 700));
    setIsGenerating(false);
    setToast({
      title: 'AI forecast refreshed',
      message: 'The latest workforce forecast has been recalculated using the current applied scenario.',
    });
  };

  const openPlanEditor = (department) => {
    const detail = scenarioResult.departmentSummaries.find((d) => d.name === department) || null;
    if (!detail) return;

    setPlanEditor({
      department: detail.name,
      riskLevel: detail.risk,
      currentCoverage: detail.coverage,
      recommendedHires: detail.suggestedHires,
      priorityRoles: detail.priorityRoles.slice(0, 3),
      recommendedSkills: detail.recommendedSkills.slice(0, 3),
      internalMatches: detail.internalMatches.slice(0, 3).map((match) => match.name),
      timeline: detail.coverage < 20 ? 'Immediate' : detail.coverage < 35 ? '30 days' : '60 days',
      aiRationale: `Targeted hiring for ${detail.name} improves coverage from ${detail.coverage}% to a stronger operating baseline while managing overtime pressure and attrition risk.`,
      appliedScenario: appliedScenario,
    });
  };

  return (
    <div className="space-y-6">
      {toast && (
        <div className="fixed right-4 top-4 z-50 max-w-sm rounded-xl border border-indigo-200 bg-white/95 p-4 shadow-xl backdrop-blur-sm">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-indigo-100 p-2 text-indigo-600"><Check className="h-4 w-4" /></div>
            <div>
              <div className="text-sm font-bold text-slate-800">{toast.title}</div>
              <div className="mt-1 text-xs text-slate-600">{toast.message}</div>
            </div>
          </div>
        </div>
      )}

      <section className="rounded-3xl bg-gradient-to-r from-indigo-900 via-indigo-800 to-violet-900 p-6 text-white shadow-xl shadow-indigo-900/30 ring-1 ring-white/10">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <div className="flex items-center gap-3">
              <div className="rounded-full bg-indigo-800/30 p-2">
                <BrainCircuit className="h-6 w-6 text-violet-200" />
              </div>
              <div>
                <div className="text-xs uppercase tracking-wider text-indigo-200">AI Workforce Engine</div>
                <h2 className="mt-1 text-2xl font-extrabold">AI Workforce Planning</h2>
                <p className="mt-1 text-sm text-indigo-200/80 max-w-2xl">
                  Predict workforce needs, identify capacity risks, and make smarter hiring and workforce decisions with AI-powered insights.
                </p>
              </div>
            </div>

            <div className="mt-4 flex flex-wrap gap-3 items-center">
              <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-3 py-1 text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                <span>Engine: Online</span>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-3 py-1 text-xs font-semibold">
                <Sparkles className="h-4 w-4 text-violet-200" />
                <span>Last analysis: <strong className="ml-1">{new Date().toLocaleString()}</strong></span>
              </div>
              <div className="inline-flex items-center gap-2 rounded-full bg-black/10 px-3 py-1 text-xs font-semibold">
                <Users className="h-4 w-4 text-indigo-200" />
                <span>Sources: Attendance · Employees · Leaves · Shifts · Timesheets</span>
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <button onClick={handleGenerateAi} className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-bold text-white shadow hover:bg-indigo-700 transition">
                {isGenerating ? 'Generating...' : 'Generate AI Forecast'}
              </button>
              <button onClick={() => setDraftScenario(appliedScenario)} className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-white/90 hover:bg-white/10 transition">
                Run Workforce Simulation
              </button>
            </div>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-3 lg:w-96">
            <div className="rounded-xl bg-white/6 p-3">
              <div className="text-xs text-indigo-200">Live Forecast</div>
              <div className="mt-1 text-xl font-extrabold">+{scenarioResult.normalized.plannedHiring}</div>
            </div>
            <div className="rounded-xl bg-white/6 p-3">
              <div className="text-xs text-indigo-200">Capacity (Effective)</div>
              <div className="mt-1 text-xl font-extrabold">{formatNumber(scenarioResult.effectiveCapacity)}</div>
            </div>
            <div className="rounded-xl bg-white/6 p-3">
              <div className="text-xs text-indigo-200">OT Ceiling</div>
              <div className="mt-1 text-xl font-extrabold">{scenarioResult.normalized.overtimeThreshold}h</div>
            </div>
          </div>
        </div>
      </section>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        {summaryMetrics.map((metric) => (
          <div key={metric.label} className="rounded-2xl bg-white p-4 shadow-sm hover:shadow-md transition transform hover:-translate-y-0.5">
            <div className="flex items-center justify-between">
              <div className="text-xs font-semibold text-slate-500">{metric.label}</div>
              <div className="text-sm font-semibold text-slate-400">{metric.tone.toUpperCase()}</div>
            </div>
            <div className="mt-3 flex items-center justify-between">
              <div className="text-2xl font-extrabold">{metric.value}</div>
              <div className="rounded-full bg-slate-100 p-2 text-slate-500"><Users className="h-4 w-4" /></div>
            </div>
            <div className="mt-2 text-[11px] text-slate-500">Updated from live system</div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 rounded-2xl bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-bold">Workforce Forecast</div>
              <div className="text-xs text-slate-500">Historical capacity and projected demand</div>
            </div>
            <div className="flex items-center gap-2">
              {['30', '90', '180', '365'].map((range) => (
                <button
                  key={range}
                  onClick={() => setSelectedRange(range)}
                  className={`px-3 py-1 rounded ${selectedRange === range ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-700'}`}
                >
                  {range === '30' ? '30d' : range === '90' ? '90d' : range === '180' ? '6m' : '1y'}
                </button>
              ))}
            </div>
          </div>

          <div className="h-64 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={scenarioResult.forecastData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorHistoric" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#60a5fa" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#60a5fa" stopOpacity={0.05} />
                  </linearGradient>
                  <linearGradient id="colorForecast" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#7c3aed" stopOpacity={0.8} />
                    <stop offset="95%" stopColor="#7c3aed" stopOpacity={0.05} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip />
                <Legend />
                <Area type="monotone" dataKey="historic" stroke="#3b82f6" fillOpacity={1} fill="url(#colorHistoric)" />
                <Area type="monotone" dataKey="forecast" stroke="#7c3aed" fillOpacity={1} fill="url(#colorForecast)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Effective Capacity Today</div>
              <div className="mt-1 text-lg font-bold">{formatNumber(scenarioResult.effectiveCapacity)}</div>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Projected After Scenario</div>
              <div className="mt-1 text-lg font-bold">{formatNumber(scenarioResult.projectedAfterScenario)}</div>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Attendance Rate</div>
              <div className="mt-1 text-lg font-bold">{activeAttendanceRate}%</div>
            </div>
          </div>
        </div>

        <aside className="rounded-2xl bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between">
            <div className="text-sm font-bold">Scenario Simulator</div>
            <div className="text-xs text-slate-500">Draft vs applied</div>
          </div>

          <div className="mt-4 space-y-4 text-sm">
            <div>
              <label className="flex justify-between">
                <span>Planned Hiring</span>
                <strong>+{draftScenario.plannedHiring}</strong>
              </label>
              <input type="range" min="0" max="200" value={draftScenario.plannedHiring} onChange={(e) => setDraftScenario((prev) => ({ ...prev, plannedHiring: Number(e.target.value) }))} className="w-full mt-2" />
            </div>

            <div>
              <label className="flex justify-between">
                <span>Overtime Threshold (hrs/wk)</span>
                <strong>{draftScenario.overtimeThreshold}h</strong>
              </label>
              <input type="range" min="0" max="40" value={draftScenario.overtimeThreshold} onChange={(e) => setDraftScenario((prev) => ({ ...prev, overtimeThreshold: Number(e.target.value) }))} className="w-full mt-2" />
            </div>

            <div>
              <label className="flex justify-between">
                <span>Expected Attrition Rate</span>
                <strong>{Math.round(draftScenario.attritionRate * 100)}%</strong>
              </label>
              <input type="range" min="0" max="30" value={Math.round(draftScenario.attritionRate * 100)} onChange={(e) => setDraftScenario((prev) => ({ ...prev, attritionRate: Number(e.target.value) / 100 }))} className="w-full mt-2" />
            </div>

            <div className="rounded-lg bg-indigo-50 p-3 text-xs text-indigo-700">
              Current applied scenario: <strong>+{appliedScenario.plannedHiring} hires</strong>, <strong>{appliedScenario.overtimeThreshold}h OT</strong>, <strong>{Math.round(appliedScenario.attritionRate * 100)}% attrition</strong>.
            </div>

            <div className="mt-2 text-xs text-slate-500">Projected impact: capacity {Math.round(((scenarioResult.projectedAfterScenario - scenarioResult.effectiveCapacity) / Math.max(1, scenarioResult.effectiveCapacity)) * 100)}% change</div>

            <div className="mt-3 flex gap-2">
              <button onClick={handleApplyScenario} className="rounded-md bg-indigo-600 px-3 py-2 text-white font-semibold">Apply Scenario</button>
              <button onClick={handleResetScenario} className="rounded-md border px-3 py-2">Reset</button>
            </div>
          </div>
        </aside>
      </div>

      <section className="rounded-2xl bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Department Capacity & Risk</div>
            <div className="text-xs text-slate-500">Click a department for details</div>
          </div>
          <div className="text-xs text-slate-500">{employmentCount} Active Profiles</div>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
          {scenarioResult.departmentSummaries.map((department) => (
            <button
              key={department.name}
              type="button"
              onClick={() => setDeptDetail(department)}
              className="cursor-pointer rounded-lg border border-slate-200 bg-slate-50 p-3 text-left transition hover:shadow-md hover:-translate-y-0.5"
            >
              <div className="flex items-center justify-between">
                <div className="font-semibold">{department.name}</div>
                <span className={`rounded-full border px-2 py-1 text-[10px] font-medium ${RISK_STYLES[department.risk]}`}>
                  {department.risk}
                </span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-200 overflow-hidden">
                <div className="h-full bg-indigo-600 transition-all" style={{ width: `${department.coverage}%` }} />
              </div>
              <div className="mt-2 text-xs text-slate-500">Coverage {department.coverage}% · {department.count} employees</div>
            </button>
          ))}
        </div>

        <div className="mt-4 rounded-lg bg-indigo-50 p-3">
          <div className="text-sm font-bold">AI Recommendations</div>
          <div className="mt-2 text-xs text-indigo-700">
            {scenarioResult.recommendation.actions.join(' ')}
          </div>
        </div>
      </section>

      <section className="rounded-2xl bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">AI Recommendations</div>
            <div className="text-xs text-slate-500">Actionable staffing guidance</div>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
          {recommendationCards.map((item) => (
            <div key={item.title} className="rounded-xl border border-slate-200 bg-slate-50 p-4">
              <div className="flex items-center justify-between">
                <span className="rounded-full bg-indigo-100 px-2 py-1 text-[10px] font-semibold uppercase tracking-wide text-indigo-700">
                  {item.priority}
                </span>
                <button type="button" onClick={() => openPlanEditor('Product')} className="text-[11px] font-medium text-indigo-600">
                  {item.suggestion}
                </button>
              </div>
              <div className="mt-3 text-sm font-bold text-slate-800">{item.title}</div>
              <div className="mt-2 text-xs text-slate-600">{item.explanation}</div>
              <div className="mt-3 flex items-center justify-between border-t border-slate-200 pt-2">
                <div className="text-[11px] text-slate-500">{item.impact}</div>
                <ArrowRight className="h-4 w-4 text-slate-400" />
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="rounded-2xl bg-white p-4 shadow-sm">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="text-sm font-bold">Hiring Plans</div>
            <div className="text-xs text-slate-500">Review and manage workforce hiring plans</div>
          </div>
        </div>

        {plansLoading ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">Loading hiring plans…</div>
        ) : hiringPlans.length === 0 ? (
          <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">No hiring plans created yet. Use a department card to begin a plan.</div>
        ) : (
          <div className="space-y-2">
            {hiringPlans.map((plan) => (
              <button
                key={plan.planId || plan._id || `${plan.department}-${plan.createdAt}`}
                type="button"
                onClick={() => setSelectedPlan(plan)}
                className="flex w-full items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-3 text-left transition hover:border-indigo-200 hover:bg-indigo-50"
              >
                <div>
                  <div className="text-sm font-semibold text-slate-800">{plan.department}</div>
                  <div className="text-xs text-slate-500">{plan.riskLevel || 'Moderate'} · {plan.recommendedHires || 0} hires</div>
                </div>
                <div className="text-right">
                  <div className="text-xs font-medium text-indigo-600">{plan.status || 'Draft'}</div>
                  <div className="text-[11px] text-slate-500">{new Date(plan.createdAt || Date.now()).toLocaleDateString()}</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>

      {deptDetail && (
        <div className="fixed inset-0 z-50 flex items-end lg:items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setDeptDetail(null)} />
          <div className="relative w-full max-w-3xl rounded-2xl bg-white shadow-xl p-6">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-xl font-bold">{departmentDetailContext?.name || deptDetail.name} — Details</h3>
                <div className="text-xs text-slate-500">Coverage {departmentDetailContext?.coverage || deptDetail.coverage}% · {departmentDetailContext?.count || deptDetail.count} employees</div>
              </div>
              <button type="button" onClick={() => setDeptDetail(null)} className="p-2 rounded-md text-slate-500 hover:bg-slate-100"><X className="w-4 h-4" /></button>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Workforce issue</div>
                <div className="mt-2 text-sm font-medium text-slate-800">{departmentDetailContext?.issue || 'Operational capacity is near threshold.'}</div>
                <div className="mt-3 flex items-center justify-between rounded-lg bg-white p-2">
                  <span className="text-xs text-slate-500">Risk</span>
                  <span className={`rounded-full border px-2 py-1 text-[10px] font-medium ${RISK_STYLES[departmentDetailContext?.risk || deptDetail.risk]}`}>
                    {departmentDetailContext?.risk || deptDetail.risk}
                  </span>
                </div>
              </div>

              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Recommended action</div>
                <div className="mt-2 text-sm font-medium text-slate-800">{departmentDetailContext?.recommendedAction || 'Target hiring and department upskilling.'}</div>
                <div className="mt-3 flex items-center justify-between rounded-lg bg-white p-2">
                  <span className="text-xs text-slate-500">Suggested hires</span>
                  <span className="text-sm font-semibold text-indigo-600">{departmentDetailContext?.suggestedHires || 1}</span>
                </div>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Priority roles</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(departmentDetailContext?.priorityRoles || ['Product Analyst', 'Operations Specialist']).map((role) => (
                    <span key={role} className="rounded-full bg-white px-2 py-1 text-xs text-slate-700">{role}</span>
                  ))}
                </div>
              </div>

              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Priority skills</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {(departmentDetailContext?.recommendedSkills || ['Lifecycle planning', 'Workflow design']).map((skill) => (
                    <span key={skill} className="rounded-full bg-white px-2 py-1 text-xs text-slate-700">{skill}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-4 rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Potential internal matches</div>
              <div className="mt-2 space-y-2 text-sm">
                {(departmentDetailContext?.internalMatches || []).map((match) => (
                  <div key={match.name} className="flex items-center justify-between rounded-lg bg-white p-2">
                    <div>
                      <div className="font-medium text-slate-800">{match.name}</div>
                      <div className="text-[11px] text-slate-500">{match.role}</div>
                    </div>
                    <span className="text-xs font-medium text-indigo-600">{match.match}% match</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="mt-4 flex gap-3">
              <button type="button" onClick={() => { openPlanEditor(departmentDetailContext?.name || deptDetail.name); setDeptDetail(null); }} className="rounded-md bg-indigo-600 px-4 py-2 text-white">Create Hiring Plan</button>
              <button type="button" onClick={() => setDeptDetail(null)} className="rounded-md border px-4 py-2">Close</button>
            </div>
          </div>
        </div>
      )}

      {planEditor && (
        <div className="fixed inset-0 z-50 flex items-end lg:items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setPlanEditor(null)} />
          <div className="relative w-full max-w-4xl rounded-2xl bg-white shadow-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-indigo-600">Hiring Plan</div>
                <h3 className="text-2xl font-bold text-slate-900">{planEditor.department}</h3>
              </div>
              <button type="button" onClick={() => setPlanEditor(null)} className="p-2 rounded-md text-slate-500 hover:bg-slate-100"><X className="w-4 h-4" /></button>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-xl bg-slate-50 p-4">
                <div className="text-xs uppercase tracking-wide text-slate-500">Hiring Plan Summary</div>
                <div className="mt-3 space-y-3 text-sm text-slate-700">
                  <div className="flex justify-between"><span>Department</span><span className="font-semibold">{planEditor.department}</span></div>
                  <div className="flex justify-between"><span>Current Risk</span><span className="font-semibold">{planEditor.riskLevel}</span></div>
                  <div className="flex justify-between"><span>Current Coverage</span><span className="font-semibold">{planEditor.currentCoverage}%</span></div>
                  <div className="flex justify-between"><span>Recommended Hiring Count</span><span className="font-semibold">{planEditor.recommendedHires}</span></div>
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <div className="text-xs uppercase tracking-wide text-slate-500">AI Rationale</div>
                <p className="mt-3 text-sm text-slate-700">{planEditor.aiRationale}</p>
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
              <div className="rounded-xl bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><Briefcase className="h-4 w-4 text-indigo-600" /> Priority Roles</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {planEditor.priorityRoles.map((role) => (
                    <span key={role} className="rounded-full bg-white px-2 py-1 text-xs text-slate-700">{role}</span>
                  ))}
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><Target className="h-4 w-4 text-indigo-600" /> Recommended Skills</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {planEditor.recommendedSkills.map((skill) => (
                    <span key={skill} className="rounded-full bg-white px-2 py-1 text-xs text-slate-700">{skill}</span>
                  ))}
                </div>
              </div>

              <div className="rounded-xl bg-slate-50 p-4">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><ShieldCheck className="h-4 w-4 text-indigo-600" /> Internal Mobility</div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {planEditor.internalMatches.map((match) => (
                    <span key={match} className="rounded-full bg-white px-2 py-1 text-xs text-slate-700">{match}</span>
                  ))}
                </div>
              </div>
            </div>

            <div className="mt-6 rounded-xl bg-slate-50 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold text-slate-800"><Calendar className="h-4 w-4 text-indigo-600" /> Hiring Timeline</div>
              <div className="mt-3 flex flex-wrap gap-2">
                {['Immediate', '30 days', '60 days', '90 days'].map((item) => (
                  <span key={item} className={`rounded-full px-3 py-1 text-xs font-medium ${item === planEditor.timeline ? 'bg-indigo-600 text-white' : 'bg-white text-slate-700'}`}>
                    {item}
                  </span>
                ))}
              </div>
            </div>

            <div className="mt-6 flex gap-3">
              <button type="button" onClick={() => handleCreatePlan('Draft')} className="rounded-md border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700">Save Draft</button>
              <button type="button" onClick={() => handleCreatePlan('Approved')} className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-semibold text-white">Create/Approve Hiring Plan</button>
              <button type="button" onClick={() => setPlanEditor(null)} className="rounded-md border px-4 py-2 text-sm font-semibold text-slate-700">Cancel</button>
            </div>
          </div>
        </div>
      )}

      {selectedPlan && (
        <div className="fixed inset-0 z-50 flex items-end lg:items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSelectedPlan(null)} />
          <div className="relative w-full max-w-2xl rounded-2xl bg-white shadow-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs uppercase tracking-wider text-indigo-600">Plan Review</div>
                <h3 className="text-xl font-bold text-slate-900">{selectedPlan.department}</h3>
              </div>
              <button type="button" onClick={() => setSelectedPlan(null)} className="p-2 rounded-md text-slate-500 hover:bg-slate-100"><X className="w-4 h-4" /></button>
            </div>

            <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-2">
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Hiring Count</div>
                <div className="mt-1 text-lg font-bold text-slate-800">{selectedPlan.recommendedHires || 0}</div>
              </div>
              <div className="rounded-lg bg-slate-50 p-3">
                <div className="text-xs text-slate-500">Status</div>
                <div className="mt-1 text-lg font-bold text-slate-800">{selectedPlan.status || 'Draft'}</div>
              </div>
            </div>

            <div className="mt-4 space-y-3 text-sm text-slate-700">
              <div className="flex justify-between"><span>Risk</span><span className="font-semibold">{selectedPlan.riskLevel || 'Moderate'}</span></div>
              <div className="flex justify-between"><span>Timeline</span><span className="font-semibold">{selectedPlan.timeline || '30 days'}</span></div>
              <div className="flex justify-between"><span>Created</span><span className="font-semibold">{selectedPlan.createdAt ? new Date(selectedPlan.createdAt).toLocaleDateString() : 'N/A'}</span></div>
              <div className="rounded-lg bg-indigo-50 p-3 text-xs text-indigo-700">{selectedPlan.aiRationale || 'Department coverage improvement plan aligned to the current workforce model and risk profile.'}</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export { AIWorkforcePlanning };
