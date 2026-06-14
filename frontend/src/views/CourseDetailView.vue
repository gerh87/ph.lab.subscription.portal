<template>
  <div class="student-shell">
    <section class="course-detail-hero">
      <div class="course-detail-heading">
        <RouterLink class="btn btn-outline-light btn-sm" to="/my-courses">Back to my courses</RouterLink>
        <p class="eyebrow">Course workspace</p>
        <h1>{{ course?.title || 'Course detail' }}</h1>
        <p>{{ course?.description || 'Course information and learning materials.' }}</p>
      </div>
      <div class="course-detail-summary">
        <span class="metric-label">Course date</span>
        <strong>{{ courseDateLabel(course) }}</strong>
        <span>{{ activeEnrollment ? activeEnrollment.payment_status : 'Subscription required' }}</span>
      </div>
    </section>

    <section v-if="!isAuthenticated" class="empty-state student-empty">
      <strong>Login to open this course</strong>
      <span>Your course detail is available after login.</span>
      <button class="btn btn-primary" type="button" @click="login">Login</button>
    </section>

    <LoadingState
      v-else-if="loading"
      title="Loading course detail"
      message="Collecting your subscription and materials."
    />

    <section v-else-if="!activeEnrollment" class="empty-state student-empty">
      <strong>You are not subscribed to this course</strong>
      <span>Only active subscribers can access private course details and attachments.</span>
      <RouterLink class="btn btn-primary" to="/">Browse catalog</RouterLink>
    </section>

    <template v-else>
      <section class="detail-tabs" aria-label="Course detail sections">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="detail-tab"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </section>

      <section v-if="activeTab === 'overview'" class="course-detail-grid">
        <article class="detail-panel">
          <p class="eyebrow">Overview</p>
          <h2>Course information</h2>
          <p>{{ course?.description || 'The course team will publish more information soon.' }}</p>
          <div class="course-detail-facts">
            <span>{{ courseDateLabel(course) }}</span>
            <span>{{ capacityLabel(course) }}</span>
            <span>{{ activeEnrollment.status }}</span>
          </div>
        </article>

        <article class="detail-panel">
          <p class="eyebrow">Virtual class</p>
          <h2>Online access</h2>
          <p>{{ virtualAccessCopy }}</p>
          <button
            class="btn btn-success"
            type="button"
            :disabled="!canJoinVirtualClass"
            @click="joinVirtualClass"
          >
            Join Zoom class
          </button>
        </article>
      </section>

      <section v-else-if="activeTab === 'schedule'" class="detail-panel">
        <p class="eyebrow">Schedule</p>
        <h2>Course timeline</h2>
        <div class="schedule-list">
          <div class="schedule-item">
            <span>1</span>
            <div>
              <strong>Subscription confirmed</strong>
              <p>{{ formatDate(activeEnrollment.created_at) }}</p>
            </div>
          </div>
          <div class="schedule-item">
            <span>2</span>
            <div>
              <strong>Course session</strong>
              <p>{{ courseDateLabel(course) }}</p>
            </div>
          </div>
          <div class="schedule-item">
            <span>3</span>
            <div>
              <strong>Materials and attachments</strong>
              <p>{{ materials.length }} private file{{ materials.length === 1 ? '' : 's' }} available for this course.</p>
            </div>
          </div>
        </div>
      </section>

      <section v-else class="course-detail-grid">
        <article class="detail-panel">
          <p class="eyebrow">Private materials</p>
          <h2>Attachments</h2>
          <div v-if="materials.length === 0" class="empty-state compact">
            <strong>No private files yet</strong>
            <span>Course files uploaded by the team will appear here.</span>
          </div>
          <div v-else class="course-file-list">
            <button
              v-for="file in materials"
              :key="file.id"
              class="course-file-row"
              type="button"
              @click="downloadMaterial(file)"
            >
              <span>
                <strong>{{ file.original_filename }}</strong>
                <small>{{ file.content_type || 'File' }} · {{ formatFileSize(file.size_bytes) }}</small>
              </span>
              <small>{{ formatDate(file.created_at) }}</small>
            </button>
          </div>
        </article>

        <article class="detail-panel">
          <p class="eyebrow">Public resources</p>
          <h2>Programs and guides</h2>
          <div v-if="resources.length === 0" class="empty-state compact">
            <strong>No public resources yet</strong>
            <span>Programs, guides, or brochures will appear here.</span>
          </div>
          <div v-else class="course-file-list">
            <button
              v-for="file in resources"
              :key="file.id"
              class="course-file-row"
              type="button"
              @click="downloadResource(file)"
            >
              <span>
                <strong>{{ file.original_filename }}</strong>
                <small>{{ file.content_type || 'File' }} · {{ formatFileSize(file.size_bytes) }}</small>
              </span>
              <small>{{ formatDate(file.created_at) }}</small>
            </button>
          </div>
        </article>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute } from 'vue-router'
