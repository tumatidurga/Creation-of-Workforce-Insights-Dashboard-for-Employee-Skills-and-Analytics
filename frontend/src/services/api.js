import axios from 'axios';

const AUTH_TOKEN_KEY = 'nexus_hrms_auth_token';
const AUTH_USER_KEY = 'nexus_hrms_auth_user';

// Normalize API base URL: accept either a full URL (e.g. http://127.0.0.1:8000 or http://127.0.0.1:8000/api)
// or fall back to the development proxy path '/api'. If VITE_API_URL is set but
// does not include the '/api' path segment, append it so apiClient requests go to
// the correct backend routes (e.g. /api/employees).
const rawApiUrl = import.meta.env.VITE_API_URL;
let API_BASE_URL = '/api';
if (rawApiUrl && rawApiUrl.length > 0) {
  const trimmed = rawApiUrl.replace(/\/+$/, '');
  if (trimmed.endsWith('/api')) {
    API_BASE_URL = trimmed;
  } else {
    API_BASE_URL = `${trimmed}/api`;
  }
}

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Helper: robustly download a file from a server-provided downloadUrl that may or may not
// include the API prefix. This function resolves the final request URL in a safe way and
// returns an axios promise with responseType 'blob'. It preserves auth headers via the
// apiClient interceptor.
export async function downloadFileByUrl(downloadUrl, opts = {}) {
  if (!downloadUrl) throw new Error('downloadUrl is required');

  // If downloadUrl is absolute (http/https), request it directly using apiClient
  // so interceptors (auth) are preserved.
  if (/^https?:\/\//i.test(downloadUrl)) {
    return apiClient.get(downloadUrl, { responseType: 'blob', ...opts });
  }

  // If downloadUrl is relative, ensure the Authorization header is attached when
  // using axios to perform an absolute-path request. Prefer apiClient when possible
  // but avoid duplicating a baseURL segment (e.g., '/api' + '/api/...').
  const base = (apiClient.defaults && apiClient.defaults.baseURL) ? String(apiClient.defaults.baseURL).replace(/\/+$/, '') : '';
  const token = getStoredAuthToken();

  // Helper to attach token to axios calls for same-origin absolute paths
  const axiosWithAuth = (url) => axios.get(url, { responseType: 'blob', headers: { ...(opts.headers || {}), ...(token ? { Authorization: 'Bearer ' + token } : {}) }, ...opts });

  // If the returned URL already contains the base path (e.g., '/api/reports/...'),
  // request by absolute path and include auth header via axiosWithAuth.
  if (base && downloadUrl.startsWith(base)) {
    return axiosWithAuth(downloadUrl);
  }

  // If downloadUrl starts with '/api', request it as an absolute path on the origin
  // and include the Authorization header.
  if (downloadUrl.startsWith('/api')) {
    return axiosWithAuth(downloadUrl);
  }

  // Otherwise, assemble final URL from apiClient baseURL + downloadUrl and request via axiosWithAuth
  const assembled = `${base}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
  return axiosWithAuth(assembled);
}

export function getStoredAuthToken() {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function persistAuthSession(token, user) {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(AUTH_TOKEN_KEY, token);
  } else {
    localStorage.removeItem(AUTH_TOKEN_KEY);
  }
  if (user) {
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
  } else {
    localStorage.removeItem(AUTH_USER_KEY);
  }
}

export function clearAuthSession() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(AUTH_USER_KEY);
}

// Request interceptor: attach bearer token if available
apiClient.interceptors.request.use((config) => {
  const token = getStoredAuthToken();
  if (token) {
    config.headers = config.headers || {};
    if (!String(config.headers.Authorization || '').startsWith('Bearer ')) {
      config.headers.Authorization = 'Bearer ' + token;
    }
  }
  return config;
});


apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.warn('API Service Layer Notice:', error?.response?.data || error.message);
    return Promise.reject(error);
  }
);

export async function downloadAndSave(downloadUrl, filename = "report-download", opts = {}) {
  if (!downloadUrl) throw new Error('downloadUrl is required');

  try {
    const token = getStoredAuthToken();
    let finalUrl = downloadUrl;

    if (!/^https?:\/\//i.test(downloadUrl)) {
      const configuredBase = String(API_BASE_URL || '/api').replace(/\/+$/, '');
      if (/^https?:\/\//i.test(configuredBase)) {
        const backendOrigin = new URL(configuredBase).origin;
        if (downloadUrl.startsWith('/api/')) {
          finalUrl = `${backendOrigin}${downloadUrl}`;
        } else {
          finalUrl = `${configuredBase}${downloadUrl.startsWith('/') ? '' : '/'}${downloadUrl}`;
        }
      } else {
        finalUrl = downloadUrl;
      }
    }

    console.debug('REPORT DOWNLOAD DEBUG', { downloadUrl, finalUrl, hasToken: !!token });

    const response = await axios.get(finalUrl, {
      responseType: 'blob',
      timeout: opts.timeout || 120000,
      headers: {
        ...(opts.headers || {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
    });

    const contentType = String(response.headers['content-type'] || '');

    

    if (!response.data || (response.data.size === 0)) {
      throw new Error('The server returned an empty report file.');
    }

    const blob = new Blob([response.data], { type: contentType || 'application/octet-stream' });
    const objectUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = objectUrl;
    link.download = filename;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    setTimeout(() => {
      document.body.removeChild(link);
      URL.revokeObjectURL(objectUrl);
    }, 2000);

    return { success: true, size: blob.size, contentType };
  } catch (error) {
    console.error('REPORT DOWNLOAD FAILED', error);
    if (error?.response) {
      try {
        const errData = error.response.data;
        if (errData && typeof errData.text === 'function') {
          const txt = await errData.text();
          console.error('Server error blob text:', txt);
        } else {
          console.error('Server error response:', errData);
        }
      } catch (e) {
        console.error('Failed to extract server error details', e);
      }
    }
    throw error;
  }
}export const api = {
  // Auth
  login: (data) => apiClient.post('/auth/login', data),
  logout: () => apiClient.post('/auth/logout'),
  getCurrentUser: () => apiClient.get('/auth/me'),
  
  // Health
  getHealth: () => apiClient.get('/health'),

  // Employees
  getEmployees: (params) => apiClient.get('/employees', { params }),
  getEmployeeById: (empId) => apiClient.get(`/employees/${empId}`),
  createEmployee: (data) => apiClient.post('/employees', data),
  updateEmployee: (empId, data) => apiClient.put(`/employees/${empId}`, data),
  deleteEmployee: (empId) => apiClient.delete(`/employees/${empId}`),

  // Attendance
  getAttendance: (params) => apiClient.get('/attendance', { params }),
  getAttendanceAnomalies: () => apiClient.get('/attendance/anomalies'),
  getAttendanceContext: (empId) => apiClient.get('/attendance/today-context', { params: { empId } }),
  submitAttendanceException: (data) => apiClient.post('/attendance/exceptions', data),
  checkIn: (data) => apiClient.post('/attendance/check-in', data),
  checkOut: (data) => apiClient.post('/attendance/check-out', data),

  // Leaves
  getLeaves: (params) => apiClient.get('/leaves', { params }),
  getLeaveBalance: () => apiClient.get('/leaves/balance'),
  submitLeave: (data) => apiClient.post('/leaves', data),
  updateLeaveStatus: (leaveId, status, approverComments) =>
    apiClient.put(`/leaves/${leaveId}/status`, { status, approverComments }),

  // Shifts
  getShifts: (params) => apiClient.get('/shifts', { params }),
  submitShiftRequest: (data) => apiClient.post('/shifts', data),
  updateShiftStatus: (shiftId, status) => apiClient.put(`/shifts/${shiftId}/status`, { status }),

  // Timesheets
  getTimesheets: (params) => apiClient.get('/timesheets', { params }),
  submitTimesheet: (data) => apiClient.post('/timesheets', data),
  updateTimesheetStatus: (timesheetId, status) => apiClient.put(`/timesheets/${timesheetId}/status`, null, { params: { new_status: status } }),

  // Payroll
  getPayroll: (params) => apiClient.get('/payroll', { params }),
  calculatePayroll: (month) => apiClient.post('/payroll/calculate', null, { params: { month } }),
  disbursePayroll: (payrollId) => apiClient.put(`/payroll/${payrollId}/disburse`),
  // Download payslip PDF (returns blob)
  downloadPayslip: (empId, month) => apiClient.get(`/payroll/${empId}/payslip`, { params: { month }, responseType: 'blob' }),
  // Export payroll CSV (returns blob)
  exportPayroll: (month) => apiClient.get('/payroll/export', { params: { month }, responseType: 'blob' }),

  // Performance
  getPerformance: () => apiClient.get('/performance'),
  getEmployeePerformance: (empId) => apiClient.get(`/performance/${empId}`),

  // Notifications
  getNotifications: () => apiClient.get('/notifications'),
  getUnreadNotificationCount: () => apiClient.get('/notifications/unread-count'),
  markNotificationRead: (id) => apiClient.put(`/notifications/${id}/read`),
  markAllNotificationsRead: () => apiClient.post('/notifications/mark-all-read'),

  // Audit Logs
  getAuditLogs: () => apiClient.get('/audit-logs'),
  createAuditLog: (data) => apiClient.post('/audit-logs', data),

  // Reports
  generateReport: (data) => apiClient.post('/reports/generate', data),
  getReportSummary: () => apiClient.get('/reports/summary'),
  // Download report by relative URL (returns a blob)
  downloadReportByUrl: (downloadUrl) => apiClient.get(downloadUrl, { responseType: 'blob' }),
  // Helper exposed on the api object so callers can trigger authenticated download+save
  downloadAndSave: (downloadUrl, filename, opts = {}) => downloadAndSave(downloadUrl, filename, opts),

  // Settings
  getSettings: () => apiClient.get('/settings'),
  updateSettings: (data) => apiClient.put('/settings', data),
  getSettingsStatus: () => apiClient.get('/settings/status'),

  // Profile
  getProfile: () => apiClient.get('/profile'),
  updateProfile: (data) => apiClient.put('/profile', data),

  // Change password
  changePassword: (payload) => apiClient.post('/auth/change-password', payload),

  // Holidays
  getHolidays: (month) => apiClient.get('/holidays', { params: { month } }),

  // AI Intelligence
  sendChatMessage: (message, role, context) => apiClient.post('/chat', { message, role, context }),
  getAIInsights: (type, department) => apiClient.post('/ai-insights', { type, department }),

  // Workforce planning simulation and hiring plans
  simulateWorkforcePlan: (payload) => apiClient.post('/ai/workforce-simulate', payload),
  createHiringPlan: (payload) => apiClient.post('/ai/hiring-plans', payload),
  getHiringPlans: () => apiClient.get('/ai/hiring-plans'),

  // Executive Dashboard Analytics
  getDashboardAnalytics: () => apiClient.get('/analytics/dashboard'),
};

export default apiClient;
