import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use((config) => {
  const stored = localStorage.getItem('doctorbook_user')
  if (stored) {
    const { access_token } = JSON.parse(stored)
    if (access_token) config.headers.Authorization = `Bearer ${access_token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('doctorbook_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──
export const authAPI = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  me: () => api.get('/auth/me'),
}

// ── Specializations ──
export const specAPI = {
  list: () => api.get('/specializations'),
  create: (data) => api.post('/specializations', data),
  delete: (id) => api.delete(`/specializations/${id}`),
}

// ── Doctors ──
export const doctorAPI = {
  list: (specializationId) => api.get('/doctors', { params: { specialization_id: specializationId } }),
  get: (id) => api.get(`/doctors/${id}`),
  create: (data) => api.post('/doctors', data),
  update: (id, data) => api.put(`/doctors/${id}`, data),
}

// ── Slots ──
export const slotAPI = {
  list: (doctorId, params) => api.get(`/doctors/${doctorId}/slots`, { params }),
  create: (doctorId, data) => api.post(`/doctors/${doctorId}/slots`, data),
  createBulk: (doctorId, data) => api.post(`/doctors/${doctorId}/slots/bulk`, data),
  delete: (doctorId, slotId) => api.delete(`/doctors/${doctorId}/slots/${slotId}`),
  clearFuture: (doctorId) => api.delete(`/doctors/${doctorId}/slots/future`),
}

// ── Appointments ──
export const appointmentAPI = {
  book: (data) => api.post('/appointments', data),
  my: () => api.get('/appointments/my'),
  all: () => api.get('/appointments/all'),
  cancel: (id) => api.put(`/appointments/${id}/cancel`),
  complete: (id, data) => api.put(`/appointments/${id}/complete`, data),
}

// ── Users ──
export const userAPI = {
  list: () => api.get('/users'),
}

// ── Chat ──
export const chatAPI = {
  ask: (message) => api.post('/chat', { message }),
}

export default api
