import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useConfirmStore = defineStore('confirm', () => {
  const resolved = ref(null)
  const message = ref('')

  function show(msg){
    message.value = String(msg || '')
    resolved.value = null
    return new Promise((resolve) => {
      resolved.value = resolve
    })
  }

  function accept(){ if(resolved.value) resolved.value(true) }
  function cancel(){ if(resolved.value) resolved.value(false) }

  return { message, show, accept, cancel }
})
