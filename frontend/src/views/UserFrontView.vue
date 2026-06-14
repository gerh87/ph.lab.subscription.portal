<template>
  <div class="user-front">
    <section class="front-hero" :style="{ backgroundImage: heroBackground }">
      <div class="front-hero-copy"></div>
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

      <div v-else class="course-browser">
        <div class="course-list-panel">
          <article
            v-for="course in availableCourses"
            :key="course.id"
            class="course-list-item"
            :class="{ active: focusedCourse?.id === course.id }"
            @click="focusCourse(course)"
          >
            <span class="course-list-main">
              <strong>{{ course.title }}</strong>
              <small>{{ courseDateLabel(course) }}</small>
            </span>
            <span class="course-list-side">
              <span class="status-badge" :class="courseCatalogStatusClass(course)">{{ courseCatalogStatusLabel(course) }}</span>
              <strong>{{ coursePriceLabel(course) }}</strong>
            </span>
            <span class="course-list-mobile-actions">
              <button class="btn btn-outline-secondary btn-sm" type="button" @click.stop="openCourseDetails(course)">
                Details
              </button>
              <button
                v-if="isEnrolled(course.id)"
                class="btn btn-primary btn-sm"
                type="button"
                @click.stop="$router.push(`/my-courses/${course.id}`)"
              >
                Open
              </button>
              <button
                v-else-if="pendingEnrollment(course.id)"
                class="btn btn-primary btn-sm"
                type="button"
                :disabled="pendingEnrollment(course.id).payment_method !== 'mercadopago'"
                @click.stop="resumeMercadoPago(course)"
              >
                {{ pendingPaymentLabel(course.id) }}
              </button>
              <button
                v-else
                class="btn btn-primary btn-sm"
                type="button"
                :disabled="isFull(course)"
                @click.stop="startSubscription(course)"
              >
                {{ isFull(course) ? 'Full' : 'Subscribe' }}
              </button>
            </span>
          </article>
        </div>

        <aside v-if="focusedCourse" class="course-focus-panel">
          <div class="course-focus-header">
            <div>
              <p class="eyebrow">Selected course</p>
              <h3>{{ focusedCourse.title }}</h3>
            </div>
            <span class="status-badge" :class="courseCatalogStatusClass(focusedCourse)">{{ courseCatalogStatusLabel(focusedCourse) }}</span>
          </div>
          <p>{{ courseSummary(focusedCourse) }}</p>
          <div class="course-focus-meta">
            <span>
              <small>Course fee</small>
              <strong>{{ coursePriceLabel(focusedCourse) }}</strong>
            </span>
            <span>
              <small>Schedule</small>
              <strong>{{ courseDateLabel(focusedCourse) }}</strong>
            </span>
            <span>
              <small>Seats</small>
              <strong>{{ capacityLabel(focusedCourse) }}</strong>
            </span>
          </div>
          <div class="course-focus-resources">
            <p class="eyebrow">Programs and guides</p>
            <div v-if="courseResources(focusedCourse.id).length === 0" class="empty-state compact">
              <strong>No public resources yet</strong>
              <span>Programs or guides will appear here when published.</span>
            </div>
            <div v-else class="course-file-list">
              <button
                v-for="file in courseResources(focusedCourse.id)"
                :key="file.id"
                class="course-file-row"
                type="button"
                @click="downloadResource(focusedCourse, file)"
              >
                <span>
                  <strong>{{ file.original_filename }}</strong>
                  <small>{{ file.content_type || 'File' }} · {{ formatFileSize(file.size_bytes) }}</small>
                </span>
              </button>
            </div>
          </div>
          <div class="front-course-actions course-focus-actions">
            <button class="btn btn-outline-secondary" type="button" @click="openCourseDetails(focusedCourse)">
              Details
            </button>
            <button
              v-if="isEnrolled(focusedCourse.id)"
              class="btn btn-primary"
              type="button"
              @click="$router.push(`/my-courses/${focusedCourse.id}`)"
            >
              Open course
            </button>
            <button
              v-if="canJoinVirtualClass(focusedCourse)"
              class="btn btn-success"
              type="button"
              @click="joinVirtualClass(focusedCourse)"
            >
              Join Zoom class
            </button>
            <button
              v-if="pendingEnrollment(focusedCourse.id)"
              class="btn btn-primary"
              type="button"
              :disabled="pendingEnrollment(focusedCourse.id).payment_method !== 'mercadopago'"
              @click="resumeMercadoPago(focusedCourse)"
            >
              {{ pendingPaymentLabel(focusedCourse.id) }}
            </button>
            <button
              v-else-if="!isEnrolled(focusedCourse.id)"
              class="btn btn-primary"
              type="button"
              :disabled="isFull(focusedCourse)"
              @click="startSubscription(focusedCourse)"
            >
              {{ isFull(focusedCourse) ? 'Full' : 'Subscribe' }}
            </button>
          </div>
        </aside>
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
              class="btn btn-primary"
              type="button"
              :disabled="pendingEnrollment(selectedCourse.id).payment_method !== 'mercadopago'"
              @click="resumeMercadoPago(selectedCourse)"
            >
              {{ pendingPaymentLabel(selectedCourse.id) }}
            </button>
            <button
              v-else-if="!isEnrolled(selectedCourse.id)"
              class="btn btn-primary"
              type="button"
              :disabled="isFull(selectedCourse)"
              @click="startSubscription(selectedCourse)"
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

    <div v-if="subscriptionCourse" class="modal fade show d-block management-modal" tabindex="-1">
      <div class="modal-dialog modal-md modal-dialog-centered">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <p class="eyebrow">Subscription</p>
              <h2 class="modal-title">{{ subscriptionCourse.title }}</h2>
            </div>
            <button type="button" class="btn-close" aria-label="Close" @click="closeSubscriptionOptions"></button>
          </div>
          <div class="modal-body">
            <div class="subscription-summary">
              <span>
                <small>Course fee</small>
                <strong>{{ coursePriceLabel(subscriptionCourse) }}</strong>
              </span>
              <span>
                <small>Schedule</small>
                <strong>{{ courseDateLabel(subscriptionCourse) }}</strong>
              </span>
            </div>
            <div class="payment-method-grid">
              <button class="payment-method-card primary" type="button" @click="choosePaymentMethod('mercadopago')">
                <strong>Mercado Pago</strong>
                <span>Pay online and get access when the payment is approved.</span>
              </button>
              <button class="payment-method-card" type="button" @click="choosePaymentMethod('manual')">
                <strong>Transfer payment</strong>
                <span>Send your transfer and wait for administrator approval.</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="subscriptionCourse" class="modal-backdrop fade show"></div>
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
const subscriptionCourse = ref(null)
const focusedCourseId = ref(null)
const loadingCatalog = ref(false)
const syncInFlight = ref(false)
const syncError = ref('')
const heroBackground = `linear-gradient(90deg, rgba(20,33,61,0.9) 0%, rgba(20,33,61,0.55) 34%, rgba(20,33,61,0.18) 100%), linear-gradient(rgba(238,242,246,0.22), rgba(238,242,246,0.22)), url(${headerMainUrl})`

