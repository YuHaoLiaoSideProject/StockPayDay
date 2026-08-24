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
import ListView from './ListView.vue'
import ViewSwitcher from './ViewSwitcher.vue'
import WatchlistSyncSettings from './WatchlistSyncSettings.vue'
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

// 目前追蹤中的項目（排除 deleted 墓碑：同步合併後移除的股票不應再顯示）
const activeItems = computed(() => items.value.filter(item => item.deleted !== true))

// 所有追蹤項目（含配息資訊作為附加屬性）
const allWatchedItems = computed(() => {
  return activeItems.value.map(item => {
    const dividend = upcoming.value.find(u => u.code === item.code)
    return {
      ...item,
      dividend,
      hasUpcomingDividend: !!dividend,
    }
  })
})

// 有配息的追蹤項目（用於列表模式）
const watchlistWithDividends = computed(() => {
  return allWatchedItems.value
    .filter(item => item.hasUpcomingDividend)
    .map(item => item.dividend!)
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

// 追蹤清單是否為空（墓碑不列入）
const isEmpty = computed(() => activeItems.value.length === 0)

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
    <!-- 同步設定（配對碼 + 匯出/匯入備援） -->
    <WatchlistSyncSettings />

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
          <h3 class="watchlist-all-title">所有追蹤（{{ activeItems.length }} 支）</h3>
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

      <!-- 列表模式：使用 ListView 顯示（按日期分組） -->
      <template v-else>
        <ListView
          :items="watchlistWithDividends"
          @stock-click="handleStockClick"
        />
        <!-- 無近期配息的追蹤項目 -->
        <div v-if="allWatchedItems.filter(i => !i.hasUpcomingDividend).length > 0" class="watchlist-no-date-group">
          <div class="list-date-group no-date">
            <span>無近期配息</span>
            <span class="group-count">{{ allWatchedItems.filter(i => !i.hasUpcomingDividend).length }} 支</span>
          </div>
          <WatchlistItemRow
            v-for="item in allWatchedItems.filter(i => !i.hasUpcomingDividend)"
            :key="item.code"
            :code="item.code"
            :name="item.name"
            :type="item.type"
            @stock-click="handleStockClick"
          />
        </div>
      </template>

      <!-- 追蹤股票數量提示 -->
      <div class="watchlist-count">
        已追蹤 {{ activeItems.length }} 支證券
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

<style scoped>
.watchlist-no-date-group {
  margin-top: 16px;
}

.no-date {
  color: var(--color-text-muted, #999);
  font-style: italic;
}
</style>
