<template>
  <div class="student-shell">
    <section class="student-header">
      <div>
        <p class="eyebrow">Learning workspace</p>
        <h1>My courses</h1>
        <p class="admin-copy">Review your active subscriptions, open course details, and access your learning materials.</p>
      </div>
      <div class="header-actions">
        <RouterLink class="btn btn-outline-secondary" to="/">Browse catalog</RouterLink>
        <button v-if="!isAuthenticated" class="btn btn-primary" type="button" @click="login">Login</button>
      </div>
    </section>

    <section class="status-grid student-metrics">
      <div class="metric">
        <span class="metric-label">Active courses</span>
        <strong>{{ subscribedCourses.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Next class</span>
        <strong>{{ nextCourseDateLabel }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Profile</span>
        <strong>{{ appUser ? 'Ready' : 'Pending' }}</strong>
      </div>
    </section>

    <section v-if="!isAuthenticated" class="empty-state student-empty">
      <strong>Login to see your courses</strong>
      <span>Your subscriptions and private materials are available after login.</span>
    </section>

    <section v-else-if="syncError" class="empty-state student-empty">
      <strong>Profile sync failed</strong>
      <span>{{ syncError }}</span>
      <button class="btn btn-primary" type="button" @click="syncSubscriber(true)">Retry</button>
    </section>

    <LoadingState
      v-else-if="loading"
      title="Loading your courses"
      message="Preparing your active subscriptions."
    />

    <section v-else-if="subscribedCourses.length === 0" class="empty-state student-empty">
      <strong>No active course subscriptions</strong>
      <span>Subscribe to a course from the catalog and it will appear here.</span>
      <RouterLink class="btn btn-primary" to="/">Browse courses</RouterLink>
    </section>

    <section v-else class="my-courses-section">
      <div class="my-courses-table-panel">
        <div class="panel-heading">
          <div>
            <p class="eyebrow">Active subscriptions</p>
            <h2>Course list</h2>
          </div>
          <span class="catalog-count">{{ paginationLabel }}</span>
        </div>

        <div class="table-responsive">
          <table class="admin-table my-courses-table">
            <thead>
              <tr>
                <th>Course</th>
                <th>Date</th>
                <th>Payment</th>
                <th>Subscribed</th>
                <th>Status</th>
                <th class="actions-column">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="item in pagedCourses" :key="item.id">
                <td>
                  <div class="course-list-cell">
                    <span class="course-avatar">{{ courseInitials(item.title) }}</span>
                    <div>
                      <strong>{{ item.title }}</strong>
                    </div>
                  </div>
                </td>
                <td>{{ courseDateLabel(item) }}</td>
                <td>{{ item.enrollment.payment_status }}</td>
                <td>{{ subscriptionDateLabel(item.enrollment.created_at) }}</td>
                <td>
                  <span class="status-badge" :class="courseProgressStatusClass(item)">{{ courseProgressStatusLabel(item) }}</span>
                </td>
                <td>
                  <div class="row-actions">
                    <RouterLink class="btn btn-sm btn-outline-secondary" :to="`/my-courses/${item.id}`">Open</RouterLink>
                    <button
                      v-if="canJoinVirtualClass(item)"
                      class="btn btn-sm btn-success"
                      type="button"
                      @click="joinVirtualClass(item)"
                    >
                      Zoom
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="table-pagination">
          <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="currentPage === 1" @click="currentPage -= 1">
            Previous
          </button>
          <span>Page {{ currentPage }} of {{ totalPages }}</span>
          <button class="btn btn-sm btn-outline-secondary" type="button" :disabled="currentPage === totalPages" @click="currentPage += 1">
            Next
          </button>
        </div>
      </div>

      <div class="my-course-grid">
        <article v-for="item in subscribedCourses" :key="item.id" class="my-course-card">
          <div class="my-course-mark">
            <span>{{ courseInitials(item.title) }}</span>
          </div>
          <div class="my-course-body">
            <div class="front-course-title">
              <h2>{{ item.title }}</h2>
              <span class="status-badge" :class="courseProgressStatusClass(item)">{{ courseProgressStatusLabel(item) }}</span>
            </div>
            <p>{{ item.description || 'Course details will be available soon.' }}</p>
            <div class="course-detail-facts">
              <span>{{ courseDateLabel(item) }}</span>
              <span>{{ item.enrollment.payment_status }}</span>
              <span>{{ formatDate(item.enrollment.created_at) }}</span>
            </div>
          </div>
          <div class="my-course-actions">
            <RouterLink class="btn btn-primary" :to="`/my-courses/${item.id}`">Open course</RouterLink>
            <button
              v-if="canJoinVirtualClass(item)"
              class="btn btn-success"
              type="button"
              @click="joinVirtualClass(item)"
            >
              Join Zoom class
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink } from 'vue-router'
import { useAuth0 } from '@auth0/auth0-vue'
import { createSubscriber as apiCreateSubscriber, getCourses, getEnrollmentsBySubscriber, getVirtualAccess, syncExternalUser } from '../services/api'
import { useToastStore } from '../stores/toast'
import LoadingState from '../components/LoadingState.vue'

const toast = useToastStore()
const { idTokenClaims, isAuthenticated, isLoading, loginWithRedirect, user } = useAuth0()
const courses = ref([])
const enrollments = ref([])
const appUser = ref(null)
const subscriberId = ref(null)
const loading = ref(false)
const syncInFlight = ref(false)
const syncError = ref('')
const currentPage = ref(1)
const pageSize = 8

const activeEnrollments = computed(() => enrollments.value.filter(enrollment => enrollment.status === 'active'))
const subscribedCourses = computed(() => activeEnrollments.value
  .map(enrollment => {
    const course = courses.value.find(item => item.id === enrollment.course_id)
    return course ? { ...course, enrollment } : null
  })
  .filter(Boolean)
  .sort((a, b) => sortDateKey(a).localeCompare(sortDateKey(b)))
)
const nextCourseDateLabel = computed(() => {
  const today = todayKey()
  const next = subscribedCourses.value.find(course => course.scheduled_date && course.scheduled_date >= today)
  return next ? courseDateLabel(next) : 'TBD'
})
const totalPages = computed(() => Math.max(Math.ceil(subscribedCourses.value.length / pageSize), 1))
const pagedCourses = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return subscribedCourses.value.slice(start, start + pageSize)
})
const paginationLabel = computed(() => {
  if(subscribedCourses.value.length === 0) return '0 courses'
  const start = (currentPage.value - 1) * pageSize + 1
  const end = Math.min(currentPage.value * pageSize, subscribedCourses.value.length)
  return `${start}-${end} of ${subscribedCourses.value.length}`
})

