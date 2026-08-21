<script setup lang="ts">
/**
 * 空狀態畫面
 * Props: message (string)
 */
defineProps<{ message: string }>()
</script>

<template>
  <div class="empty-state">
    <p class="msg">{{ message }}</p>
  </div>
</template>
