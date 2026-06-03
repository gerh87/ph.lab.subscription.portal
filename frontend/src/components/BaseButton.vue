<template>
  <button
    :type="type"
    :class="btnClass"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>

<script setup>
import { computed } from 'vue'
defineEmits(['click'])
const props = defineProps({
  variant: { type: String, default: 'primary' },
  size: { type: String, default: 'md' },
  block: { type: Boolean, default: false },
  type: { type: String, default: 'button' },
})

const btnClass = computed(() => {
  const base = []
  // variant mapping: primary, secondary, danger, outline-primary, etc.
  if (props.variant.startsWith('outline-')) {
    base.push(`btn btn-${props.variant}`)
  } else {
    base.push(`btn btn-${props.variant}`)
  }
  if (props.size === 'sm') base.push('btn-sm')
  if (props.size === 'lg') base.push('btn-lg')
  if (props.block) base.push('w-100')
  return base.join(' ')
})
</script>

<style scoped>
/* small helper: ensure focus ring is subtle */
.btn:focus{box-shadow:0 0 0 0.25rem rgba(13,110,253,0.18)}
</style>
