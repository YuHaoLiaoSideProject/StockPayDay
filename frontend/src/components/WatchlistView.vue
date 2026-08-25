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
import { useSecuritiesIndex } from '../composables/useSecuritiesIndex'
import { useCalendar } from '../composables/useCalendar'
import Calendar from './Calendar.vue'
import DayDetail from './DayDetail.vue'
import WatchlistEmpty from './WatchlistEmpty.vue'
import WatchlistItemRow from './WatchlistItemRow.vue'
import ListView from './ListView.vue'
import ViewSwitcher from './ViewSwitcher.vue'

import type { ViewMode, UpcomingDividend } from '../types/stock'

const { items, watchedCodes } = useWatchlist()
const { allMonths, status, load, getByDate, upcoming } = useUpcoming()
const { getName } = useSecuritiesIndex()
const router = useRouter()

const currentView = ref<ViewMode>('calendar')
const selectedDate = ref<string | null>(null)

onMounted(() => {
  if (status.value === 'loading') {
    load()
  }
})

const activeItems = computed(() => items.value)

// 所有追蹤項目（含配息資訊作為附加屬性）
const allWatchedItems = computed(() => {
  return activeItems.value.map(item => {
    const dividend = upcoming.value.find(u => u.code === item.code)
    return {
      code: item.code,
      addedAt: item.addedAt,
      name: dividend?.name ?? getName(item.code),
      dividend,
      hasUpcomingDividend: !!dividend,
    }
  })
})

// 追蹤清單是否為空（墓碑不列入）
const isEmpty = computed(() => activeItems.value.length === 0)

// 行事曆：只顯示追蹤股票的配息
const filteredMonths = computed(() => {
  const codes = watchedCodes.value
  const result = new Map<string, UpcomingDividend[]>()
  for (const [key, records] of allMonths.value.entries()) {
    const filtered = records.filter(item => codes.has(item.code))
    if (filtered.length > 0) result.set(key, filtered)
  }
  return result
})
const { monthLabel, days, prevMonth, nextMonth } = useCalendar(filteredMonths)

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
      <!-- 視圖切換 + 追蹤數量 -->
      <div class="watchlist-controls">
        <ViewSwitcher :current-view="currentView" @view-change="handleViewChange" />
        <span class="watchlist-count">已追蹤 {{ activeItems.length }} 支證券</span>
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
      </template>

      <!-- 列表模式：使用 ListView 顯示（按日期分組） -->
      <template v-else>
        <ListView
          :items="allWatchedItems.filter(i => i.hasUpcomingDividend).map(i => i.dividend!)"
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
            @stock-click="handleStockClick"
          />
        </div>
      </template>

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
.watchlist-controls {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.watchlist-count {
  font-size: 0.875rem;
  color: var(--text-muted);
}

.watchlist-no-date-group {
  margin-top: 16px;
}

.no-date {
  color: var(--text-muted);
  font-style: italic;
}
</style>