const activeEnrollments = computed(() => enrollments.value.filter(enrollment => enrollment.status === 'active'))
const availableCourses = computed(() => courses.value
  .filter(course => !isPastCourse(course))
  .sort((a, b) => courseSortKey(a).localeCompare(courseSortKey(b)))
)
const focusedCourse = computed(() => {
  if(availableCourses.value.length === 0) return null
  return availableCourses.value.find(course => course.id === focusedCourseId.value) || availableCourses.value[0]
})
const profileStatus = computed(() => {
  if(syncError.value) return syncError.value
  if(appUser.value) return `App user #${appUser.value.id}`
  if(syncInFlight.value) return 'Preparing app user'
  return 'App user pending'
})

onMounted(async () => {
  loadingCatalog.value = true
  try{
    courses.value = await getCourses()
    focusDefaultCourse()
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

function focusCourse(course){
  focusedCourseId.value = course?.id || null
}

function focusDefaultCourse(){
  if(availableCourses.value.length === 0){
    focusedCourseId.value = null
    return
  }
  if(!availableCourses.value.find(course => course.id === focusedCourseId.value)){
    focusedCourseId.value = availableCourses.value[0].id
  }
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

function startSubscription(course){
  if(Number(course.price || 0) <= 0){
    subscribe(course, 'free')
    return
  }
  selectedCourse.value = null
  subscriptionCourse.value = course
}

function closeSubscriptionOptions(){
  subscriptionCourse.value = null
}

async function choosePaymentMethod(method){
  if(!subscriptionCourse.value) return
  const course = subscriptionCourse.value
  closeSubscriptionOptions()
  await subscribe(course, method)
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
    focusDefaultCourse()
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
    focusDefaultCourse()
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

function coursePriceLabel(course){
  const price = Number(course.price || 0)
  return price > 0 ? `$${formatPrice(price)}` : 'Free'
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

function courseSummary(course){
  const text = String(course.description || '').trim()
  if(!text) return 'A focused LabSchool course with guided practice and curated resources.'
  return text.length > 118 ? `${text.slice(0, 115).trim()}...` : text
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
