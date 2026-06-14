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
          <li v-if="isAuthenticated" class="nav-item"><router-link class="nav-link" to="/my-courses">My courses</router-link></li>
          <li v-if="isAdmin" class="nav-item"><router-link class="nav-link" to="/admin/users">Users</router-link></li>
          <li v-if="isAdmin" class="nav-item"><router-link class="nav-link" to="/admin/courses">Course Admin</router-link></li>
        </ul>
        <div class="nav-session">
          <button v-if="!isAuthenticated" class="btn btn-outline-light btn-sm me-2" type="button" @click="login">
            Login
          </button>
          <div v-else class="nav-user">
            <button class="nav-user-trigger" type="button" @click="userMenuOpen = !userMenuOpen">
              <span class="nav-user-avatar">{{ userInitials }}</span>
              <span class="nav-user-name">{{ userLabel }}</span>
            </button>
            <div v-if="userMenuOpen" class="nav-user-menu">
              <router-link class="nav-user-menu-item" to="/my-courses" @click="userMenuOpen = false">My courses</router-link>
              <button class="nav-user-menu-item" type="button" @click="logoutUser">Logout</button>
            </div>
          </div>
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
const { isAuthenticated, loginWithRedirect, logout, user } = useAuth0()
const appUser = ref(readAppUser())
const userMenuOpen = ref(false)
const isAdmin = computed(() => Boolean(appUser.value?.is_admin))
const userLabel = computed(() => {
  const source = user.value?.name || user.value?.email || 'Account'
  return String(source).split('@')[0]
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
  userMenuOpen.value = false
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
.nav-session{
  display:flex;
  align-items:center;
  justify-content:flex-end;
}
.nav-user{
  position:relative;
}
.nav-user-trigger{
  display:flex;
  align-items:center;
  gap:8px;
  min-height:36px;
  padding:4px 8px 4px 4px;
  border:1px solid rgba(255,255,255,0.2);
  border-radius:8px;
  background:rgba(255,255,255,0.08);
  color:#fff;
}
.nav-user-trigger:hover{
  background:rgba(255,255,255,0.14);
}
.nav-user-avatar{
  display:inline-grid;
  place-items:center;
  width:28px;
  height:28px;
  border-radius:8px;
  color:#14213d;
  background:#fff;
  font-size:0.76rem;
  font-weight:800;
}
.nav-user-name{
  overflow:hidden;
  max-width:140px;
  text-overflow:ellipsis;
  white-space:nowrap;
  font-size:0.9rem;
  font-weight:700;
}
.nav-user-menu{
  position:absolute;
  right:0;
  top:calc(100% + 8px);
  z-index:20;
  min-width:170px;
  padding:6px;
  border:1px solid #d8e2ed;
  border-radius:8px;
  background:#fff;
  box-shadow:0 14px 30px rgba(15,23,42,0.16);
}
.nav-user-menu-item{
  display:block;
  width:100%;
  padding:8px 10px;
  border:0;
  border-radius:6px;
  background:transparent;
  color:#14213d;
  font-size:0.92rem;
  font-weight:700;
  text-align:left;
  text-decoration:none;
}
.nav-user-menu-item:hover{
  background:#f1f5f9;
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
  .nav-session{
    justify-content:flex-start;
    margin-top:8px;
  }
  .nav-user-menu{
    left:0;
    right:auto;
  }
}
</style>
