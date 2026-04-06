export const API_BASE = 'http://localhost:8000';

export const API_ENDPOINTS = {
  DEMO_SEED: '/demo/seed',
  STATS: '/stats',
  CONTACTS: '/contacts',
  CALLS: '/calls',
  CALL_DETAIL: (id) => `/calls/${id}`,
};
