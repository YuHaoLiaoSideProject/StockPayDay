<script setup lang="ts">
/**
 * WatchlistView 追蹤清單視圖
 *
 * 顯示追蹤股票的行事曆/列表模式。
 * 從 useWatchlist 取得追蹤清單，結合 upcoming 資料顯示配息資訊。
 */
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWatchlist } from '../composables/useWatchlist'
import { useUpcoming } from '../composables/useUpcoming'
import { useCalendar } from '../composables/useCalendar'
import Calendar from './Calendar.vue'
import ListView from './ListView.vue'
import WatchlistEmpty from './WatchlistEmpty.vue'
import ViewSwitcher from './ViewSwitcher.vue'
import type { ViewMode, UpcomingDividend } from '../types/stock'

const { items, watchedCodes } = useWatchlist()
const { upcoming, status, load } = useUpcoming()
const router = useRouter()

const currentView = ref<ViewMode>('calendar')

onMounted(() => {
  if (status.value === 'loading') {
    load()
  }
})

// 追蹤股票的配息資料
const watchlistUpcoming = computed<UpcomingDividend[]>(() => {
  return upcoming.value.filter(item => watchedCodes.value.has(item.code))
})

// 追蹤股票的配息日期集合
const watchlistDividendDates = computed(() => {
  return new Set(watchlistUpcoming.value.map(item => item.ex_date))
})

// 追蹤清單是否為空
const isEmpty = computed(() => items.value.length === 0)

// 行事曆資料（傳入追蹤股票的配息日期和配息資料）
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(
  watchlistDividendDates,
  watchlistUpcoming
)

// 依日期排序的列表
const sortedUpcoming = computed(() => {
  return [...watchlistUpcoming.value].sort(
    (a, b) => a.ex_date.localeCompare(b.ex_date)
  )
})

function handleViewChange(view: ViewMode) {
  currentView.value = view
}

/** 列表模式點擊證券 → 導航至單股頁（與首頁行為一致） */
function handleStockClick(code: string) {
  router.push(`/stock/${code}`)
}

// Watchlist calendar: clicking a date does nothing special (no modal),
// but we handle the event to avoid a dead click target.
function handleDateClick(_date: string) {
  // intentionally empty — watchlist mode shows data on calendar, no day detail modal
}
</script>

<template>
  <div class="watchlist-view">
    <!-- 追蹤清單為空 -->
    <WatchlistEmpty v-if="isEmpty" />

    <!-- 有追蹤股票 -->
    <template v-else>
      <!-- 視圖切換 -->
      <div class="watchlist-controls">
        <ViewSwitcher :current-view="currentView" @view-change="handleViewChange" />
      </div>

      <!-- 行事曆模式 -->
      <Calendar
        v-if="currentView === 'calendar'"
        :month-label="monthLabel"
        :days="days"
        @prev-month="prevMonth"
        @next-month="nextMonth"
        @date-click="handleDateClick"
      />

      <!-- 列表模式 -->
      <ListView
        v-else
        :items="sortedUpcoming"
        @stock-click="handleStockClick"
      />

      <!-- 追蹤股票數量提示 -->
      <div class="watchlist-count">
        已追蹤 {{ items.length }} 支證券
      </div>
    </template>
  </div>
</template>
