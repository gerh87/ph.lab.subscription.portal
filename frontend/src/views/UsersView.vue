<template>
  <div class="admin-shell">
    <section class="admin-header">
      <div>
        <p class="eyebrow">Administration</p>
        <h1>Users</h1>
        <p class="admin-copy">Create, review, and update portal users from a single operational view.</p>
      </div>
      <button class="btn btn-outline-secondary" @click="load">Refresh</button>
    </section>

    <section class="status-grid admin-metrics">
      <div class="metric">
        <span class="metric-label">Total users</span>
        <strong>{{ users.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Administrators</span>
        <strong>{{ adminUsers.length }}</strong>
      </div>
      <div class="metric">
        <span class="metric-label">Latest ID</span>
        <strong>{{ latestUserId || '-' }}</strong>
      </div>
    </section>

    <section class="admin-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">New account</p>
          <h2>Create user</h2>
        </div>
      </div>
      <form @submit.prevent="create" class="admin-form">
        <label>
          <span>Email</span>
          <BaseInput v-model="newUser.email" placeholder="name@example.com" />
        </label>
        <label>
          <span>Full name</span>
          <BaseInput v-model="newUser.full_name" placeholder="Subscriber Admin" />
        </label>
        <label>
          <span>Password</span>
          <BaseInput v-model="newUser.password" placeholder="Password" type="password" />
        </label>
        <BaseButton class="submit-button" variant="primary" type="submit">Create</BaseButton>
      </form>
    </section>

    <section v-if="editing" class="admin-panel edit-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Editing</p>
          <h2>{{ editing.email }}</h2>
        </div>
      </div>
      <form @submit.prevent="save" class="admin-form edit-form">
        <label>
          <span>Email</span>
          <BaseInput v-model="editing.email" />
        </label>
        <label>
          <span>Full name</span>
          <BaseInput v-model="editing.full_name" />
        </label>
        <label class="toggle-field">
          <input type="checkbox" v-model="editing.is_admin" />
          <span>Administrator</span>
        </label>
        <div class="form-actions">
          <BaseButton variant="primary" type="submit">Save</BaseButton>
          <BaseButton variant="outline-secondary" @click="cancel">Cancel</BaseButton>
        </div>
      </form>
    </section>

    <section class="admin-panel table-panel">
      <div class="panel-heading">
        <div>
          <p class="eyebrow">Directory</p>
          <h2>User list</h2>
        </div>
      </div>

      <div v-if="users.length === 0" class="empty-state compact">
        <strong>No users found</strong>
        <span>Create the first user to start managing access.</span>
      </div>

      <div v-else class="table-responsive">
        <table class="admin-table">
          <thead>
            <tr>
              <th>User</th>
              <th>Role</th>
              <th>Created</th>
              <th class="actions-column">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td>
                <div class="user-cell">
                  <span class="user-avatar">{{ initials(u) }}</span>
                  <div>
                    <strong>{{ u.full_name || 'Unnamed user' }}</strong>
                    <span>{{ u.email }}</span>
                  </div>
                </div>
              </td>
              <td>
                <span class="role-badge" :class="{ admin: u.is_admin }">
                  {{ u.is_admin ? 'Admin' : 'User' }}
                </span>
              </td>
              <td>{{ formatDate(u.created_at) }}</td>
              <td>
                <div class="row-actions">
                  <BaseButton size="sm" variant="outline-secondary" @click="edit(u)">Edit</BaseButton>
                  <BaseButton size="sm" variant="outline-danger" @click="remove(u.id)">Delete</BaseButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed, ref, onMounted } from 'vue'
import { getUsers, createUser, updateUser, deleteUser } from '../services/api'
import { useToastStore } from '../stores/toast'
import { useConfirmStore } from '../stores/confirm'
import BaseInput from '../components/BaseInput.vue'
import BaseButton from '../components/BaseButton.vue'

function validEmail(email){
  return typeof email === 'string' && email.includes('@') && email.indexOf('@') > 0
}

const users = ref([])
const newUser = ref({ email: '', full_name: '', password: 'Test1234!' })
const editing = ref(null)
const toast = useToastStore()
const confirmStore = useConfirmStore()

const adminUsers = computed(() => users.value.filter(user => user.is_admin))
const latestUserId = computed(() => users.value.reduce((latest, user) => Math.max(latest, user.id || 0), 0))

async function load() {
  users.value = await getUsers()
}

async function create() {
  if (!validEmail(newUser.value.email)){
    toast.error('Please provide a valid email')
    return
  }
  try{
    await createUser(newUser.value)
    newUser.value = { email: '', full_name: '', password: 'Test1234!' }
    toast.success('User created')
    await load()
  } catch(e){
    toast.error('Failed to create user: '+(e?.response?.data?.detail||e))
  }
}

function edit(u) {
  editing.value = { ...u }
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

async function save() {
  if (!validEmail(editing.value.email)){
    toast.error('Please provide a valid email')
    return
  }
  try{
    await updateUser(editing.value.id, {
      email: editing.value.email,
      full_name: editing.value.full_name,
      is_admin: editing.value.is_admin,
    })
    editing.value = null
    toast.success('User updated')
    await load()
  } catch(e){
    toast.error('Failed to save user: '+(e?.response?.data?.detail||e))
  }
}

function cancel() {
  editing.value = null
}

async function remove(id) {
  const ok = await confirmStore.show('Delete user?')
  if(!ok) return
  await deleteUser(id)
  toast.success('User deleted')
  await load()
}

function initials(user){
  const source = user.full_name || user.email || 'User'
  return String(source)
    .split(/[ @.]/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0]?.toUpperCase())
    .join('')
}

function formatDate(value){
  if(!value) return '-'
  return new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(value))
}

onMounted(load)
</script>
