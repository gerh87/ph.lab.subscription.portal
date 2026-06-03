<template>
  <div class="user-front">
    <section class="front-hero" :style="{ backgroundImage: heroBackground }">
      <div class="front-hero-copy">
        <div class="front-hero-actions">
          <a class="btn btn-light" href="#courses">View courses</a>
          <button v-if="!isAuthenticated" class="btn btn-outline-light" type="button" @click="login">Register / Login</button>
          <a v-else class="btn btn-outline-light" href="#subscriber">My profile</a>
        </div>
      </div>
    </section>

    <section class="front-steps">
      <div>
        <span>1</span>
        <strong>Create your profile</strong>
      </div>
      <div>
        <span>2</span>
        <strong>Select a course</strong>
      </div>
      <div>
        <span>3</span>
        <strong>Confirm subscription</strong>
      </div>
    </section>

    <section id="subscriber" class="front-registration">
      <div>
        <p class="eyebrow">Subscriber</p>
        <h2>{{ isAuthenticated ? 'Your LabSchool profile' : 'Register as a subscriber' }}</h2>
        <p>
          {{ isAuthenticated ? 'Your account is ready to request course subscriptions.' : 'Create an account or log in before choosing a course.' }}
        </p>
      </div>
      <div v-if="!isAuthenticated" class="front-login-panel">
        <button class="btn btn-primary" type="button" @click="login">Create account / Login</button>
      </div>
      <div v-else class="front-profile-card">
        <span class="subscriber-avatar">{{ userInitials }}</span>
        <div>
          <strong>{{ user?.name || user?.email || 'LabSchool user' }}</strong>
          <span>{{ user?.email }}</span>
          <small :class="{ 'text-danger': syncError }">{{ profileStatus }}</small>
          <button v-if="syncError" class="btn btn-sm btn-outline-primary mt-2" type="button" @click="syncSubscriber(true)">
            Retry app sync
          </button>
        </div>
      </div>
    </section>

    <section id="courses" class="front-catalog">
      <div class="section-heading">
        <div>
          <p class="eyebrow">Course catalog</p>
          <h2>Available courses</h2>
        </div>
        <span class="catalog-count">{{ courses.length }} course{{ courses.length === 1 ? '' : 's' }}</span>
      </div>

      <div v-if="courses.length === 0" class="empty-state">
        <strong>No courses available</strong>
        <span>New courses will appear here as soon as they are published.</span>
      </div>

      <div v-else class="front-course-grid">
        <article v-for="course in courses" :key="course.id" class="front-course-card">
          <div class="front-course-media">
            <span>{{ courseInitials(course.title) }}</span>
          </div>
          <div class="front-course-content">
            <div class="front-course-title">
              <h3>{{ course.title }}</h3>
              <span v-if="isEnrolled(course.id)" class="status-badge enrolled">Subscribed</span>
            </div>
            <p>{{ course.description || 'Course details will be available soon.' }}</p>
            <div class="front-course-meta">
              <strong>${{ formatPrice(course.price) }}</strong>
              <span>{{ courseDateLabel(course) }}</span>
              <span>{{ capacityLabel(course) }}</span>
            </div>
            <div v-if="courseResources(course.id).length" class="course-card-resources">
              <strong>Program and guides</strong>
              <button
                v-for="file in courseResources(course.id)"
                :key="file.id"
                class="btn btn-sm btn-outline-secondary"
                type="button"
                @click="downloadResource(course, file)"
              >
                {{ file.original_filename }}
              </button>
            </div>
          </div>
          <div class="front-course-actions">
            <button
              v-if="isEnrolled(course.id)"
              class="btn btn-outline-secondary"
              type="button"
              @click="toggleCourseMaterials(course)"
            >
              Materials
            </button>
            <button
              v-if="canJoinVirtualClass(course)"
              class="btn btn-success"
              type="button"
              @click="joinVirtualClass(course)"
            >
              Join Zoom class
            </button>
            <button
              v-if="!isEnrolled(course.id)"
              class="btn btn-primary"
              type="button"
              :disabled="isFull(course)"
              @click="subscribe(course)"
            >
              {{ isFull(course) ? 'Full' : 'Subscribe' }}
            </button>
            <button
              v-else
              class="btn btn-outline-danger"
              type="button"
              @click="unsubscribe(isEnrolled(course.id).id)"
            >
              Cancel subscription
            </button>
          </div>
          <div v-if="openMaterialsCourseId === course.id" class="course-materials">
            <strong>Course materials</strong>
            <span v-if="materialsLoadingCourseId === course.id">Loading files</span>
            <span v-else-if="courseMaterials(course.id).length === 0">No files available yet</span>
            <button
              v-for="file in courseMaterials(course.id)"
              :key="file.id"
              class="btn btn-sm btn-outline-secondary"
              type="button"
              @click="downloadMaterial(course, file)"
            >
              {{ file.original_filename }}
            </button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth0 } from '@auth0/auth0-vue'
import { cancelEnrollment, createEnrollment, createSubscriber as apiCreateSubscriber, downloadCourseFile, downloadCourseResource, getCourses, getEnrollmentsBySubscriber, getVirtualAccess, listCourseFiles, listCourseResources, syncExternalUser } from '../services/api'
import { useToastStore } from '../stores/toast'
import headerMainUrl from '../assets/banners/header_main_clean.png'

