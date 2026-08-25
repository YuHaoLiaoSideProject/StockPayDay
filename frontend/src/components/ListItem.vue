<script setup lang="ts">
/**
 * 列表項目
 *
 * 顯示：代號、名稱、金額、追蹤按鈕
 */
import type { UpcomingDividend } from '../types/stock'
import WatchlistButton from './WatchlistButton.vue'

defineProps<{ dividend: UpcomingDividend }>()

defineEmits<{
  'stock-click': [code: string]
}>()

/** 金額顯示：去除尾端多餘的 0，最多顯示 3 位小數 */
function formatAmount(amount?: number | null): string {
  const val = amount ?? 0
  if (val === 0) return '—'
  const rounded = Math.round(val * 1000) / 1000
  return `$${rounded.toFixed(3).replace(/\.?0+$/, '')}`
}
</script>

<template>
  <div class="list-item" @click="$emit('stock-click', dividend.code)">
    <span class="item-code">{{ dividend.code }}</span>
    <span class="item-name">{{ dividend.name }}</span>
    <span
      class="item-amount"
      :class="{ zero: (dividend.dividend ?? dividend.cash_dividend ?? 0) === 0 }"
    >{{ formatAmount(dividend.dividend ?? dividend.cash_dividend) }}</span>
    <WatchlistButton
      :code="dividend.code"
      size="sm"
    />
  </div>
</template>
