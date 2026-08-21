<script setup lang="ts">
/**
 * 行事曆組件
 *
 * Props:
 *   - monthLabel: 月份標題
 *   - days: 行事曆格子資料
 *
 * Emits:
 *   - date-click(date: string) — 點擊日期
 *   - prev-month — 切換上月
 *   - next-month — 切換下月
 */
import type { CalendarDay } from '../types/stock'
import CalendarDayComponent from './CalendarDay.vue'

defineProps<{
  monthLabel: string
  days: CalendarDay[]
}>()

const emit = defineEmits<{
  'date-click': [date: string]
  'prev-month': []
  'next-month': []
}>()

// 星期標題
const weekHeaders = ['日', '一', '二', '三', '四', '五', '六']
</script>

<template>
  <div class="calendar">
    <!-- 月份導航 -->
    <div class="calendar-header">
      <button class="prev-month" @click="emit('prev-month')">‹</button>
      <h2 class="month-label">{{ monthLabel }}</h2>
      <button class="next-month" @click="emit('next-month')">›</button>
    </div>

    <!-- 星期標題列 -->
    <div class="calendar-weekdays">
      <div v-for="day in weekHeaders" :key="day" class="weekday">{{ day }}</div>
    </div>

    <!-- 日期格子（7 欄） -->
    <div class="calendar-grid">
      <CalendarDayComponent
        v-for="item in days"
        :key="item.date"
        :day="item"
        @click="emit('date-click', item.date)"
      />
    </div>
  </div>
</template>
