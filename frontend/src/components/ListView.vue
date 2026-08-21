<script setup lang="ts">
/**
 * 列表模式組件
 *
 * Props:
 *   - items: 已依日期排序的配息資料
 *
 * Emits:
 *   - stock-click(code: string) — 點擊股票（Phase 5 導航）
 */
import type { UpcomingDividend } from '../types/stock'
import ListItem from './ListItem.vue'
import EmptyState from './EmptyState.vue'

defineProps<{ items: UpcomingDividend[] }>()

const emit = defineEmits<{
  'stock-click': [code: string]
}>()
</script>

<template>
  <div class="list-view">
    <div class="list-header">
      <div>日期</div>
      <div>代號</div>
      <div>名稱</div>
      <div style="text-align: right;">金額</div>
    </div>
    <ListItem
      v-for="item in items"
      :key="`${item.code}-${item.ex_date}`"
      :dividend="item"
      @click="emit('stock-click', item.code)"
    />
    <EmptyState v-if="items.length === 0" message="目前沒有即將配息的證券" />
  </div>
</template>
