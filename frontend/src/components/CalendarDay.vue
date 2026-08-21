<script setup lang="ts">
/**
 * 單日格子
 *
 * 標示是否有配息（has-dividend class），
 * 非當月日期半透明。
 * 追蹤股票的配息日顯示紅色追蹤圓點。
 */
import { computed } from 'vue'
import type { CalendarDay } from '../types/stock'
import { useWatchlist } from '../composables/useWatchlist'

const props = defineProps<{ day: CalendarDay }>()

const { watchedCodes } = useWatchlist()

// 該日是否有追蹤股票的配息
const hasWatchedDividend = computed(() => {
  return props.day.dividends.some(d => watchedCodes.value.has(d.code))
})
</script>

<template>
  <div
    class="calendar-day"
    :class="{
      'other-month': !day.isCurrentMonth,
      'is-today': day.isToday,
      'has-dividend': day.hasDividend,
      'has-watched': hasWatchedDividend,
    }"
    :data-date="day.date"
  >
    <span class="day-number">{{ new Date(day.date + 'T00:00:00').getDate() }}</span>
    <span v-if="day.hasDividend" class="dividend-dot"></span>
    <!-- 追蹤標記（紅色小圓點） -->
    <span v-if="hasWatchedDividend" class="watched-dot"></span>
  </div>
</template>
