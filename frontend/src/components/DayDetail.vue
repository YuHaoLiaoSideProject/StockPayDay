<script setup lang="ts">
/**
 * 日期配息明細 Modal
 *
 * 顯示某日所有配息股票，點擊可導航至單股歷史（Phase 5）。
 */
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import type { UpcomingDividend } from '../types/stock'

const props = defineProps<{
  date: string
  dividends: UpcomingDividend[]
}>()

const emit = defineEmits<{
  close: []
  'stock-click': [code: string]
}>()

// 本地化日期 e.g. 8月21日
const formattedDate = computed(() => {
  const d = new Date(props.date + 'T00:00:00')
  const m = d.getMonth() + 1
  const day = d.getDate()
  return `${m}月${day}日`
})

// Focus trap & Escape key handling
const modalContent = ref<HTMLElement | null>(null)

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  // Focus trap: Tab 循環於 modal 內
  if (e.key === 'Tab' && modalContent.value) {
    const focusable = modalContent.value.querySelectorAll<HTMLElement>(
      'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
    )
    if (focusable.length === 0) return
    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (e.shiftKey) {
      if (document.activeElement === first) {
        e.preventDefault()
        last.focus()
      }
    } else {
      if (document.activeElement === last) {
        e.preventDefault()
        first.focus()
      }
    }
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleKeydown)
  document.body.style.overflow = 'hidden'
  nextTick(() => {
    modalContent.value?.focus()
  })
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div
      ref="modalContent"
      class="modal-content"
      tabindex="-1"
      role="dialog"
      aria-modal="true"
      aria-labelledby="day-detail-title"
    >
      <div class="modal-header">
        <h3 id="day-detail-title">{{ formattedDate }} 配息股票</h3>
        <button class="modal-close" aria-label="關閉" @click="emit('close')">✕</button>
      </div>
      <div v-if="dividends.length === 0" class="empty-hint" style="text-align:center;color:var(--text-muted);padding:1rem 0;">
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
