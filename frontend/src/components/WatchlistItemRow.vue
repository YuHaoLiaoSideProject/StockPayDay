<script setup lang="ts">
/**
 * WatchlistItemRow 追蹤項目列
 *
 * 顯示單一追蹤股票，含/不含配息資訊。
 * 用於追蹤清單中顯示所有已追蹤的股票。
 */
import type { UpcomingDividend } from '../types/stock'
import WatchlistButton from './WatchlistButton.vue'

interface Props {
  code: string
  name: string
  type?: 'stock' | 'etf' | 'preferred'
  dividend?: UpcomingDividend
}

withDefaults(defineProps<Props>(), {
  type: 'stock',
})

defineEmits<{
  'stock-click': [code: string]
}>()

/** 金額顯示 */
function formatAmount(amount?: number | null): string {
  const val = amount ?? 0
  if (val === 0) return '—'
  return `$${val.toFixed(2)}`
}
</script>

<template>
  <div class="watchlist-item-row" @click="$emit('stock-click', code)">
    <span class="item-code">{{ code }}</span>
    <span class="item-name">{{ name }}</span>
    <span v-if="dividend" class="item-dividend">
      {{ formatAmount(dividend.cash_dividend) }}
    </span>
    <span v-else class="item-no-dividend">無近期配息</span>
    <WatchlistButton
      :code="code"
      :name="name"
      :type="type"
      size="sm"
    />
  </div>
</template>

<style scoped>
.watchlist-item-row {
  display: grid;
  grid-template-columns: 80px 1fr auto auto;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-bottom: 1px solid var(--color-border, #eee);
  cursor: pointer;
  transition: background-color 0.15s;
}

.watchlist-item-row:hover {
  background-color: var(--color-hover, #f5f5f5);
}

.item-code {
  font-family: monospace;
  font-weight: 600;
  color: var(--color-text, #333);
}

.item-name {
  color: var(--color-text, #333);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-dividend {
  font-weight: 600;
  color: var(--color-accent, #e74c3c);
  text-align: right;
}

.item-no-dividend {
  color: var(--color-text-muted, #999);
  font-size: 0.9em;
  text-align: right;
}
</style>
