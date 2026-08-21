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
    <header class="app-header">
      <h1>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        StockPayDay++
      </h1>
      <button class="theme-toggle" @click="toggleDark">
        <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <circle cx="12" cy="12" r="5"/>
          <line x1="12" y1="1" x2="12" y2="3"/>
          <line x1="12" y1="21" x2="12" y2="23"/>
          <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
          <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
          <line x1="1" y1="12" x2="3" y2="12"/>
          <line x1="21" y1="12" x2="23" y2="12"/>
          <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
          <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
        </svg>
        <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
        </svg>
      </button>
    </header>

    <!-- 狀態處理 -->
    <LoadingState v-if="status === 'loading'" />
    <ErrorState v-else-if="status === 'error'" :message="errorMessage" @retry="retry" />
    <EmptyState v-else-if="status === 'empty'" message="目前沒有即將配息的證券" />

    <!-- 主要內容 -->
    <template v-else>
      <div class="content-container">
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
      </div>

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
