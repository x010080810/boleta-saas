import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api`,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken && error.config.url !== '/auth/login') {
        try {
          const res = await api.post('/auth/refresh', { token: refreshToken });
          localStorage.setItem('access_token', res.data.access_token);
          localStorage.setItem('refresh_token', res.data.refresh_token);
          error.config.headers.Authorization = `Bearer ${res.data.access_token}`;
          return api(error.config);
        } catch {
          localStorage.clear();
          window.location.href = '/login';
        }
      } else {
        localStorage.clear();
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;

export const authApi = {
  login: (email: string, password: string) =>
    api.post('/auth/login', { email, password }),
  superLogin: (email: string, password: string) =>
    api.post('/auth/super-login', { email, password }),
  register: (data: any) =>
    api.post('/auth/register', data),
  me: () => api.get('/auth/me'),
};

export const companiesApi = {
  list: () => api.get('/companies'),
  get: (id: string) => api.get(`/companies/${id}`),
  update: (id: string, data: any) => api.put(`/companies/${id}`, data),
  employees: (id: string) => api.get(`/companies/${id}/employees`),
  createEmployee: (id: string, data: any) =>
    api.post(`/companies/${id}/employees`, data),
  batchEmployees: (id: string, data: any) =>
    api.post(`/companies/${id}/employees/batch`, data),
  testSmtp: (data: any) => api.post('/companies/test-smtp', data),
};

export const payrollApi = {
  upload: (companyId: string, formData: FormData) =>
    api.post(`/companies/${companyId}/payroll/upload`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }),
  list: (companyId: string, params?: any) =>
    api.get(`/companies/${companyId}/payroll/uploads`, { params }),
  preview: (companyId: string, uploadId: string) =>
    api.get(`/companies/${companyId}/payroll/uploads/${uploadId}/preview`),
  process: (companyId: string, uploadId: string) =>
    api.post(`/companies/${companyId}/payroll/uploads/${uploadId}/process`),
  deletePending: (companyId: string, uploadId: string) =>
    api.delete(`/companies/${companyId}/payroll/uploads/${uploadId}`),
  status: (companyId: string, uploadId: string) =>
    api.get(`/companies/${companyId}/payroll/uploads/${uploadId}/status`),
  report: (companyId: string, uploadId: string) =>
    api.get(`/companies/${companyId}/payroll/uploads/${uploadId}/report`),
  boletas: (companyId: string, uploadId: string) =>
    api.get(`/companies/${companyId}/payroll/uploads/${uploadId}/boletas`),
  download: (companyId: string, boletaId: string) =>
    api.get(`/companies/${companyId}/payroll/boletas/${boletaId}/download`, {
      responseType: 'blob',
    }),
  resend: (companyId: string, uploadId: string, data: any) =>
    api.post(`/companies/${companyId}/payroll/uploads/${uploadId}/resend`, data),
  quotaStatus: (companyId: string) =>
    api.get(`/companies/${companyId}/payroll/quota-status`),
};

export const adminApi = {
  companies: () => api.get('/admin/companies'),
  createCompany: (data: any) => api.post('/admin/companies', data),
  getCompany: (id: string) => api.get(`/admin/companies/${id}`),
  updateLicense: (id: string, data: any) =>
    api.put(`/admin/companies/${id}/license`, data),
  expiring: (dias?: number) =>
    api.get('/admin/license/expiring', { params: { dias } }),
  gracePeriod: () => api.get('/admin/license/grace-period'),
  stats: () => api.get('/admin/stats'),
  dashboard: () => api.get('/admin/dashboard'),
  licenseHistory: (id: string) =>
    api.get(`/admin/companies/${id}/license-history`),
  getSystemSettings: () => api.get('/admin/system-settings'),
  updateSystemSettings: (data: any) => api.put('/admin/system-settings', data),
  users: () => api.get('/admin/users'),
  createUser: (data: any) => api.post('/admin/users', data),
  getUser: (id: string) => api.get(`/admin/users/${id}`),
  companyUsers: (companyId: string) =>
    api.get(`/admin/companies/${companyId}/users`),
  assignUser: (companyId: string, data: any) =>
    api.post(`/admin/companies/${companyId}/users`, data),
  updateAssignment: (companyId: string, userId: string, data: any) =>
    api.put(`/admin/companies/${companyId}/users/${userId}`, data),
  removeAssignment: (companyId: string, userId: string) =>
    api.delete(`/admin/companies/${companyId}/users/${userId}`),
};

export const templatesApi = {
  downloadExcel: () => api.get('/templates/excel', {
    responseType: 'blob',
  }),
};
