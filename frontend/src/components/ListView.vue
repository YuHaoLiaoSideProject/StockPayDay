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
import { computed } from 'vue'
import type { UpcomingDividend } from '../types/stock'
import ListItem from './ListItem.vue'
import EmptyState from './EmptyState.vue'

const props = defineProps<{ items: UpcomingDividend[] }>()

const emit = defineEmits<{
  'stock-click': [code: string]
}>()

/** 按日期分組（從早到晚排序） */
const groupedItems = computed(() => {
  const groups: Record<string, UpcomingDividend[]> = {}
  for (const item of props.items) {
    const date = item.ex_date
    if (!groups[date]) groups[date] = []
    groups[date].push(item)
  }
  // 按日期從早到晚排序
  return Object.entries(groups).sort(([a], [b]) => a.localeCompare(b))
})

/** 本地化日期格式 e.g. 8月25日（週二） */
function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  const m = d.getMonth() + 1
  const day = d.getDate()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${m}月${day}日（週${weekdays[d.getDay()]}）`
}
</script>

<template>
  <div class="list-view">
    <div class="list-header">
      <div>日期</div>
      <div>代號</div>
      <div>名稱</div>
      <div style="text-align: right;">金額</div>
      <div></div>
    </div>
    <template v-for="[date, group] in groupedItems" :key="date">
      <div class="list-date-group">
        <span>{{ formatDate(date) }}</span>
        <span class="group-count">{{ group.length }} 支</span>
      </div>
      <ListItem
        v-for="item in group"
        :key="`${item.code}-${item.ex_date}`"
        :dividend="item"
        class="clickable"
        tabindex="0"
        @click="emit('stock-click', item.code)"
        @keydown.enter="emit('stock-click', item.code)"
      />
    </template>
    <EmptyState v-if="items.length === 0" message="目前沒有即將配息的證券" />
  </div>
</template>
