<script setup lang="ts">
/**
 * 錯誤畫面
 * Props: message (string)
 * Emits: retry
 */
defineProps<{ message: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div class="error-state">
    <p class="msg">{{ message }}</p>
    <button class="retry-btn" @click="emit('retry')">重試</button>
  </div>
</template>