const toast = useToastStore()
const { idTokenClaims, isAuthenticated, isLoading, loginWithRedirect, user } = useAuth0()
const courses = ref([])
const enrollments = ref([])
const appUser = ref(null)
const subscriberId = ref(null)
const courseFiles = ref({})
const coursePublicResources = ref({})
const openMaterialsCourseId = ref(null)
const materialsLoadingCourseId = ref(null)
const syncInFlight = ref(false)
const syncError = ref('')
const heroBackground = `linear-gradient(90deg, rgba(20,33,61,0.9) 0%, rgba(20,33,61,0.55) 34%, rgba(20,33,61,0.18) 100%), linear-gradient(rgba(238,242,246,0.22), rgba(238,242,246,0.22)), url(${headerMainUrl})`

const activeEnrollments = computed(() => enrollments.value.filter(enrollment => enrollment.status === 'active'))
const profileStatus = computed(() => {
  if(syncError.value) return syncError.value
  if(appUser.value) return `App user #${appUser.value.id}`
  if(syncInFlight.value) return 'Preparing app user'
  return 'App user pending'
})
const userInitials = computed(() => {
  const source = user.value?.name || user.value?.email || 'LS'
  return String(source)
    .split(/[ @.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('')
})

onMounted(async () => {
  courses.value = await getCourses()
  await loadCoursePublicResources()
  await syncSubscriber()
})

watch([isLoading, isAuthenticated, user, idTokenClaims], syncSubscriber, { immediate: true })

async function login(){
  await loginWithRedirect({
    appState: { target: window.location.pathname },
  })
}

async function syncSubscriber(force = false){
  if(isLoading.value) return
  if(!isAuthenticated.value || !user.value?.sub) return
  if(syncInFlight.value) return
  if(appUser.value && !force) return

  syncInFlight.value = true
  syncError.value = ''
  try{
    const claims = idTokenClaims.value
    if(!claims?.__raw){
      throw new Error('Identity provider did not return a raw ID token')
    }
    appUser.value = await syncExternalUser(claims.__raw)
  }catch(e){
    const detail = e?.error_description || e?.message || 'unknown error'
    syncError.value = `App user sync failed: ${detail}`
    console.error('Identity provider app user sync failed', e)
    return
  }finally{
    syncInFlight.value = false
  }

  try{
    const subscriber = await apiCreateSubscriber({
      full_name: user.value.name || user.value.email || 'LabSchool user',
      email: user.value.email,
      phone: '',
    })
    subscriberId.value = subscriber.id
    await loadEnrollments()
  }catch(e){ /* api service already reports the error */ }
}

async function loadEnrollments(){
  if(!subscriberId.value) return
  enrollments.value = await getEnrollmentsBySubscriber(subscriberId.value)
}

function isEnrolled(courseId){
  return enrollments.value.find(enrollment => enrollment.course_id === courseId && enrollment.status === 'active')
}

async function subscribe(course){
  if(!isAuthenticated.value){
    toast.error('Login or create an account first')
    await login()
    return
  }
  await syncSubscriber()
  if(!subscriberId.value){
    toast.error('We could not prepare your subscriber profile yet')
    return
  }

  try{
    await createEnrollment({ subscriber_id: Number(subscriberId.value), course_id: course.id })
    await loadEnrollments()
    courses.value = await getCourses()
    await loadCoursePublicResources()
    toast.success('Subscription request created. Payment will be confirmed manually.')
  }catch(e){ /* api service already reports the error */ }
}

async function unsubscribe(enrollmentId){
  try{
    await cancelEnrollment(enrollmentId)
    toast.success('Subscription cancelled')
    await loadEnrollments()
    courses.value = await getCourses()
    await loadCoursePublicResources()
    openMaterialsCourseId.value = null
  }catch(e){ /* api service already reports the error */ }
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

function capacityLabel(course){
  const seats = Number(course.max_students || 0)
  if(seats <= 0) return 'Open enrollment'
  const available = Number(course.available_seats ?? seats)
  return `${available} of ${seats} seats available`
}

function courseDateLabel(course){
  if(!course.scheduled_date) return 'Date to be confirmed'
  return new Date(`${course.scheduled_date}T00:00:00`).toLocaleDateString()
}

function todayKey(){
  const now = new Date()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const day = String(now.getDate()).padStart(2, '0')
  return `${now.getFullYear()}-${month}-${day}`
}

function canJoinVirtualClass(course){
  return Boolean(isEnrolled(course.id) && course.scheduled_date === todayKey())
}

async function joinVirtualClass(course){
  const enrollment = isEnrolled(course.id)
  if(!enrollment) return
  const access = await getVirtualAccess(enrollment.id)
  window.open(access.zoom_url, '_blank', 'noopener,noreferrer')
}

function courseMaterials(courseId){
  return courseFiles.value[courseId] || []
}

function courseResources(courseId){
  return coursePublicResources.value[courseId] || []
}

async function loadCoursePublicResources(){
  const entries = await Promise.all(
    courses.value.map(async course => [course.id, await listCourseResources(course.id)])
  )
  coursePublicResources.value = Object.fromEntries(entries)
}

async function toggleCourseMaterials(course){
  if(openMaterialsCourseId.value === course.id){
    openMaterialsCourseId.value = null
    return
  }
  openMaterialsCourseId.value = course.id
  if(courseFiles.value[course.id]) return
  materialsLoadingCourseId.value = course.id
  try{
    courseFiles.value = {
      ...courseFiles.value,
      [course.id]: await listCourseFiles(course.id),
    }
  }finally{
    materialsLoadingCourseId.value = null
  }
}

async function downloadMaterial(course, file){
  await downloadCourseFile(course.id, file)
}

async function downloadResource(course, file){
  await downloadCourseResource(course.id, file)
}

function isFull(course){
  return Number(course.max_students || 0) > 0 && Number(course.available_seats ?? course.max_students) <= 0
}
</script>
