<script setup lang="ts">
/**
 * 單日格子
 *
 * 標示是否有配息（has-dividend class），
 * 非當月日期半透明。
 */
import type { CalendarDay } from '../types/stock'

defineProps<{ day: CalendarDay }>()
</script>

<template>
  <div
    class="calendar-day"
    :class="{
      'other-month': !day.isCurrentMonth,
      'is-today': day.isToday,
      'has-dividend': day.hasDividend,
    }"
    :data-date="day.date"
  >
    <span class="day-number">{{ new Date(day.date + 'T00:00:00').getDate() }}</span>
    <span v-if="day.hasDividend" class="dividend-dot"></span>
  </div>
</template>
