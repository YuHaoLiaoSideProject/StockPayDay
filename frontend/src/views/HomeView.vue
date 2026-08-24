<script setup lang="ts">
/**
 * 首頁視圖
 *
 * 職責：
 * 1. 管理顯示模式（calendar / list）
 * 2. 協調 useUpcoming + useCalendar
 * 3. 根據 status 顯示 Loading / Error / Empty / 內容
 * 4. 管理 DayDetail Modal 開關
 * 5. 股點擊導航至 /stock/:code
 *
 * 注意：Header 已由 App.vue 處理，此處僅負責內容區。
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUpcoming } from '../composables/useUpcoming'
import { useCalendar } from '../composables/useCalendar'
import type { ViewMode } from '../types/stock'
import LoadingState from '../components/LoadingState.vue'
import ErrorState from '../components/ErrorState.vue'
import EmptyState from '../components/EmptyState.vue'
import ViewSwitcher from '../components/ViewSwitcher.vue'
import Calendar from '../components/Calendar.vue'
import ListView from '../components/ListView.vue'
import DayDetail from '../components/DayDetail.vue'

const router = useRouter()
const { upcoming, status, errorMessage, load, retry, getByDate, sortedUpcoming, dividendDates } = useUpcoming()
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(dividendDates, upcoming)

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

function handleStockClick(code: string) {
  router.push(`/stock/${code}`)
}

// 計算選中日期的配息資料
const selectedDividends = computed(() => {
  if (!selectedDate.value) return []
  return getByDate(selectedDate.value)
})
</script>

<template>
  <div class="home-view">
    <!-- 狀態處理 -->
    <LoadingState v-if="status === 'loading'" />
    <ErrorState v-else-if="status === 'error'" :message="errorMessage" @retry="retry" />
    <EmptyState v-else-if="status === 'empty'" message="目前沒有即將配息的證券" />

    <!-- 主要內容 -->
    <template v-else>
      <div class="content-container">
        <ViewSwitcher :current-view="currentView" @view-change="handleViewChange" />

        <transition name="view-fade" mode="out-in">
          <Calendar
            v-if="currentView === 'calendar'"
            :key="'calendar'"
            :month-label="monthLabel"
            :days="days"
            @prev-month="prevMonth"
            @next-month="nextMonth"
            @date-click="handleDateClick"
          />

          <ListView
            v-else
            :key="'list'"
            :items="sortedUpcoming"
            @stock-click="handleStockClick"
          />
        </transition>
      </div>

      <!-- 日期明細 Modal -->
      <transition name="modal-fade">
        <DayDetail
          v-if="selectedDate"
          :date="selectedDate"
          :dividends="selectedDividends"
          @close="handleCloseDetail"
          @stock-click="handleStockClick"
        />
      </transition>
    </template>
  </div>
</template>
