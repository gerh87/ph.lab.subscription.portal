<template>
  <div class="admin-shell">
    <section class="admin-header course-admin-header">
      <div>
        <p class="eyebrow">Academic operations</p>
        <h1>Course Admin</h1>
        <p class="admin-copy">Manage course setup, available seats, and active subscribers.</p>
      </div>
      <div class="header-actions">
        <BaseButton variant="primary" @click="openCreateModal">New course</BaseButton>
        <button class="btn btn-outline-secondary" @click="load">Refresh</button>
      </div>
    </section>

    <section class="status-grid admin-metrics">
      <div class="metric">
        <span class="metric-label">Published courses</span>
        <strong>{{ courses.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Active subscriptions</span>
        <strong>{{ activeEnrollmentCount }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Available seats</span>
        <strong>{{ availableSeatsLabel }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Course capacity</span>
        <strong>{{ totalCapacityLabel }}</strong>
      </div>
    </section>

    <section class="admin-panel table-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Catalog</p>
          <h2>Managed courses</h2>
        </div>
      </div>

      <div v-if="courses.length === 0" class="empty-state compact">
        <strong>No courses found</strong>
        <span>Create the first course to make it available in the subscriber catalog.</span>
      </div>

      <div v-else class="table-responsive">
        <table class="admin-table">
          <thead>
            <tr>
              <th>Course</th>
              <th>Date</th>
              <th>Virtual</th>
              <th>Price</th>
              <th>Seats</th>
              <th>Subscribers</th>
              <th>Status</th>
              <th class="actions-column">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in courses" :key="c.id">
              <td>
                <strong class="course-name">{{ c.title }}</strong>
              </td>
              <td>{{ formatCourseDate(c.scheduled_date) }}</td>
              <td>
                <span class="role-badge" :class="{ admin: Boolean(c.zoom_url) }">
                  {{ c.zoom_url ? 'Ready' : 'Missing' }}
                </span>
              </td>
              <td>
                <strong class="price-text">${{ formatPrice(c.price) }}</strong>
              </td>
              <td>{{ capacityLabel(c) }}</td>
              <td>{{ activeEnrollmentCountFor(c.id) }}</td>
              <td>
                <span class="role-badge" :class="{ admin: Number(c.price || 0) > 0 }">
                  {{ Number(c.price || 0) > 0 ? 'Paid' : 'Free' }}
                </span>
              </td>
              <td>
                <div class="row-actions">
                  <BaseButton size="sm" variant="outline-secondary" @click="selectCourse(c)">Subscribers</BaseButton>
                  <BaseButton size="sm" variant="outline-secondary" @click="startEdit(c)">Edit</BaseButton>
                  <BaseButton size="sm" variant="outline-danger" @click="del(c.id)">Delete</BaseButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="selectedCourse" class="admin-panel table-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Course subscribers</p>
          <h2>{{ selectedCourse.title }}</h2>
        </div>
        <BaseButton variant="outline-secondary" @click="selectedCourseId = null">Close</BaseButton>
      </div>

      <section class="status-grid admin-metrics detail-metrics">
        <div class="metric">
          <span class="metric-label">Active subscribers</span>
          <strong>{{ activeEnrollmentCountFor(selectedCourse.id) }}</strong>
        </div>
        <div class="metric">
          <span class="metric-label">Seats</span>
          <strong>{{ capacityLabel(selectedCourse) }}</strong>
        </div>
      </section>

      <section class="course-files-panel">
        <div class="panel-heading compact-heading">
          <div>
            <p class="eyebrow">Public resources</p>
            <h3>Programs and guides</h3>
          </div>
          <label class="file-upload-control compact-upload">
            <input type="file" @change="uploadFileForSelectedCourse" />
            <span>Upload file</span>
          </label>
        </div>

        <div v-if="selectedCourseFiles.length === 0" class="empty-state compact">
          <strong>No files uploaded</strong>
          <span>Attach programs, brochures, guides, or public course information.</span>
        </div>

        <div v-else class="table-responsive">
          <table class="admin-table files-table">
            <thead>
              <tr>
                <th>File</th>
                <th>Type</th>
                <th>Size</th>
                <th>Uploaded</th>
                <th class="actions-column">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="file in selectedCourseFiles" :key="file.id">
                <td>
                  <strong class="course-name">{{ file.original_filename }}</strong>
                  <span class="file-guid">{{ file.guid }}</span>
                </td>
                <td>{{ file.content_type || '-' }}</td>
                <td>{{ formatFileSize(file.size_bytes) }}</td>
                <td>{{ formatDate(file.created_at) }}</td>
                <td>
                  <div class="row-actions">
                    <BaseButton size="sm" variant="outline-secondary" @click="downloadCourseMaterial(file)">Download</BaseButton>
                    <BaseButton size="sm" variant="outline-danger" @click="deleteCourseMaterial(file)">Delete</BaseButton>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <div v-if="selectedCourseEnrollments.length === 0" class="empty-state compact">
        <strong>No subscribers yet</strong>
        <span>This course has no subscription requests.</span>
      </div>

      <div v-else class="table-responsive">
        <table class="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Status</th>
              <th>Payment</th>
              <th>Requested</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="enrollment in selectedCourseEnrollments" :key="enrollment.id">
              <td>
                <div class="subscriber-list-cell">
                  <strong>{{ subscriberFor(enrollment)?.full_name || 'Unknown subscriber' }}</strong>
                  <span>{{ subscriberFor(enrollment)?.email || `Subscriber #${enrollment.subscriber_id}` }}</span>
                </div>
              </td>
              <td>
                <span class="role-badge" :class="{ admin: enrollment.status === 'active' }">{{ enrollment.status }}</span>
              </td>
              <td>{{ enrollment.payment_status }}</td>
              <td>{{ formatDate(enrollment.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <div v-if="createModalOpen" class="modal fade show d-block management-modal" tabindex="-1">
      <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <p class="eyebrow">New course</p>
              <h2 class="modal-title">Create course wizard</h2>
            </div>
            <button type="button" class="btn-close" aria-label="Close" @click="closeCreateModal"></button>
          </div>
          <div class="modal-body">
            <div class="course-wizard">
              <div class="wizard-steps" aria-label="Course creation progress">
                <button
                  v-for="step in wizardSteps"
                  :key="step.id"
                  type="button"
                  class="wizard-step"
                  :class="{ active: createStep === step.id, complete: createStep > step.id }"
                  @click="goToStep(step.id)"
                >
                  <span>{{ step.id }}</span>
                  <strong>{{ step.label }}</strong>
                </button>
              </div>

              <form @submit.prevent="createCourse" class="wizard-body">
                <section v-if="createStep === 1" class="wizard-pane">
                  <div class="wizard-grid two-columns">
                    <label>
                      <span>Title</span>
                      <BaseInput v-model="form.title" placeholder="Intro to SaaS" />
                    </label>
                    <label>
                      <span>Description</span>
                      <textarea v-model="form.description" class="form-control" rows="4" placeholder="What subscribers will learn"></textarea>
                    </label>
                  </div>
                </section>

                <section v-else-if="createStep === 2" class="wizard-pane">
                  <div class="wizard-grid">
                    <label>
                      <span>Course date</span>
                      <BaseInput v-model="form.scheduled_date" type="date" />
                    </label>
                    <label>
                      <span>Price</span>
                      <BaseInput v-model.number="form.price" type="number" placeholder="0.00" />
                    </label>
                    <label>
                      <span>Seats</span>
                      <BaseInput v-model.number="form.max_students" type="number" placeholder="0" />
                    </label>
                    <label class="wide-field">
                      <span>Zoom link</span>
                      <BaseInput v-model="form.zoom_url" type="url" placeholder="https://zoom.us/j/..." />
                    </label>
                  </div>
                </section>

                <section v-else class="wizard-pane">
                  <div class="file-uploader">
                    <label class="file-drop-control">
                      <input type="file" multiple @change="queueCourseFiles" />
                      <span class="file-drop-title">Attach public resources</span>
                      <span class="file-drop-copy">Programs, brochures, guides, and public course information.</span>
                    </label>

                    <div v-if="pendingCourseFiles.length === 0" class="empty-state compact">
                      <strong>No files selected</strong>
                      <span>You can create the course now and attach resources later.</span>
                    </div>

                    <div v-else class="queued-files">
                      <div v-for="(file, index) in pendingCourseFiles" :key="`${file.name}-${file.size}-${index}`" class="queued-file">
                        <div>
                          <strong>{{ file.name }}</strong>
                          <span>{{ file.type || 'Unknown type' }} · {{ formatFileSize(file.size) }}</span>
                        </div>
                        <BaseButton size="sm" variant="outline-danger" @click="removeQueuedFile(index)">Remove</BaseButton>
                      </div>
                    </div>
                  </div>
                </section>

                <div class="wizard-actions">
                  <BaseButton v-if="createStep > 1" variant="outline-secondary" @click="createStep -= 1">Back</BaseButton>
                  <BaseButton v-if="createStep < wizardSteps.length" variant="primary" @click="nextCreateStep">Next</BaseButton>
                  <BaseButton v-else class="submit-button" variant="primary" type="submit" :disabled="creatingCourse">
                    {{ creatingCourse ? 'Creating...' : 'Create course' }}
                  </BaseButton>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div v-if="createModalOpen" class="modal-backdrop fade show"></div>

    <div v-if="editing" class="modal fade show d-block management-modal" tabindex="-1">
      <div class="modal-dialog modal-lg modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content">
          <div class="modal-header">
            <div>
              <p class="eyebrow">Editing</p>
              <h2 class="modal-title">{{ editing.title }}</h2>
            </div>
            <button type="button" class="btn-close" aria-label="Close" @click="cancelEdit"></button>
          </div>
          <form @submit.prevent="saveEdit">
            <div class="modal-body">
              <div class="edit-modal-form">
                <label>
                  <span>Title</span>
                  <BaseInput v-model="editing.title" />
                </label>
                <label>
                  <span>Description</span>
                  <textarea v-model="editing.description" class="form-control" rows="4"></textarea>
                </label>
                <label>
                  <span>Course date</span>
                  <BaseInput v-model="editing.scheduled_date" type="date" />
                </label>
                <label>
                  <span>Price</span>
                  <BaseInput v-model.number="editing.price" type="number" />
                </label>
                <label>
                  <span>Seats</span>
                  <BaseInput v-model.number="editing.max_students" type="number" />
                </label>
                <label class="wide-field">
                  <span>Zoom link</span>
                  <BaseInput v-model="editing.zoom_url" type="url" placeholder="https://zoom.us/j/..." />
                </label>
              </div>
            </div>
            <div class="modal-footer">
              <BaseButton variant="outline-secondary" @click="cancelEdit">Cancel</BaseButton>
              <BaseButton variant="primary" type="submit">Save</BaseButton>
            </div>
          </form>
        </div>
      </div>
    </div>
    <div v-if="editing" class="modal-backdrop fade show"></div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { deleteCourseFile, downloadCourseFile, getAdminCourses, createCourse as apiCreate, updateCourse, deleteCourse, listCourseFiles, listEnrollments, listSubscribers, uploadCourseFile } from '../services/api'
import { useToastStore } from '../stores/toast'
import { useConfirmStore } from '../stores/confirm'
import BaseInput from '../components/BaseInput.vue'
import BaseButton from '../components/BaseButton.vue'

function validCourse(payload){
  if(!payload.title || String(payload.title).trim().length === 0) return 'Title is required'
  if(payload.price == null || isNaN(payload.price)) return 'Price must be a number'
  if(Number(payload.price) < 0) return 'Price must be zero or positive'
  if(payload.max_students == null || isNaN(payload.max_students)) return 'Seats must be a number'
  if(Number(payload.max_students) < 0) return 'Seats must be zero or positive'
  return null
}

const courses = ref([])
const enrollments = ref([])
const subscribers = ref([])
const courseFiles = ref({})
const form = ref({ title: '', description: '', scheduled_date: '', zoom_url: '', price: 0, max_students: 0 })
const createModalOpen = ref(false)
const createStep = ref(1)
const creatingCourse = ref(false)
const pendingCourseFiles = ref([])
const editing = ref(null)
const selectedCourseId = ref(null)
const toast = useToastStore()
const confirmStore = useConfirmStore()
const wizardSteps = [
  { id: 1, label: 'Content' },
  { id: 2, label: 'Schedule' },
  { id: 3, label: 'Files' },
]

const totalCapacityLabel = computed(() => {
  const capacities = courses.value.map(course => Number(course.max_students || 0)).filter(Boolean)
  if(capacities.length === 0) return 'Open'
  return String(capacities.reduce((sum, value) => sum + value, 0))
})

const availableSeatsLabel = computed(() => {
  const limitedCourses = courses.value.filter(course => Number(course.max_students || 0) > 0)
  if(limitedCourses.length === 0) return 'Open'
  return String(limitedCourses.reduce((sum, course) => sum + Number(course.available_seats ?? course.max_students ?? 0), 0))
})

const activeEnrollmentCount = computed(() => enrollments.value.filter(enrollment => enrollment.status === 'active').length)
const selectedCourse = computed(() => courses.value.find(course => course.id === selectedCourseId.value))
const selectedCourseFiles = computed(() => selectedCourseId.value ? (courseFiles.value[selectedCourseId.value] || []) : [])
const selectedCourseEnrollments = computed(() => {
  if(!selectedCourse.value) return []
  return enrollments.value.filter(enrollment => enrollment.course_id === selectedCourse.value.id && enrollment.status === 'active')
})

async function load() {
  const [courseList, enrollmentList, subscriberList] = await Promise.all([
    getAdminCourses(),
    listEnrollments(),
    listSubscribers(),
  ])
  courses.value = courseList
  enrollments.value = enrollmentList
  subscribers.value = subscriberList
  if(selectedCourseId.value && !courses.value.find(course => course.id === selectedCourseId.value)){
    selectedCourseId.value = null
  }
}

async function createCourse() {
  const err = validCourse(form.value)
  if(err){ toast.error(err); return }
  creatingCourse.value = true
  let created = null
  try{
    created = await apiCreate(form.value)
  } catch(e){
    toast.error('Failed to create course: '+(e?.response?.data?.detail||e))
    creatingCourse.value = false
    return
  }

  const filesToUpload = [...pendingCourseFiles.value]
  const failedUploads = []
  for(const file of filesToUpload){
    try{
      await uploadCourseFile(created.id, file)
    } catch(e){
      failedUploads.push(file)
    }
  }

  try{
    await load()
    selectedCourseId.value = created.id
    await loadCourseFiles(created.id)
    if(failedUploads.length){
      pendingCourseFiles.value = failedUploads
      createStep.value = 3
      toast.error('Course created, but some files failed to upload')
    } else {
      resetCreateWizard()
      createModalOpen.value = false
      toast.success(filesToUpload.length ? 'Course created with files' : 'Course created')
    }
  } finally {
    creatingCourse.value = false
  }
}

function resetCreateWizard(){
  form.value = { title: '', description: '', scheduled_date: '', zoom_url: '', price: 0, max_students: 0 }
  pendingCourseFiles.value = []
  createStep.value = 1
}

function openCreateModal(){
  resetCreateWizard()
  createModalOpen.value = true
}

function closeCreateModal(){
  if(creatingCourse.value) return
  createModalOpen.value = false
  resetCreateWizard()
}

function goToStep(step){
  if(step === createStep.value) return
  if(step > createStep.value + 1) return
  if(step > createStep.value && !canLeaveCreateStep()) return
  createStep.value = step
}

function nextCreateStep(){
  if(!canLeaveCreateStep()) return
  createStep.value = Math.min(createStep.value + 1, wizardSteps.length)
}

function canLeaveCreateStep(){
  if(createStep.value === 1 && (!form.value.title || String(form.value.title).trim().length === 0)){
    toast.error('Title is required')
    return false
  }
  if(createStep.value === 2){
    const err = validCourse(form.value)
    if(err){ toast.error(err); return false }
  }
  return true
}

function queueCourseFiles(event){
  const files = Array.from(event.target.files || [])
  event.target.value = ''
  if(files.length === 0) return
  pendingCourseFiles.value = [...pendingCourseFiles.value, ...files]
}

function removeQueuedFile(index){
  pendingCourseFiles.value = pendingCourseFiles.value.filter((_, fileIndex) => fileIndex !== index)
}

function startEdit(c) {
  editing.value = { ...c }
}

async function saveEdit() {
  const err = validCourse(editing.value)
  if(err){ toast.error(err); return }
  try{
    await updateCourse(editing.value.id, editing.value)
    editing.value = null
    toast.success('Course updated')
    await load()
  } catch(e){
    toast.error('Failed to save course: '+(e?.response?.data?.detail||e))
  }
}

function cancelEdit() {
  editing.value = null
}

async function del(id) {
  const ok = await confirmStore.show('Delete course?')
  if(!ok) return
  await deleteCourse(id)
  if(selectedCourseId.value === id) selectedCourseId.value = null
  toast.success('Course deleted')
  await load()
}

function selectCourse(course){
  selectedCourseId.value = course.id
  loadCourseFiles(course.id)
}

async function loadCourseFiles(courseId){
  courseFiles.value = {
    ...courseFiles.value,
    [courseId]: await listCourseFiles(courseId),
  }
}

async function uploadFileForSelectedCourse(event){
  const file = event.target.files?.[0]
  event.target.value = ''
  if(!file || !selectedCourseId.value) return
  try{
    await uploadCourseFile(selectedCourseId.value, file)
    toast.success('Course file uploaded')
    await loadCourseFiles(selectedCourseId.value)
  } catch(e){
    toast.error('Failed to upload file: '+(e?.response?.data?.detail||e))
  }
}

async function downloadCourseMaterial(file){
  if(!selectedCourseId.value) return
  await downloadCourseFile(selectedCourseId.value, file)
}

async function deleteCourseMaterial(file){
  if(!selectedCourseId.value) return
  const ok = await confirmStore.show('Delete file?')
  if(!ok) return
  await deleteCourseFile(selectedCourseId.value, file.id)
  toast.success('Course file deleted')
  await loadCourseFiles(selectedCourseId.value)
}

function formatPrice(price){
  return Number(price || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
}

function capacityLabel(course){
  const seats = Number(course.max_students || 0)
  if(seats <= 0) return 'Open'
  const available = Number(course.available_seats ?? seats)
  return `${available} of ${seats}`
}

function activeEnrollmentCountFor(courseId){
  return enrollments.value.filter(enrollment => enrollment.course_id === courseId && enrollment.status === 'active').length
}

function subscriberFor(enrollment){
  return subscribers.value.find(subscriber => subscriber.id === enrollment.subscriber_id)
}

function formatDate(value){
  if(!value) return '-'
  return new Date(value).toLocaleDateString()
}

function formatCourseDate(value){
  if(!value) return 'Unscheduled'
  return new Date(`${value}T00:00:00`).toLocaleDateString()
}

function formatFileSize(bytes){
  const size = Number(bytes || 0)
  if(size < 1024) return `${size} B`
  if(size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`
  return `${(size / (1024 * 1024)).toFixed(1)} MB`
}

onMounted(load)
</script>
