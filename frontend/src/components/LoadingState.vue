<template>
  <div class="loading-state" :class="{ compact }" role="status" aria-live="polite">
    <span class="loading-spinner" aria-hidden="true"></span>
    <div>
      <strong>{{ title }}</strong>
      <span>{{ message }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: 'Loading' },
  message: { type: String, default: 'Preparing the latest information.' },
  compact: { type: Boolean, default: false },
})
</script>
