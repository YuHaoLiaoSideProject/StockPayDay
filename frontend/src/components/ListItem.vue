<script setup lang="ts">
/**
 * 列表項目
 *
 * 顯示：日期、代號、名稱、金額、追蹤按鈕
 */
import type { UpcomingDividend } from '../types/stock'
import WatchlistButton from './WatchlistButton.vue'

defineProps<{ dividend: UpcomingDividend }>()

defineEmits<{
  'stock-click': [code: string]
}>()
</script>

<template>
  <div class="list-item" @click="$emit('stock-click', dividend.code)">
    <span class="item-date">{{ dividend.ex_date }}</span>
    <span class="item-code">{{ dividend.code }}</span>
    <span class="item-name">{{ dividend.name }}</span>
    <span class="item-amount">${{ (dividend.dividend ?? dividend.cash_dividend ?? 0).toFixed(2) }}</span>
    <WatchlistButton
      :code="dividend.code"
      :name="dividend.name"
      :type="(dividend.type as 'stock' | 'etf' | 'preferred')"
      size="sm"
    />
  </div>
</template>
