<template>
  <div v-if="store.message" class="modal fade show d-block" style="background: rgba(0,0,0,0.4); z-index:1090">
    <div class="modal-dialog modal-dialog-centered">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title">Confirm</h5>
          <button type="button" class="btn-close" @click="onCancel"></button>
        </div>
        <div class="modal-body">{{ store.message }}</div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="onCancel">Cancel</button>
          <button class="btn btn-danger" @click="onAccept">Confirm</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useConfirmStore } from '../stores/confirm'
const store = useConfirmStore()
function onAccept(){ store.accept(); store.message = '' }
function onCancel(){ store.cancel(); store.message = '' }
</script>

<style scoped>
.modal{ display:block }
</style>
