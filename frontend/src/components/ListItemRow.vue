<script setup lang="ts">
/**
 * ListItemRow 統一列表項目列
 *
 * 主畫面 & 追蹤清單共用。顯示：代號、名稱、金額（或佔位）、追蹤按鈕。
 *
 * Props:
 *   - code: 證券代號
 *   - name: 證券名稱
 *   - cashDividend?: 現金配息金額（可選，無則顯示 "—"）
 *
 * Emits:
 *   - stock-click(code: string)
 */
import WatchlistButton from './WatchlistButton.vue'

defineProps<{
  code: string
  name: string
  cashDividend?: number | null
}>()

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
  <div class="list-item-row" @click="$emit('stock-click', code)">
    <span class="item-code">{{ code }}</span>
    <span class="item-name">{{ name }}</span>
    <span v-if="cashDividend != null" class="item-dividend">
      {{ formatAmount(cashDividend) }}
    </span>
    <span v-else class="item-dividend item-no-dividend">—</span>
    <WatchlistButton
      :code="code"
      size="sm"
    />
  </div>
</template>

<style scoped>
.list-item-row {
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

.list-item-row:hover {
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
  font-weight: 400;
}
</style>
