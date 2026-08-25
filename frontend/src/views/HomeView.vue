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
const { status, errorMessage, load, retry, ensureMonth, allMonths, getByDate, sortedUpcoming } = useUpcoming()

/** 當前月份 key (YYYY-MM) */
function currentMonthKey(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
}

/** 懶載入 callback：確保指定月份已載入 */
async function loadMonth(monthKey: string): Promise<void> {
  await ensureMonth(monthKey)
}

const { monthLabel, days, prevMonth, nextMonth } = useCalendar(allMonths, loadMonth)

const currentView = ref<ViewMode>('calendar')
const selectedDate = ref<string | null>(null)

onMounted(() => {
  load([currentMonthKey()])
})

/** 產生從 today 起算的月份列表（含當月） */
function getFutureMonths(count: number): string[] {
  const months: string[] = []
  const now = new Date()
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() + i, 1)
    months.push(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`)
  }
  return months
}

function handleViewChange(view: ViewMode) {
  currentView.value = view
  if (view === 'list') {
    // 列表模式需要未來配息資料，載入當月 + 未來 4 個月
    load(getFutureMonths(5))
  }
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
