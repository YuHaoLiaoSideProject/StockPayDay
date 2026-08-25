<script setup lang="ts">
/**
 * WatchlistItemRow 追蹤項目列
 *
 * 顯示單一追蹤股票，含/不含配息資訊。
 * 用於追蹤清單中顯示所有已追蹤的股票。
 */
import { computed } from 'vue'
import type { UpcomingDividend } from '../types/stock'
import WatchlistButton from './WatchlistButton.vue'

interface Props {
  code: string
  name?: string
  dividend?: UpcomingDividend
}

const props = withDefaults(defineProps<Props>(), {
  name: '',
})

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

/** 顯示名稱：優先使用 props.name，其次用 dividend.name，最後用 code */
const displayName = computed(() => props.name || props.dividend?.name || props.code)
</script>

<template>
  <div class="watchlist-item-row" @click="$emit('stock-click', code)">
    <span class="item-code">{{ code }}</span>
    <span class="item-name">{{ displayName }}</span>
    <span v-if="dividend" class="item-dividend">
      {{ formatAmount(dividend.cash_dividend) }}
    </span>
    <span v-else class="item-no-dividend">無近期配息</span>
    <WatchlistButton
      :code="code"
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
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background-color var(--transition-fast);
  border-radius: 6px;
}

.watchlist-item-row:hover {
  background-color: var(--surface-2);
}

.item-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-weight: 600;
  color: var(--text);
  font-variant-numeric: tabular-nums;
}

.item-name {
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-dividend {
  font-weight: 600;
  color: var(--amount-color);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.item-no-dividend {
  color: var(--text-muted);
  font-size: 0.8125rem;
  text-align: right;
}
</style>
