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
        <span class="catalog-count">{{ availableCourses.length }} course{{ availableCourses.length === 1 ? '' : 's' }}</span>
      </div>

      <LoadingState
        v-if="loadingCatalog"
        title="Loading courses"
        message="Fetching the latest available courses."
      />

      <div v-else-if="availableCourses.length === 0" class="empty-state">
        <strong>No courses available</strong>
        <span>New courses will appear here as soon as they are published.</span>
      </div>

      <div v-else class="front-course-grid">
        <article v-for="course in availableCourses" :key="course.id" class="front-course-card">
          <div class="front-course-media">
            <div class="front-course-media-heading">
              <h3>{{ course.title }}</h3>
              <span class="status-badge" :class="courseCatalogStatusClass(course)">{{ courseCatalogStatusLabel(course) }}</span>
            </div>
          </div>
          <div class="front-course-content">
            <div class="front-course-meta">
              <strong>${{ formatPrice(course.price) }}</strong>
              <span>{{ courseDateLabel(course) }}</span>
            </div>
          </div>
          <div class="front-course-actions">
            <button
              class="btn btn-outline-secondary"
              type="button"
              @click="openCourseDetails(course)"
            >
              Details
            </button>
            <button
              v-if="isEnrolled(course.id)"
              class="btn btn-primary"
              type="button"
              @click="$router.push(`/my-courses/${course.id}`)"
            >
              Open course
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
              v-if="pendingEnrollment(course.id)"
              class="btn btn-outline-secondary"
              type="button"
              :disabled="pendingEnrollment(course.id).payment_method !== 'mercadopago'"
              @click="resumeMercadoPago(course)"
            >
              {{ pendingPaymentLabel(course.id) }}
            </button>
            <template v-else-if="!isEnrolled(course.id) && Number(course.price || 0) > 0">
              <button
                class="btn btn-primary"
                type="button"
                :disabled="isFull(course)"
                @click="subscribe(course, 'mercadopago')"
              >
                {{ isFull(course) ? 'Full' : 'Pay with Mercado Pago' }}
              </button>
              <button
                class="btn btn-outline-secondary"
                type="button"
                :disabled="isFull(course)"
                @click="subscribe(course, 'manual')"
              >
                Transfer payment
              </button>
            </template>
            <button
              v-else-if="!isEnrolled(course.id)"
              class="btn btn-primary"
              type="button"
              :disabled="isFull(course)"
              @click="subscribe(course, 'free')"
            >
              {{ isFull(course) ? 'Full' : 'Subscribe' }}
            </button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="selectedCourse" class="modal fade show d-block management-modal" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <p class="eyebrow">Course detail</p>
              <h2 class="modal-title">{{ selectedCourse.title }}</h2>
            </div>
            <button type="button" class="btn-close" aria-label="Close" @click="closeCourseDetails"></button>
          </div>
          <div class="modal-body">
            <section class="course-detail-modal-grid">
              <div class="detail-panel compact-detail-panel">
                <p class="eyebrow">Overview</p>
                <p>{{ selectedCourse.description || 'Course details will be available soon.' }}</p>
                <div class="course-detail-facts">
                  <span>${{ formatPrice(selectedCourse.price) }}</span>
                  <span>{{ courseDateLabel(selectedCourse) }}</span>
                  <span>{{ capacityLabel(selectedCourse) }}</span>
                </div>
              </div>

              <div class="detail-panel compact-detail-panel">
                <p class="eyebrow">Programs and guides</p>
                <div v-if="courseResources(selectedCourse.id).length === 0" class="empty-state compact">
                  <strong>No public resources yet</strong>
                  <span>Programs or guides will appear here when published.</span>
                </div>
                <div v-else class="course-file-list">
                  <button
                    v-for="file in courseResources(selectedCourse.id)"
                    :key="file.id"
                    class="course-file-row"
                    type="button"
                    @click="downloadResource(selectedCourse, file)"
                  >
                    <span>
                      <strong>{{ file.original_filename }}</strong>
                      <small>{{ file.content_type || 'File' }} · {{ formatFileSize(file.size_bytes) }}</small>
                    </span>
                  </button>
                </div>
              </div>
            </section>
          </div>
          <div class="modal-footer course-detail-modal-actions">
            <button
              v-if="isEnrolled(selectedCourse.id)"
              class="btn btn-outline-danger"
              type="button"
              @click="unsubscribe(isEnrolled(selectedCourse.id).id)"
            >
              Cancel subscription
            </button>
            <button
              v-if="canJoinVirtualClass(selectedCourse)"
              class="btn btn-success"
              type="button"
              @click="joinVirtualClass(selectedCourse)"
            >
              Join Zoom class
            </button>
            <button
              v-if="pendingEnrollment(selectedCourse.id)"
              class="btn btn-outline-secondary"
              type="button"
              :disabled="pendingEnrollment(selectedCourse.id).payment_method !== 'mercadopago'"
              @click="resumeMercadoPago(selectedCourse)"
            >
              {{ pendingPaymentLabel(selectedCourse.id) }}
            </button>
            <template v-else-if="!isEnrolled(selectedCourse.id) && Number(selectedCourse.price || 0) > 0">
              <button
                class="btn btn-primary"
                type="button"
                :disabled="isFull(selectedCourse)"
                @click="subscribe(selectedCourse, 'mercadopago')"
              >
                {{ isFull(selectedCourse) ? 'Full' : 'Pay with Mercado Pago' }}
              </button>
              <button
                class="btn btn-outline-secondary"
                type="button"
                :disabled="isFull(selectedCourse)"
                @click="subscribe(selectedCourse, 'manual')"
              >
                Transfer payment
              </button>
            </template>
            <button
              v-else-if="!isEnrolled(selectedCourse.id)"
              class="btn btn-primary"
              type="button"
              :disabled="isFull(selectedCourse)"
              @click="subscribe(selectedCourse, 'free')"
            >
              {{ isFull(selectedCourse) ? 'Full' : 'Subscribe' }}
            </button>
            <button
              v-else
              class="btn btn-primary"
              type="button"
              @click="$router.push(`/my-courses/${selectedCourse.id}`)"
            >
              Open course
            </button>
          </div>
        </div>
      </div>
    </div>
    <div v-if="selectedCourse" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useAuth0 } from '@auth0/auth0-vue'
