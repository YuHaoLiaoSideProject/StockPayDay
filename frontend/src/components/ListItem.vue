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

/** 金額顯示：0 → "—" */
function formatAmount(amount?: number | null): string {
  const val = amount ?? 0
  if (val === 0) return '—'
  return `$${val.toFixed(2)}`
}
</script>

<template>
  <div class="list-item" @click="$emit('stock-click', dividend.code)">
    <span></span>
    <span class="item-code">{{ dividend.code }}</span>
    <span class="item-name">{{ dividend.name }}</span>
    <span
      class="item-amount"
      :class="{ zero: (dividend.dividend ?? dividend.cash_dividend ?? 0) === 0 }"
    >{{ formatAmount(dividend.dividend ?? dividend.cash_dividend) }}</span>
    <WatchlistButton
      :code="dividend.code"
      :name="dividend.name"
      :type="(dividend.type as 'stock' | 'etf' | 'preferred')"
      size="sm"
    />
  </div>
</template>