onMounted(load)
watch([isLoading, isAuthenticated, user, idTokenClaims], load, { immediate: true })
watch(totalPages, (pages) => {
  if(currentPage.value > pages) currentPage.value = pages
})

async function load(){
  if(isLoading.value) return
  loading.value = true
  try{
    courses.value = await getCourses()
    if(!isAuthenticated.value) return
    await syncSubscriber()
  }finally{
    if(!syncInFlight.value) loading.value = false
  }
}

async function login(){
  await loginWithRedirect({ appState: { target: '/my-courses' } })
}

async function syncSubscriber(force = false){
  if(isLoading.value || !isAuthenticated.value || !user.value?.sub || syncInFlight.value) return
  if(appUser.value && subscriberId.value && !force) return
  syncInFlight.value = true
  syncError.value = ''
  try{
    const claims = idTokenClaims.value
    if(!claims?.__raw) throw new Error('Identity provider did not return a raw ID token')
    appUser.value = await syncExternalUser(claims.__raw)
    const subscriber = await apiCreateSubscriber({
      full_name: user.value.name || user.value.email || 'LabSchool user',
      email: user.value.email,
      phone: '',
    })
    subscriberId.value = subscriber.id
    enrollments.value = await getEnrollmentsBySubscriber(subscriber.id)
  }catch(e){
    syncError.value = e?.message || 'Could not prepare your student profile'
  }finally{
    syncInFlight.value = false
    loading.value = false
  }
}

function courseInitials(title){
  return String(title || 'Course')
    .split(' ')
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('')
}

function courseDateLabel(course){
  if(!course.scheduled_date) return 'Date to be confirmed'
  return new Date(`${course.scheduled_date}T00:00:00`).toLocaleDateString()
}

function formatDate(value){
  if(!value) return 'Requested recently'
  return `Subscribed ${new Date(value).toLocaleDateString()}`
}

function subscriptionDateLabel(value){
  if(!value) return '-'
  return new Date(value).toLocaleDateString()
}

function todayKey(){
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function sortDateKey(course){
  return course.scheduled_date || '9999-12-31'
}

function canJoinVirtualClass(course){
  return Boolean(course.enrollment && course.scheduled_date === todayKey())
}

function courseProgressStatusLabel(course){
  if(!course.scheduled_date) return 'No date yet'
  if(course.scheduled_date < todayKey()) return 'Completed'
  if(course.scheduled_date === todayKey()) return 'Today'
  return 'Upcoming'
}

function courseProgressStatusClass(course){
  if(!course.scheduled_date) return 'neutral'
  if(course.scheduled_date < todayKey()) return 'completed'
  if(course.scheduled_date === todayKey()) return 'today'
  return 'upcoming'
}

async function joinVirtualClass(course){
  try{
    const access = await getVirtualAccess(course.enrollment.id)
    window.open(access.zoom_url, '_blank', 'noopener,noreferrer')
  }catch(e){
    toast.error('Virtual access is not available yet')
  }
}
</script>
