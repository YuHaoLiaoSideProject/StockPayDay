<script setup lang="ts">
/**
 * 日期配息明細 Modal
 *
 * 顯示某日所有配息股票，點擊可導航至單股歷史（Phase 5）。
 */
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import type { UpcomingDividend } from '../types/stock'

defineProps<{
  date: string
  dividends: UpcomingDividend[]
}>()

const emit = defineEmits<{
  close: []
  'stock-click': [code: string]
}>()

// Focus trap & Escape key handling
const modalContent = ref<HTMLElement | null>(null)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  nextTick(() => {
    modalContent.value?.focus()
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
})
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div ref="modalContent" class="modal-content" tabindex="-1">
      <div class="modal-header">
        <h3>{{ date }} 配息股票</h3>
        <button class="modal-close" aria-label="關閉" @click="emit('close')">✕</button>
      </div>
      <div v-if="dividends.length === 0" class="empty-hint" style="text-align:center;color:#9ca3af;padding:1rem 0;">
        該日無配息股票
      </div>
      <ul v-else class="modal-list">
        <li
          v-for="item in dividends"
          :key="item.code"
          class="dividend-item"
          @click="emit('stock-click', item.code)"
        >
          <span>
            <span class="code">{{ item.code }}</span>
            <span class="name">{{ item.name }}</span>
          </span>
          <span class="amount">${{ (item.dividend ?? item.cash_dividend ?? 0).toFixed(2) }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>
