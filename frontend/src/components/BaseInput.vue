<template>
  <div>
    <input :type="type" class="form-control" :placeholder="placeholder" :value="modelValue" @input="$emit('update:modelValue', $event.target.value)" />
  </div>
</template>

<script setup>
defineProps({ modelValue: [String, Number], placeholder: String, type: { type: String, default: 'text' } })
</script>

<style scoped>
/* minimal: inherit Bootstrap form-control */
</style>
