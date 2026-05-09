import api from './client'

export function login(username, password) {
  return api.post('/auth/login', { username, password })
}
export function register(username, password) {
  return api.post('/auth/register', { username, password })
}
export function getMe() {
  return api.get('/auth/me')
}
export function logout() {
  return api.post('/auth/logout')
}

// User management (admin)
export function getUsers(page = 1, pageSize = 20) {
  return api.get('/users', { params: { page, page_size: pageSize } })
}
export function createUser(data) {
  return api.post('/users', data)
}
export function updateUser(userId, data) {
  return api.put(`/user/${userId}`, data)
}
export function deleteUser(userId) {
  return api.delete(`/user/${userId}`)
}
