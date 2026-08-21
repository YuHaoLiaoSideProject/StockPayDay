<script setup lang="ts">
/**
 * 通用返回按鈕
 */
const emit = defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    class="back-button"
    aria-label="返回首頁"
    @click="emit('click')"
  >
    ← 返回
  </button>
</template>
