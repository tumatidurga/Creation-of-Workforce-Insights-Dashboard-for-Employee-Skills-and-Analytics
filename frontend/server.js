import express from "express";
import path from "path";
import { createServer as createViteServer } from "vite";
import { GoogleGenAI } from "@google/genai";
import dotenv from "dotenv";

dotenv.config();

async function startServer() {
  const app = express();
  const PORT = 3000;

  app.use(express.json());

  const ai = process.env.GEMINI_API_KEY
    ? new GoogleGenAI({
        apiKey: process.env.GEMINI_API_KEY,
        httpOptions: {
          headers: {
            "User-Agent": "aistudio-build",
          },
        },
      })
    : null;

  const USE_REAL_BACKEND = process.env.USE_REAL_BACKEND === "true";
  const BACKEND_API_URL = process.env.VITE_API_URL || process.env.BACKEND_API_URL || "http://127.0.0.1:8000";

  if (!USE_REAL_BACKEND) {
    app.get("/api/health", (req, res) => {
      res.json({
        status: "online",
        system: "AI Workforce Management Automation System",
        backendFramework: "FastAPI / Express Gateway",
        geminiConnected: !!ai,
        timestamp: new Date().toISOString(),
      });
    });

    app.get("/api/employees", (req, res) => {
      const list = [
        {
          empId: "E-1001",
          firstName: "Alexander",
          lastName: "Wright",
          email: "alexander.wright@enterprise.com",
          phone: "+1 (555) 019-2834",
          avatar: "https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=250",
          gender: "Male",
          age: 38,
          department: "Engineering",
          jobRole: "Director of Technology",
          designation: "Director",
          jobLevel: 5,
          location: "Headquarters - New York",
          status: "Active",
          monthlyIncome: 16500,
          yearsAtCompany: 7,
          yearsInRole: 3,
          yearsWithManager: 4,
          workLifeBalanceScore: 4,
          jobSatisfactionScore: 5,
          environmentSatisfactionScore: 4,
          relationshipSatisfactionScore: 5,
          skills: ["System Architecture", "Cloud Governance", "AI Engineering"],
          education: "Master of Computer Science",
          educationField: "Software Systems",
          emergencyContact: { name: "Elena Wright", relationship: "Spouse", phone: "+1 (555) 019-2835" },
          address: "742 Evergreen Terrace, Manhattan, NY",
        },
        {
          empId: "E-1002",
          firstName: "Sarah",
          lastName: "Jenkins",
          email: "sarah.jenkins@enterprise.com",
          phone: "+1 (555) 018-9201",
          avatar: "https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?auto=format&fit=crop&q=80&w=250",
          gender: "Female",
          age: 31,
          department: "Engineering",
          jobRole: "Lead Full Stack Engineer",
          designation: "Tech Lead",
          jobLevel: 4,
          location: "Headquarters - New York",
          status: "Active",
          monthlyIncome: 12800,
          yearsAtCompany: 4,
          yearsInRole: 2,
          yearsWithManager: 2,
          workLifeBalanceScore: 4,
          jobSatisfactionScore: 5,
          environmentSatisfactionScore: 4,
          relationshipSatisfactionScore: 4,
          skills: ["React", "Node.js", "FastAPI", "PostgreSQL"],
          education: "Bachelor of Software Engineering",
          educationField: "Computer Science",
          emergencyContact: { name: "Mark Jenkins", relationship: "Brother", phone: "+1 (555) 018-9202" },
          address: "120 Broadway, Brooklyn, NY",
        },
      ];

      if (req.query.page || req.query.size) {
        return res.json({
          items: list,
          total: list.length,
          page: Number(req.query.page) || 1,
          size: Number(req.query.size) || 50,
          pages: 1,
        });
      }
      res.json(list);
    });

    app.get("/api/attendance", (req, res) => {
      const list = [
        {
          id: "ATT-101",
          empId: "E-1001",
          empName: "Alexander Wright",
          department: "Engineering",
          date: "2026-08-04",
          checkIn: "08:52",
          checkOut: "18:15",
          workingHours: 9.38,
          status: "Present",
          isAnomaly: false,
        },
      ];

      if (req.query.page || req.query.size) {
        return res.json({
          items: list,
          total: list.length,
          page: Number(req.query.page) || 1,
          size: Number(req.query.size) || 50,
          pages: 1,
        });
      }
      res.json(list);
    });

    app.post("/api/attendance/check-in", (req, res) => {
      const { empId } = req.body;
      res.status(201).json({
        id: `ATT-${Date.now().toString().slice(-4)}`,
        empId: empId || "E-1001",
        empName: "Alexander Wright",
        department: "Engineering",
        date: new Date().toISOString().split("T")[0],
        checkIn: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        checkOut: "--:--",
        workingHours: 0,
        status: "Present",
        isAnomaly: false,
      });
    });

    app.post("/api/attendance/check-out", (req, res) => {
      const { empId } = req.body;
      res.json({
        id: "ATT-101",
        empId: empId || "E-1001",
        empName: "Alexander Wright",
        department: "Engineering",
        date: new Date().toISOString().split("T")[0],
        checkIn: "09:00",
        checkOut: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        workingHours: 8.5,
        status: "Present",
        isAnomaly: false,
      });
    });

    app.get("/api/leaves", (req, res) => {
      res.json([
        {
          id: "LV-801",
          empId: "E-1003",
          empName: "Michael Chang",
          department: "Engineering",
          leaveType: "Casual Leave",
          startDate: "2026-08-10",
          endDate: "2026-08-12",
          days: 3,
          reason: "Attending AI Research Conference",
          status: "Approved",
          appliedOn: "2026-08-01",
        },
      ]);
    });

    app.get("/api/leaves/balance", (req, res) => {
      res.json({
        casualLeave: { total: 12, used: 4, remaining: 8 },
        sickLeave: { total: 10, used: 2, remaining: 8 },
        earnedLeave: { total: 18, used: 5, remaining: 13 },
        parentalLeave: { total: 30, used: 0, remaining: 30 },
      });
    });

    app.get("/api/payroll", (req, res) => {
      res.json([
        {
          id: "PAY-2026-07-1001",
          empId: "E-1001",
          empName: "Alexander Wright",
          department: "Engineering",
          designation: "Director",
          month: "August 2026",
          baseSalary: 16500,
          overtimeHours: 0,
          overtimePay: 0,
          performanceBonus: 2500,
          incentives: 500,
          grossEarnings: 19500,
          taxDeductions: 3900,
          attendanceDeductions: 0,
          netPay: 15600,
          status: "Calculated",
        },
      ]);
    });

    app.get("/api/analytics/dashboard", (req, res) => {
      res.json({
        totalEmployees: 10,
        activeEmployees: 10,
        attendanceRate: "96.4%",
        attritionRiskCount: 3,
        totalMonthlyPayroll: 482500,
        pendingLeaveRequests: 2,
        pendingShiftRequests: 3,
      });
    });

    const handleChat = async (req, res) => {
      try {
        const message = req.body.message || req.body.prompt;
        const role = req.body.role;
        const context = req.body.context;

        if (!message) {
          return res.status(400).json({ error: "Message or prompt is required" });
        }

        if (!ai) {
          const lowerMsg = message.toLowerCase();
          let fallbackReply = "";
          let dataWidget = null;

          if (lowerMsg.includes("attrition") || lowerMsg.includes("risk") || lowerMsg.includes("turnover")) {
            fallbackReply = "Based on machine learning attrition risk models (XGBoost classifier), 3 employees are flagged with high attrition risk (>70% probability):\n\n1. **Emp #E-1004 (David Miller)** - Engineering (88% Attrition Risk) | Driver: High Overtime (28 hrs/mo), Low Environment Satisfaction.\n2. **Emp #E-1009 (Jessica Taylor)** - Product Management (79% Risk) | Driver: Market Pay Gap & 4.2 yrs in current role.\n3. **Emp #E-1015 (Rachel Green)** - Customer Success (74% Risk) | Driver: Long commute distance & Work-Life Balance score 2/5.\n\n**Recommended Intervention:** Conduct 1-on-1 stay interviews, re-evaluate workload/overtime compensation, and review market alignment for senior individual contributors.";
            dataWidget = {
              type: "attrition_widget",
              highRiskCount: 3,
              avgRiskScore: "34%",
              topDepartment: "Engineering",
            };
          } else if (lowerMsg.includes("absent") || lowerMsg.includes("attendance") || lowerMsg.includes("trend")) {
            fallbackReply = "Attendance Analytics & Absenteeism Forecast:\n\n• **Overall Organization Attendance Rate:** 96.4%\n• **Highest Absenteeism Dept:** Customer Support (7.2% unscheduled absence rate on Fridays/Mondays).\n• **AI Predictive Alert:** Upcoming seasonal spike anticipated next Monday due to regional public transit maintenance. Recommend enabling remote work option for North Hub employees.";
            dataWidget = {
              type: "attendance_widget",
              rate: "96.4%",
              flaggedDays: ["Mondays", "Fridays"],
            };
          } else if (lowerMsg.includes("promotion") || lowerMsg.includes("recommend") || lowerMsg.includes("talent")) {
            fallbackReply = "AI Talent Intelligence & Promotion Recommendations:\n\n1. **Emp #E-1002 (Sarah Jenkins)** - Lead Full Stack Engineer → *Senior Staff Architect* (Performance Score: 96/100, Skill Mastery: 94%, High Peer Collaboration).\n2. **Emp #E-1007 (Alex Rivera)** - Senior UX Researcher → *Product Design Manager* (Performance Score: 92/100, Completed Leadership Development Module).\n\nBoth candidates satisfy all internal mobility and compliance criteria.";
          } else if (lowerMsg.includes("payroll") || lowerMsg.includes("salary") || lowerMsg.includes("cost")) {
            fallbackReply = "Current Month Payroll Input Automation Summary:\n\n• **Total Projected Payroll:** $482,500\n• **Approved Overtime Cost:** $18,420 (214 hours total across Engineering & Ops)\n• **Automated Unpaid Leave Deductions:** $4,200\n• **Payroll Sync Status:** 100% synchronized with biometric & leave modules ready for ERP / Snowflake export.";
          } else {
            fallbackReply = `I am your Enterprise Workforce AI Assistant. I have analyzed your system context (${role || "Admin"} view).\n\nYou can ask me about:\n- Attrition predictions and employee retention strategies\n- Attendance anomaly detection and absenteeism forecasts\n- Internal promotion and skill gap recommendations\n- Payroll inputs summary and overtime calculations\n- Workforce planning and headcount optimization.`;
          }

          return res.json({ reply: fallbackReply, text: fallbackReply, dataWidget, model: "Simulated Enterprise AI Rules" });
        }

        const systemInstruction = `You are the AI Assistant for an Enterprise Workforce Management Automation System (inspired by SAP SuccessFactors, Workday, and Oracle HCM).
The current user role is: ${role || "HR Administrator"}.
Current System Context: ${JSON.stringify(context || {})}
Provide authoritative, actionable, concise, professional HR insights with bullet points and clear metric summaries.
Help the user make data-driven decisions on attrition, attendance, payroll inputs, performance, and staffing.`;

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: message,
          config: {
            systemInstruction,
            temperature: 0.3,
          },
        });

        const text = response.text || "No response generated from AI.";
        return res.json({
          reply: text,
          text,
          model: "gemini-3.6-flash",
        });
      } catch (error) {
        console.error("Gemini API error:", error);
        res.status(500).json({ error: "Error generating AI response", details: error.message });
      }
    };

    app.post("/api/chat", handleChat);
    app.post("/api/ai/chat", handleChat);

    app.post("/api/ai-insights", async (req, res) => {
      try {
        const { type, department } = req.body;

        if (!ai) {
          return res.json({
            insight: `Automated AI Predictive Assessment [${type || "General"}] for ${department || "All Departments"}: High workforce stability overall (92.4%), low flight risk in core product teams, recommended skill uplift in Cloud Infrastructure & Data Governance.`,
            simulated: true,
          });
        }

        const prompt = `Generate an executive HR intelligence brief on ${type} for department: ${department || "Entire Organization"}. Include key metrics, top 3 risks, and 3 strategic recommendations.`;

        const response = await ai.models.generateContent({
          model: "gemini-3.6-flash",
          contents: prompt,
          config: {
            systemInstruction: "You are an Enterprise Workforce Analytics AI Specialist.",
          },
        });

        res.json({ insight: response.text, simulated: false });
      } catch (err) {
        res.status(500).json({ error: err.message });
      }
    });
  }

  if (process.env.NODE_ENV !== "production") {
    const viteConfig = {
      server: {
        middlewareMode: true,
        ...(USE_REAL_BACKEND ? { proxy: { "/api": { target: BACKEND_API_URL, changeOrigin: true, secure: false } } } : {}),
      },
      appType: "spa",
    };

    const vite = await createViteServer(viteConfig);
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  app.listen(PORT, "0.0.0.0", () => {
    console.log(`Enterprise Workforce Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer().catch((err) => {
  console.error("Failed to start server:", err);
});