import { cancelEnrollment, createEnrollment, createPreference, createSubscriber as apiCreateSubscriber, downloadCourseResource, getCourses, getEnrollmentsBySubscriber, getVirtualAccess, listCourseResources, syncExternalUser } from '../services/api'
import { useToastStore } from '../stores/toast'
import LoadingState from '../components/LoadingState.vue'
import headerMainUrl from '../assets/banners/header_main_clean.png'

const toast = useToastStore()
const { idTokenClaims, isAuthenticated, isLoading, loginWithRedirect, user } = useAuth0()
const courses = ref([])
const enrollments = ref([])
const appUser = ref(null)
const subscriberId = ref(null)
const coursePublicResources = ref({})
const selectedCourse = ref(null)
const loadingCatalog = ref(false)
const syncInFlight = ref(false)
const syncError = ref('')
const heroBackground = `linear-gradient(90deg, rgba(20,33,61,0.9) 0%, rgba(20,33,61,0.55) 34%, rgba(20,33,61,0.18) 100%), linear-gradient(rgba(238,242,246,0.22), rgba(238,242,246,0.22)), url(${headerMainUrl})`

const activeEnrollments = computed(() => enrollments.value.filter(enrollment => enrollment.status === 'active'))
const availableCourses = computed(() => courses.value
  .filter(course => !isPastCourse(course))
  .sort((a, b) => courseSortKey(a).localeCompare(courseSortKey(b)))
)
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
  loadingCatalog.value = true
  try{
    courses.value = await getCourses()
    await loadCoursePublicResources()
    await syncSubscriber()
  }finally{
    loadingCatalog.value = false
  }
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

function pendingEnrollment(courseId){
  return enrollments.value.find(enrollment => enrollment.course_id === courseId && enrollment.status === 'pending_payment')
}

