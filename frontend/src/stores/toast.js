import { defineStore } from 'pinia'

let nextId = 1

export const useToastStore = defineStore('toast', {
  state: () => ({ toasts: [] }),
  actions: {
    show(message, variant = 'primary', timeout = 5000){
      const id = nextId++
      this.toasts.push({ id, message, variant })
      if(timeout && timeout>0){
        setTimeout(()=> this.remove(id), timeout)
      }
      return id
    },
    success(message, timeout=4000){ return this.show(message, 'success', timeout) },
    error(message, timeout=6000){ return this.show(message, 'danger', timeout) },
    info(message, timeout=4000){ return this.show(message, 'info', timeout) },
    remove(id){ this.toasts = this.toasts.filter(t => t.id !== id) }
  }
})

export function useToastStoreAlias(){ return useToastStore() }
