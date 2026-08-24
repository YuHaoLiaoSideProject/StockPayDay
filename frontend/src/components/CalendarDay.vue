<script setup lang="ts">
/**
 * 單日格子
 *
 * 標示是否有配息（has-dividend class），
 * 非當月日期半透明。
 * 追蹤股票顯示代號 + ♥，非追蹤顯示代號。
 * 最多顯示 3 支，超過顯示 +N。
 */
import { computed } from 'vue'
import type { CalendarDay } from '../types/stock'
import { useWatchlist } from '../composables/useWatchlist'

const props = defineProps<{ day: CalendarDay }>()

const { watchedCodes } = useWatchlist()

const MAX_DISPLAY = 2

// 該日是否有追蹤股票的配息
const hasWatchedDividend = computed(() => {
  return props.day.dividends.some(d => watchedCodes.value.has(d.code))
})

// 排序後的配息資料：追蹤優先，再依代號排序
const sortedDividends = computed(() => {
  return [...props.day.dividends].sort((a, b) => {
    const aWatched = watchedCodes.value.has(a.code) ? 0 : 1
    const bWatched = watchedCodes.value.has(b.code) ? 0 : 1
    if (aWatched !== bWatched) return aWatched - bWatched
    return a.code.localeCompare(b.code)
  })
})

// 顯示的配息項目（最多 3 支）
const displayedDividends = computed(() => {
  return sortedDividends.value.slice(0, MAX_DISPLAY)
})

// 超過 3 支的數量
const overflowCount = computed(() => {
  return Math.max(0, props.day.dividends.length - MAX_DISPLAY)
})

// 判斷是否為追蹤股票
function isWatched(code: string): boolean {
  return watchedCodes.value.has(code)
}
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
    <span class="day-number">{{ parseInt(day.date.split('-')[2], 10) }}</span>
    
    <!-- 配息股票代號列表 -->
    <div v-if="day.hasDividend" class="dividend-labels">
      <span
        v-for="item in displayedDividends"
        :key="item.code"
        class="dividend-label"
        :class="{ 'dividend-label--watched': isWatched(item.code) }"
      >
        {{ item.code }}<span v-if="isWatched(item.code)" class="watched-heart">♥</span>
      </span>
      <span v-if="overflowCount > 0" class="dividend-more">
        +{{ overflowCount }}
      </span>
    </div>
  </div>
</template>
