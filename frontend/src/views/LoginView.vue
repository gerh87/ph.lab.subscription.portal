<template>
  <div class="login">
    <h1 class="mb-4">Login</h1>
    <form @submit.prevent="onLogin" class="row g-3 w-50">
      <div class="col-12">
        <label class="form-label">Email</label>
        <input class="form-control" v-model="email" type="email" required />
      </div>
      <div class="col-12">
        <label class="form-label">Password</label>
        <input class="form-control" v-model="password" type="password" required />
      </div>
      <div class="col-12 d-flex gap-2">
        <button class="btn btn-primary" type="submit">Login</button>
        <button class="btn btn-outline-secondary" type="button" @click="onRegister">Register</button>
      </div>
    </form>
    <p v-if="error" class="text-danger mt-2">{{ error }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login, register } from '../services/api'

const email = ref('')
const password = ref('')
const error = ref('')
const router = useRouter()

async function onLogin() {
  error.value = ''
  try {
    const data = await login(email.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    router.push('/')
  } catch (err) {
    error.value = err?.response?.data?.detail || String(err)
  }
}

async function onRegister() {
  error.value = ''
  try {
    const data = await register(email.value, password.value)
    localStorage.setItem('access_token', data.access_token)
    router.push('/')
  } catch (err) {
    error.value = err?.response?.data?.detail || String(err)
  }
}
</script>
