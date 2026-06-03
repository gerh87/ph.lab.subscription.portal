<template>
  <div :class="['card', classes]">
    <div v-if="$slots.header" class="card-header bg-transparent border-0 px-3 py-2">
      <slot name="header" />
    </div>
    <div class="card-body px-3 py-2">
      <slot />
    </div>
    <div v-if="$slots.footer" class="card-footer bg-transparent border-0 px-3 py-2">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ classes: { type: String, default: '' } })
</script>

<style scoped>
.card{border-radius:8px}
</style>
