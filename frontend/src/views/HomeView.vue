<script setup lang="ts">
/**
 * 首頁視圖
 *
 * 職責：
 * 1. 管理顯示模式（calendar / list）
 * 2. 協調 useUpcoming + useCalendar
 * 3. 根據 status 顯示 Loading / Error / Empty / 內容
 * 4. 管理 DayDetail Modal 開關
 */
import { ref, computed, onMounted } from 'vue'
import { useUpcoming } from '../composables/useUpcoming'
import { useCalendar } from '../composables/useCalendar'
import { useDarkMode } from '../composables/useDarkMode'
import type { ViewMode } from '../types/stock'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import ViewSwitcher from '../components/ViewSwitcher.vue'
import Calendar from '../components/Calendar.vue'
import ListView from '../components/ListView.vue'
import DayDetail from '../components/DayDetail.vue'

const { upcoming, status, errorMessage, load, retry, getByDate, sortedUpcoming, dividendDates } = useUpcoming()
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(dividendDates, upcoming)
const { isDark, toggle: toggleDark } = useDarkMode()

const currentView = ref<ViewMode>('calendar')
const selectedDate = ref<string | null>(null)

onMounted(() => {
  load()
})



function handleViewChange(view: ViewMode) {
  currentView.value = view
}

function handleDateClick(date: string) {
  selectedDate.value = date
}

function handleCloseDetail() {
  selectedDate.value = null
}

// 計算選中日期的配息資料
const selectedDividends = computed(() => {
  if (!selectedDate.value) return []
  return getByDate(selectedDate.value)
})
</script>

<template>
  <div class="home-view" :class="{ dark: isDark }">
    <!-- Header -->
    <header class="app-header" style="display:flex;align-items:center;justify-content:space-between;padding:0.75rem 1rem;border-bottom:1px solid #e5e7eb;">
      <h1 style="font-size:1rem;margin:0;display:flex;align-items:center;gap:0.4rem;">
        📅 StockPayDay++
      </h1>
      <button class="theme-toggle" style="background:none;border:none;cursor:pointer;font-size:1.1rem;padding:0.4rem;border-radius:50%;transition:background 0.15s ease;" @click="toggleDark">
        {{ isDark ? '☀️' : '🌙' }}
      </button>
    </header>

    <!-- 狀態處理 -->
    <LoadingState v-if="status === 'loading'" />
    <ErrorState v-else-if="status === 'error'" :message="errorMessage" @retry="retry" />
    <EmptyState v-else-if="status === 'empty'" message="目前沒有即將配息的證券" />

    <!-- 主要內容 -->
    <template v-else>
      <ViewSwitcher :current-view="currentView" @view-change="handleViewChange" />

      <Calendar
        v-if="currentView === 'calendar'"
        :month-label="monthLabel"
        :days="days"
        @prev-month="prevMonth"
        @next-month="nextMonth"
        @date-click="handleDateClick"
      />

      <ListView
        v-else
        :items="sortedUpcoming"
      />

      <!-- 日期明細 Modal -->
      <DayDetail
        v-if="selectedDate"
        :date="selectedDate"
        :dividends="selectedDividends"
        @close="handleCloseDetail"
      />
    </template>
  </div>
</template>
