import axios from 'axios'
import { useToastStore } from '../stores/toast'

const api = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('idp_token') || localStorage.getItem('auth0_token') || localStorage.getItem('access_token')
  if (token && !config.headers.Authorization) config.headers.Authorization = `Bearer ${token}`
  return config
})

function handleApiError(e, prefix = 'Request failed'){
  try{
    const toast = useToastStore()
    const msg = (e?.response?.data?.detail) || e?.message || String(e)
    toast.error(`${prefix}: ${msg}`)
  }catch(err){
    console.error('Toast unavailable', err)
  }
  throw e
}

export async function login(email, password) {
  try{
    const resp = await api.post('/auth/login', { email, password })
    return resp.data
  }catch(e){ return handleApiError(e, 'Login failed') }
}

export async function register(email, password, full_name = '') {
  try{
    const resp = await api.post('/auth/register', { email, password, full_name })
    return resp.data
  }catch(e){ return handleApiError(e, 'Register failed') }
}

export async function syncExternalUser(idToken) {
  try{
    const resp = await api.post('/auth/sync', {}, {
      headers: { Authorization: `Bearer ${idToken}` },
    })
    localStorage.setItem('idp_token', idToken)
    localStorage.setItem('auth0_token', idToken)
    localStorage.setItem('app_user', JSON.stringify(resp.data))
    window.dispatchEvent(new CustomEvent('app-user-updated', { detail: resp.data }))
    return resp.data
  }catch(e){ return handleApiError(e, 'Sync user failed') }
}

export const syncAuth0User = syncExternalUser

export async function getCourses() {
  try{
    const resp = await api.get('/courses')
    return resp.data
  }catch(e){ return handleApiError(e, 'Get courses failed') }
}

export async function getAdminCourses() {
  try{
    const resp = await api.get('/courses/admin')
    return resp.data
  }catch(e){ return handleApiError(e, 'Get admin courses failed') }
}

export async function createCourse(payload) {
  try{
    const resp = await api.post('/courses', payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Create course failed') }
}

export async function updateCourse(id, payload) {
  try{
    const resp = await api.put(`/courses/${id}`, payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Update course failed') }
}

export async function deleteCourse(id) {
  try{
    const resp = await api.delete(`/courses/${id}`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Delete course failed') }
}

export async function listCourseFiles(courseId) {
  try{
    const resp = await api.get(`/courses/${courseId}/files`)
    return resp.data
  }catch(e){ return handleApiError(e, 'List course files failed') }
}

export async function listCourseResources(courseId) {
  try{
    const resp = await api.get(`/courses/${courseId}/resources`)
    return resp.data
  }catch(e){ return handleApiError(e, 'List course resources failed') }
}

export async function uploadCourseFile(courseId, file) {
  try{
    const formData = new FormData()
    formData.append('file', file)
    const resp = await api.post(`/courses/${courseId}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return resp.data
  }catch(e){ return handleApiError(e, 'Upload course file failed') }
}

export async function deleteCourseFile(courseId, fileId) {
  try{
    const resp = await api.delete(`/courses/${courseId}/files/${fileId}`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Delete course file failed') }
}

export async function downloadCourseFile(courseId, file) {
  try{
    const resp = await api.get(`/courses/${courseId}/files/${file.id}/download`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(resp.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = file.original_filename || 'course-file'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(blobUrl)
  }catch(e){ return handleApiError(e, 'Download course file failed') }
}

export async function downloadCourseResource(courseId, file) {
  try{
    const resp = await api.get(`/courses/${courseId}/resources/${file.id}/download`, {
      responseType: 'blob',
    })
    const blobUrl = window.URL.createObjectURL(resp.data)
    const link = document.createElement('a')
    link.href = blobUrl
    link.download = file.original_filename || 'course-resource'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(blobUrl)
  }catch(e){ return handleApiError(e, 'Download course resource failed') }
}

export async function getUsers() {
  try{
    const resp = await api.get('/users')
    return resp.data
  }catch(e){ return handleApiError(e, 'Get users failed') }
}

export async function createUser(payload) {
  try{
    const resp = await api.post('/users', payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Create user failed') }
}

export async function updateUser(id, payload) {
  try{
    const resp = await api.put(`/users/${id}`, payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Update user failed') }
}

export async function deleteUser(id) {
  try{
    const resp = await api.delete(`/users/${id}`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Delete user failed') }
}

export default api

// Subscribers
export async function createSubscriber(payload){
  try{
    const resp = await api.post('/subscribers', payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Create subscriber failed') }
}

export async function listSubscribers(){
  try{
    const resp = await api.get('/subscribers')
    return resp.data
  }catch(e){ return handleApiError(e, 'List subscribers failed') }
}

// Enrollments / subscriptions
export async function createEnrollment(payload){
  try{
    const resp = await api.post('/enrollments', payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Create enrollment failed') }
}

export async function getEnrollmentsBySubscriber(subscriber_id){
  try{
    const resp = await api.get(`/enrollments/subscriber/${subscriber_id}`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Get enrollments failed') }
}

export async function listEnrollments(){
  try{
    const resp = await api.get('/enrollments')
    return resp.data
  }catch(e){ return handleApiError(e, 'List enrollments failed') }
}

export async function cancelEnrollment(id){
  try{
    const resp = await api.post(`/enrollments/${id}/cancel`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Cancel enrollment failed') }
}

export async function getVirtualAccess(id){
  try{
    const resp = await api.get(`/enrollments/${id}/virtual-access`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Get virtual access failed') }
}

export async function markEnrollmentPaid(id){
  try{
    const resp = await api.post(`/enrollments/${id}/pay`)
    return resp.data
  }catch(e){ return handleApiError(e, 'Mark enrollment paid failed') }
}

// Mercado Pago preference
export async function createPreference(payload){
  try{
    const resp = await api.post('/payments/create_preference', payload)
    return resp.data
  }catch(e){ return handleApiError(e, 'Create preference failed') }
}
