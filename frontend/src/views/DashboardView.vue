<template>
  <div class="dashboard-shell">
    <section class="portal-hero">
      <div>
        <p class="eyebrow">Online courses</p>
        <h1>Course subscriptions</h1>
        <p class="hero-copy">
          Register a subscriber, review available courses, and manage active enrollments from one focused workspace.
        </p>
      </div>
      <div class="hero-actions">
        <span class="session-pill" :class="{ active: logged }">{{ logged ? 'Session active' : 'Guest session' }}</span>
        <router-link v-if="!logged" to="/login" class="btn btn-light">Login</router-link>
        <button v-else class="btn btn-outline-light" @click="logout">Logout</button>
      </div>
    </section>

    <section class="status-grid">
      <div class="metric">
        <span class="metric-label">Available courses</span>
        <strong>{{ courses.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Active enrollments</span>
        <strong>{{ activeEnrollments.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Subscriber</span>
        <strong>{{ subscriberId ? `#${subscriberId}` : 'Pending' }}</strong>
      </div>
    </section>

    <section class="subscriber-panel">
      <div>
        <p class="eyebrow">Subscriber profile</p>
        <h2>{{ subscriberId ? 'Subscriber ready' : 'Create subscriber' }}</h2>
        <p class="panel-copy">
          {{ subscriberId ? 'This browser is linked to a subscriber and can enroll in courses.' : 'Start by registering the learner who will receive access to the courses.' }}
        </p>
      </div>
      <form v-if="!subscriberId" class="subscriber-form" @submit.prevent="createSubscriber">
        <input class="form-control" v-model="newSubscriber.email" placeholder="Email" type="email" required />
        <input class="form-control" v-model="newSubscriber.full_name" placeholder="Full name" required />
        <button class="btn btn-primary" type="submit">Create</button>
      </form>
      <div v-else class="subscriber-actions">
        <button class="btn btn-outline-primary" @click="clearSubscriber">Change subscriber</button>
      </div>
    </section>

    <section class="courses-section">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Catalog</p>
          <h2>Courses</h2>
        </div>
        <button class="btn btn-sm btn-outline-secondary" @click="fetchDevToken">Dev token</button>
      </div>

      <LoadingState
        v-if="loadingDashboard"
        title="Loading courses"
        message="Fetching courses and active enrollments."
      />

      <div v-else-if="courses.length === 0" class="empty-state">
        <strong>No courses available</strong>
        <span>Create courses from the admin area to publish them here.</span>
      </div>

      <div v-else class="course-grid">
        <BaseCard v-for="c in courses" :key="c.id" classes="course-card">
          <template #header>
            <div class="course-visual">
              <span>{{ courseInitials(c.title) }}</span>
            </div>
          </template>
          <div class="course-body">
            <div class="course-title-row">
              <h3>{{ c.title }}</h3>
              <span v-if="isEnrolled(c.id)" class="status-badge enrolled">Active</span>
            </div>
            <p>{{ c.description || 'No description provided yet.' }}</p>
            <div class="course-meta">
              <strong>${{ formatPrice(c.price) }}</strong>
              <span>{{ c.max_students || 'Open' }} seats</span>
            </div>
          </div>
          <template #footer>
            <div class="course-actions">
              <BaseButton size="sm" variant="primary" v-if="!isEnrolled(c.id)" @click="subscribe(c.id)">Subscribe</BaseButton>
              <BaseButton size="sm" variant="outline-danger" v-else @click="unsubscribe(isEnrolled(c.id).id)">Cancel</BaseButton>
            </div>
          </template>
        </BaseCard>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getCourses, createSubscriber as apiCreateSubscriber, getEnrollmentsBySubscriber, createEnrollment, cancelEnrollment, createPreference } from '../services/api'
import { useRouter } from 'vue-router'
import { useToastStore } from '../stores/toast'
import BaseButton from '../components/BaseButton.vue'
import BaseCard from '../components/BaseCard.vue'
import LoadingState from '../components/LoadingState.vue'

const courses = ref([])
const logged = ref(false)
const loadingDashboard = ref(false)
const router = useRouter()
const toast = useToastStore()

const subscriberId = ref(localStorage.getItem('subscriber_id') || null)
const enrollments = ref([])
const newSubscriber = ref({ email: '', full_name: '' })
const activeEnrollments = computed(() => enrollments.value.filter(e => e.status === 'active'))

function logout() {
  localStorage.removeItem('access_token')
  logged.value = false
  router.push('/login')
}

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  logged.value = !!token
  loadingDashboard.value = true
  try {
    courses.value = await getCourses()
    if(subscriberId.value){ await loadEnrollments() }
  } catch (err) {
    console.error(err)
  } finally {
    loadingDashboard.value = false
  }
})

async function fetchDevToken() {
  try {
    const resp = await fetch('/api/v1/auth/dev-token')
    if (!resp.ok) throw new Error('No dev token')
    const data = await resp.json()
    localStorage.setItem('access_token', data.access_token)
    logged.value = true
    toast.success('Dev token saved')
  } catch (err) {
    toast.error('Failed to get dev token: ' + (err?.message || err))
  }
}

async function createSubscriber(){
  try{
    const s = await apiCreateSubscriber(newSubscriber.value)
    subscriberId.value = s.id
    localStorage.setItem('subscriber_id', String(s.id))
    newSubscriber.value = { email: '', full_name: '' }
    toast.success('Subscriber created')
    await loadEnrollments()
  }catch(e){ /* errors bubbled by api.js */ }
}

async function loadEnrollments(){
  if(!subscriberId.value) return
  enrollments.value = await getEnrollmentsBySubscriber(subscriberId.value)
}

function isEnrolled(courseId){
  return enrollments.value.find(e => e.course_id === courseId && e.status === 'active')
}

async function subscribe(courseId){
  if(!subscriberId.value){ toast.error('Create a subscriber first'); return }
  try{
    const en = await createEnrollment({ subscriber_id: Number(subscriberId.value), course_id: courseId })
    toast.success('Subscribed, redirecting to payment')
    const course = courses.value.find(c => c.id === courseId) || { title: 'Course', price: 0 }
    const pref = await createPreference({ enrollment_id: en.id, title: course.title, price: Number(course.price || 0) })
    if(pref?.init_point){ window.location.href = pref.init_point }
    await loadEnrollments()
  }catch(e){}
}

async function unsubscribe(enrollmentId){
  try{
    await cancelEnrollment(enrollmentId)
    toast.success('Subscription cancelled')
    await loadEnrollments()
  }catch(e){}
}

function clearSubscriber(){
  localStorage.removeItem('subscriber_id')
  subscriberId.value = null
  enrollments.value = []
}

function courseInitials(title){
  return String(title || 'Course')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('')
}

function formatPrice(price){
  return Number(price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}
</script>
