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
import DayDetail from './DayDetail.vue'
import WatchlistEmpty from './WatchlistEmpty.vue'
import WatchlistItemRow from './WatchlistItemRow.vue'
import ViewSwitcher from './ViewSwitcher.vue'
import type { ViewMode, UpcomingDividend } from '../types/stock'

const { items, watchedCodes } = useWatchlist()
const { upcoming, status, load, getByDate } = useUpcoming()
const router = useRouter()

const currentView = ref<ViewMode>('calendar')
const selectedDate = ref<string | null>(null)

onMounted(() => {
  if (status.value === 'loading') {
    load()
  }
})

// 所有追蹤項目（含配息資訊作為附加屬性）
const allWatchedItems = computed(() => {
  return items.value.map(item => {
    const dividend = upcoming.value.find(u => u.code === item.code)
    return {
      ...item,
      dividend,
      hasUpcomingDividend: !!dividend,
    }
  })
})

// 追蹤股票中有未來配息的（用於行事曆標記）
const watchlistUpcoming = computed<UpcomingDividend[]>(() => {
  return allWatchedItems.value
    .filter(item => item.hasUpcomingDividend)
    .map(item => item.dividend!)
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

// 所有追蹤項目（依加入時間排序）
const sortedAllItems = computed(() => {
  return [...allWatchedItems.value].sort(
    (a, b) => b.addedAt - a.addedAt
  )
})

function handleViewChange(view: ViewMode) {
  currentView.value = view
}

/** 列表模式點擊證券 → 導航至單股頁（與首頁行為一致） */
function handleStockClick(code: string) {
  router.push(`/stock/${code}`)
}

function handleDateClick(date: string) {
  selectedDate.value = date
}

function handleCloseDetail() {
  selectedDate.value = null
}

// 計算選中日期的配息資料（僅追蹤清單內的）
const selectedDividends = computed(() => {
  if (!selectedDate.value) return []
  return getByDate(selectedDate.value).filter(d => watchedCodes.value.has(d.code))
})
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
      <template v-if="currentView === 'calendar'">
        <Calendar
          :month-label="monthLabel"
          :days="days"
          @prev-month="prevMonth"
          @next-month="nextMonth"
          @date-click="handleDateClick"
        />
        <!-- 行事曆下方：所有追蹤項目概覽 -->
        <div class="watchlist-all-items">
          <h3 class="watchlist-all-title">所有追蹤（{{ items.length }} 支）</h3>
          <WatchlistItemRow
            v-for="item in sortedAllItems"
            :key="item.code"
            :code="item.code"
            :name="item.name"
            :type="item.type"
            :dividend="item.dividend"
            @stock-click="handleStockClick"
          />
        </div>
      </template>

      <!-- 列表模式：顯示所有追蹤項目 -->
      <div v-else class="watchlist-all-items">
        <WatchlistItemRow
          v-for="item in sortedAllItems"
          :key="item.code"
          :code="item.code"
          :name="item.name"
          :type="item.type"
          :dividend="item.dividend"
          @stock-click="handleStockClick"
        />
        <div v-if="sortedAllItems.length === 0" class="watchlist-no-items">
          目前沒有追蹤的證券
        </div>
      </div>

      <!-- 追蹤股票數量提示 -->
      <div class="watchlist-count">
        已追蹤 {{ items.length }} 支證券
      </div>
      <!-- 日期明細 Modal -->
      <DayDetail
        v-if="selectedDate"
        :date="selectedDate"
        :dividends="selectedDividends"
        @close="handleCloseDetail"
        @stock-click="handleStockClick"
      />
    </template>
  </div>
</template>
