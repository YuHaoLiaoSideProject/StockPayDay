<script setup lang="ts">
/**
 * 空狀態畫面
 * Props: message (string)
 */
defineProps<{ message: string }>()
</script>

<template>
  <div class="empty-state">
    <div class="state-icon-wrapper empty">
      <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" y1="3" x2="12" y2="15"/>
      </svg>
    </div>
    <p class="state-title">暫無資料</p>
    <p class="state-desc">{{ message }}</p>
  </div>
</template>
