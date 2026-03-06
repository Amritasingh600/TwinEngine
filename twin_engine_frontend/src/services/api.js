import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh on 401 (with lock to prevent parallel refresh attempts)
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(newToken) {
  refreshSubscribers.forEach((cb) => cb(newToken));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb);
}

api.interceptors.response.use(
  (res) => res,
  async (err) => {
    const original = err.config;
    if (err.response?.status === 401 && !original._retry) {
      original._retry = true;

      // If already refreshing, queue this request to retry after refresh completes
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          addRefreshSubscriber((newToken) => {
            original.headers.Authorization = `Bearer ${newToken}`;
            resolve(api(original));
          });
        });
      }

      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        isRefreshing = true;
        try {
          const { data } = await axios.post(`${API_BASE}/api/auth/token/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          if (data.refresh) localStorage.setItem('refresh_token', data.refresh);
          isRefreshing = false;
          onRefreshed(data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return api(original);
        } catch {
          isRefreshing = false;
          refreshSubscribers = [];
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(err);
  }
);

// --- Auth ---
export const login = (username, password) =>
  api.post('/auth/token/', { username, password });

export const getProfile = () => api.get('/auth/me/');

// --- Outlets ---
export const getOutlets = () => api.get('/outlets/');

// --- Floor / Nodes ---
export const getNodes = (outletId) =>
  api.get('/nodes/', { params: { outlet: outletId, is_active: true } });

export const getFlowGraph = (outletId) =>
  api.get('/flows/graph/', { params: { outlet: outletId } });

export const updateNodeStatus = (nodeId, status) =>
  api.post(`/nodes/${nodeId}/update_status/`, { status });

// --- Orders ---
export const getOrders = (params) => api.get('/orders/', { params });

export const getOrder = (id) => api.get(`/orders/${id}/`);

export const updateOrderStatus = (id, newStatus) =>
  api.post(`/orders/${id}/update_status/`, { status: newStatus });

// --- Predictions ---
export const getPredictionDashboard = (outletId, date) =>
  api.get('/predictions/dashboard/', { params: { outlet: outletId, date } });

export const getBusyHours = (outletId, date) =>
  api.get('/predictions/busy-hours/', { params: { outlet: outletId, date } });

export const getFootfall = (outletId, date) =>
  api.get('/predictions/footfall/', { params: { outlet: outletId, date } });

export const getRevenue = (outletId, date) =>
  api.get('/predictions/revenue/', { params: { outlet: outletId, date } });

export const getFoodDemand = (outletId, date) =>
  api.get('/predictions/food-demand/', { params: { outlet: outletId, date } });

export const getInventoryAlerts = (outletId) =>
  api.get('/predictions/inventory-alerts/', { params: { outlet: outletId } });

export const getStaffing = (outletId, date) =>
  api.get('/predictions/staffing/', { params: { outlet: outletId, date } });

export const trainModels = (outletId) =>
  api.post('/predictions/train/', null, { params: { outlet: outletId, sync: true } });

// --- Orders (create) ---
export const createOrder = (data) => api.post('/orders/', data);

// --- Inventory ---
export const getInventory = (outletId) =>
  api.get('/inventory/', { params: { outlet: outletId } });

export const createInventoryItem = (data) => api.post('/inventory/', data);

export const updateInventoryItem = (itemId, data) =>
  api.patch(`/inventory/${itemId}/`, data);

export const deleteInventoryItem = (itemId) =>
  api.delete(`/inventory/${itemId}/`);

// --- Payments ---
export const getPayments = (params) => api.get('/payments/', { params });

export const createPayment = (data) => api.post('/payments/', data);

export const updatePayment = (paymentId, data) =>
  api.patch(`/payments/${paymentId}/`, data);

// --- Staff ---
export const getStaff = (outletId) =>
  api.get('/staff/', { params: { outlet: outletId, is_on_shift: true } });

export const getAllStaff = (outletId) =>
  api.get('/staff/', { params: { outlet: outletId } });

export const updateStaffMember = (staffId, data) =>
  api.patch(`/staff/${staffId}/`, data);

// --- Reports ---
export const generateReport = (outletId, reportType, startDate) =>
  api.post('/reports/generate/', {
    outlet_id: outletId,
    report_type: reportType,
    start_date: startDate,
  });

export const getDailySummaries = (outletId) =>
  api.get('/summaries/', { params: { outlet: outletId } });

// --- Data Generation ---
export const generateData = (outletId, date, orderCount = 40, days = 14) =>
  api.post('/generate-data/', {
    outlet_id: outletId,
    date,
    order_count: orderCount,
    days,
  });

export default api;
