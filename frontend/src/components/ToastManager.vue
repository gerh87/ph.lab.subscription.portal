<template>
  <div aria-live="polite" aria-atomic="true" class="position-fixed top-0 end-0 p-3" style="z-index: 1080">
    <div v-for="t in toasts" :key="t.id" class="toast show mb-2 align-items-center text-white" :class="toastClass(t.variant)" role="alert" aria-live="assertive" aria-atomic="true">
      <div class="d-flex">
        <div class="toast-body">{{ t.message }}</div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" @click="remove(t.id)"></button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useToastStore } from '../stores/toast'

const store = useToastStore()
const toasts = computed(() => store.toasts)

function remove(id){ store.remove(id) }

function toastClass(variant){
  switch(variant){
    case 'success': return 'bg-success'
    case 'danger': return 'bg-danger'
    case 'warning': return 'bg-warning text-dark'
    case 'info': return 'bg-info text-dark'
    default: return 'bg-primary'
  }
}
</script>

<style scoped>
.toast { min-width: 220px }
</style>
