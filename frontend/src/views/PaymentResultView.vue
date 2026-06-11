<template>
  <div class="student-shell">
    <section class="payment-result-panel">
      <span class="status-badge" :class="resultClass">{{ resultLabel }}</span>
      <h1>{{ title }}</h1>
      <p>{{ message }}</p>
      <div class="payment-result-actions">
        <RouterLink class="btn btn-primary" to="/my-courses">My courses</RouterLink>
        <RouterLink class="btn btn-outline-secondary" to="/">Course catalog</RouterLink>
      </div>
    </section>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute } from 'vue-router'

const route = useRoute()
const status = computed(() => {
  if(route.path.includes('/failure')) return 'failure'
  if(route.path.includes('/pending')) return 'pending'
  return 'success'
})
const resultLabel = computed(() => {
  if(status.value === 'failure') return 'Payment failed'
  if(status.value === 'pending') return 'Payment pending'
  return 'Payment approved'
})
const resultClass = computed(() => {
  if(status.value === 'failure') return 'danger'
  if(status.value === 'pending') return 'today'
  return 'enrolled'
})
const title = computed(() => {
  if(status.value === 'failure') return 'We could not complete the payment'
  if(status.value === 'pending') return 'Your payment is pending'
  return 'Payment received'
})
const message = computed(() => {
  if(status.value === 'failure') return 'You can return to the catalog and try again when you are ready.'
  if(status.value === 'pending') return 'Mercado Pago is still processing the payment. Your course will update when confirmation arrives.'
  return 'Your subscription will be updated as soon as Mercado Pago confirms the transaction.'
})
</script>