function pendingPaymentLabel(courseId){
  const enrollment = pendingEnrollment(courseId)
  if(!enrollment) return 'Payment pending'
  if(enrollment.payment_method === 'mercadopago') return 'Resume payment'
  return 'Transfer pending approval'
}

async function subscribe(course, paymentMethod = 'manual'){
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
    const method = Number(course.price || 0) > 0 ? paymentMethod : 'free'
    const enrollment = await createEnrollment({
      subscriber_id: Number(subscriberId.value),
      course_id: course.id,
      payment_method: method === 'free' ? null : method,
    })
    await loadEnrollments()
    courses.value = await getCourses()
    await loadCoursePublicResources()
    if(Number(course.price || 0) > 0 && method === 'mercadopago'){
      const preference = await createPreference({ enrollment_id: enrollment.id })
      if(preference?.init_point){
        toast.success('Redirecting to payment')
        window.location.href = preference.init_point
        return
      }
    } else if(Number(course.price || 0) > 0 && method === 'manual') {
      toast.success('Transfer request created. An administrator will confirm your payment.')
      return
    } else {
      await createPreference({ enrollment_id: enrollment.id })
      await loadEnrollments()
    }
    toast.success('Subscription confirmed')
  }catch(e){ /* api service already reports the error */ }
}

async function resumeMercadoPago(course){
  const enrollment = pendingEnrollment(course.id)
  if(!enrollment || enrollment.payment_method !== 'mercadopago') return
  try{
    const preference = await createPreference({ enrollment_id: enrollment.id })
    if(preference?.init_point){
      toast.success('Redirecting to payment')
      window.location.href = preference.init_point
    }
  }catch(e){ /* api service already reports the error */ }
}

async function unsubscribe(enrollmentId){
  try{
    await cancelEnrollment(enrollmentId)
    toast.success('Subscription cancelled')
    await loadEnrollments()
    courses.value = await getCourses()
    await loadCoursePublicResources()
    if(selectedCourse.value){
      selectedCourse.value = courses.value.find(course => course.id === selectedCourse.value.id) || null
    }
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
  const date = new Date(`${course.scheduled_date}T00:00:00`).toLocaleDateString()
  return course.scheduled_time ? `${date} ${formatCourseTime(course.scheduled_time)}` : date
}

function formatCourseTime(value){
  if(!value) return ''
  return String(value).slice(0, 5)
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

function courseResources(courseId){
  return coursePublicResources.value[courseId] || []
}

function openCourseDetails(course){
  selectedCourse.value = course
}

function closeCourseDetails(){
  selectedCourse.value = null
}

async function loadCoursePublicResources(){
  const entries = await Promise.all(
    availableCourses.value.map(async course => [course.id, await listCourseResources(course.id)])
  )
  coursePublicResources.value = Object.fromEntries(entries)
}

async function downloadResource(course, file){
  await downloadCourseResource(course.id, file)
}

function isFull(course){
  return Number(course.max_students || 0) > 0 && Number(course.available_seats ?? course.max_students) <= 0
}

function courseCatalogStatusLabel(course){
  if(isEnrolled(course.id)) return 'Subscribed'
  if(pendingEnrollment(course.id)) return 'Payment pending'
  if(isFull(course)) return 'Full'
  if(!course.scheduled_date) return 'No date yet'
  if(course.scheduled_date === todayKey()) return 'Today'
  return 'Upcoming'
}

function courseCatalogStatusClass(course){
  if(isEnrolled(course.id)) return 'enrolled'
  if(pendingEnrollment(course.id)) return 'neutral'
  if(isFull(course)) return 'danger'
  if(!course.scheduled_date) return 'neutral'
  if(course.scheduled_date === todayKey()) return 'today'
  return 'upcoming'
}

function courseSortKey(course){
  return course.scheduled_date || '9999-12-31'
}

function formatFileSize(bytes){
  const size = Number(bytes || 0)
  if(size < 1024) return `${size} B`
  if(size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

function isPastCourse(course){
  return Boolean(course.scheduled_date && course.scheduled_date < todayKey())
}
</script>
