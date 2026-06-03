<template>
  <nav class="navbar navbar-expand-lg navbar-dark app-nav">
    <div class="container-fluid">
      <router-link class="navbar-brand brand-logo-link" to="/" aria-label="LabSchool home">
        <img class="brand-logo" :src="logoUrl" alt="" />
        <span class="brand-name">LabSchool</span>
      </router-link>
      <button class="navbar-toggler" type="button" @click="open = !open" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" :class="{show: open}">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item"><router-link class="nav-link" to="/">Courses</router-link></li>
          <li v-if="isAdmin" class="nav-item"><router-link class="nav-link" to="/admin/users">Users</router-link></li>
          <li v-if="isAdmin" class="nav-item"><router-link class="nav-link" to="/admin/courses">Course Admin</router-link></li>
        </ul>
        <div class="d-flex">
          <button v-if="!isAuthenticated" class="btn btn-outline-light btn-sm me-2" type="button" @click="login">
            Login
          </button>
          <button v-else class="btn btn-light btn-sm" type="button" @click="logoutUser">Logout</button>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useAuth0 } from '@auth0/auth0-vue'
import { useRoute } from 'vue-router'
import logoUrl from '../assets/logos/labschool_nav_mark.png'

const open = ref(false)
const route = useRoute()
const { isAuthenticated, loginWithRedirect, logout } = useAuth0()
const appUser = ref(readAppUser())
const isAdmin = computed(() => Boolean(appUser.value?.is_admin))

onMounted(() => {
  window.addEventListener('app-user-updated', refreshAppUser)
  window.addEventListener('storage', refreshAppUser)
})

onUnmounted(() => {
  window.removeEventListener('app-user-updated', refreshAppUser)
  window.removeEventListener('storage', refreshAppUser)
})

function login() {
  loginWithRedirect({
    appState: { target: route.fullPath },
  })
}

function logoutUser() {
  clearAuth0Cache()
  logout({
    logoutParams: {
      returnTo: window.location.origin,
    },
  })
}

function clearAuth0Cache(){
  localStorage.removeItem('app_user')
  localStorage.removeItem('idp_token')
  localStorage.removeItem('auth0_token')
  appUser.value = null
  for(const storage of [localStorage, sessionStorage]){
    Object.keys(storage)
      .filter(key => key.startsWith('@@auth0spajs@@') || key.includes('auth0'))
      .forEach(key => storage.removeItem(key))
  }
}

function refreshAppUser(event){
  appUser.value = event?.detail || readAppUser()
}

function readAppUser(){
  try{
    return JSON.parse(localStorage.getItem('app_user') || 'null')
  }catch(e){
    return null
  }
}
</script>

<style scoped>
.navbar-brand{font-weight:800}
.navbar{border-bottom:3px solid rgba(255,255,255,0.04)}
.brand-logo-link{
  display:flex;
  align-items:center;
  gap:8px;
  min-height:44px;
  padding:0 16px 0 0;
  color:#fff;
  text-decoration:none;
}
.brand-logo{
  display:block;
  width:34px;
  height:30px;
  object-fit:contain;
}
.brand-name{
  color:#fff;
  font-size:1.08rem;
  font-weight:800;
  letter-spacing:0;
}
@media(max-width:700px){
  .brand-logo-link{
    padding-right:8px;
  }
  .brand-logo{
    width:31px;
    height:27px;
  }
  .brand-name{
    font-size:1rem;
  }
}
</style>