import { useAuth0 } from '@auth0/auth0-vue'
import { createSubscriber as apiCreateSubscriber, downloadCourseFile, downloadCourseResource, getCourses, getEnrollmentsBySubscriber, getVirtualAccess, listCourseFiles, listCourseResources, syncExternalUser } from '../services/api'
import { useToastStore } from '../stores/toast'
import LoadingState from '../components/LoadingState.vue'

const route = useRoute()
const toast = useToastStore()
const { idTokenClaims, isAuthenticated, isLoading, loginWithRedirect, user } = useAuth0()
const course = ref(null)
const enrollments = ref([])
const materials = ref([])
const resources = ref([])
const loading = ref(false)
const syncInFlight = ref(false)
const activeTab = ref('overview')
const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'schedule', label: 'Schedule' },
  { id: 'materials', label: 'Materials' },
]

const courseId = computed(() => Number(route.params.id))
const activeEnrollment = computed(() => enrollments.value.find(enrollment => enrollment.course_id === courseId.value && enrollment.status === 'active'))
const canJoinVirtualClass = computed(() => Boolean(activeEnrollment.value && course.value?.scheduled_date === todayKey()))
const virtualAccessCopy = computed(() => {
  if(!course.value?.scheduled_date) return 'Virtual access will be available when the course date is confirmed.'
  if(canJoinVirtualClass.value) return 'The virtual classroom is open today for active subscribers.'
  return 'The Zoom link is shown only on the scheduled course date.'
})

onMounted(load)
watch([isLoading, isAuthenticated, user, idTokenClaims], load, { immediate: true })

async function load(){
  if(isLoading.value || !courseId.value || syncInFlight.value) return
  loading.value = true
  try{
    const courseList = await getCourses()
    course.value = courseList.find(item => item.id === courseId.value) || null
    resources.value = await listCourseResources(courseId.value)
    if(!isAuthenticated.value) return
    await syncSubscriberAndLoadMaterials()
  }finally{
    loading.value = false
  }
}

async function syncSubscriberAndLoadMaterials(){
  if(!user.value?.sub) return
  syncInFlight.value = true
  try{
    const claims = idTokenClaims.value
    if(!claims?.__raw) throw new Error('Identity provider did not return a raw ID token')
    await syncExternalUser(claims.__raw)
    const subscriber = await apiCreateSubscriber({
      full_name: user.value.name || user.value.email || 'LabSchool user',
      email: user.value.email,
      phone: '',
    })
    enrollments.value = await getEnrollmentsBySubscriber(subscriber.id)
    if(activeEnrollment.value){
      const files = await listCourseFiles(courseId.value)
      materials.value = files.filter(file => file.resource_type !== 'public_resource')
    }
  }finally{
    syncInFlight.value = false
  }
}

async function login(){
  await loginWithRedirect({ appState: { target: route.fullPath } })
}

function courseDateLabel(value){
  const target = value?.scheduled_date
  if(!target) return 'Date to be confirmed'
  const date = new Date(`${target}T00:00:00`).toLocaleDateString()
  return value?.scheduled_time ? `${date} ${formatCourseTime(value.scheduled_time)}` : date
}

function formatCourseTime(value){
  if(!value) return ''
  return String(value).slice(0, 5)
}

function capacityLabel(value){
  const seats = Number(value?.max_students || 0)
  if(seats <= 0) return 'Open enrollment'
  const available = Number(value?.available_seats ?? seats)
  return `${available} of ${seats} seats available`
}

function todayKey(){
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function formatDate(value){
  if(!value) return '-'
  return new Date(value).toLocaleDateString()
}

function formatFileSize(bytes){
  const size = Number(bytes || 0)
  if(size < 1024) return `${size} B`
  if(size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

async function joinVirtualClass(){
  if(!activeEnrollment.value) return
  try{
    const access = await getVirtualAccess(activeEnrollment.value.id)
    window.open(access.zoom_url, '_blank', 'noopener,noreferrer')
  }catch(e){
    toast.error('Virtual access is not available yet')
  }
}

async function downloadMaterial(file){
  await downloadCourseFile(courseId.value, file)
}

async function downloadResource(file){
  await downloadCourseResource(courseId.value, file)
}
</script>
