<template>
  <div id="app-root">
    <NavBar />
    <ToastManager />
    <ConfirmDialog />
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import NavBar from './components/NavBar.vue'
import ToastManager from './components/ToastManager.vue'
import ConfirmDialog from './components/ConfirmDialog.vue'
</script>



<style>
html,body,#app{height:100%}
</style>
