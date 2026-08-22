<script setup lang="ts">
/**
 * 追蹤清單頁面
 *
 * 路由：/watchlist
 * 功能：顯示追蹤股票的行事曆/列表視圖。
 * 頁面頂部提供常駐搜尋欄（空狀態亦可用），可直接從結果 ❤️ 加入追蹤。
 */
import { useRouter } from 'vue-router'
import SearchBar from '../components/SearchBar.vue'
import WatchlistButton from '../components/WatchlistButton.vue'
import WatchlistView from '../components/WatchlistView.vue'
import { useSearch } from '../composables/useSearch'

const router = useRouter()
// 頁面獨立搜尋狀態（與導覽列 useSearch 互不干擾）
const { query, results } = useSearch()

function onStockSelect(result: { code: string; name: string }) {
  router.push(`/stock/${result.code}`)
  query.value = ''
}
</script>

<template>
  <div class="watchlist-page">
    <!-- 頁面標題 -->
    <div class="watchlist-header">
      <h1 class="watchlist-title">❤️ 我的追蹤清單</h1>
      <p class="watchlist-subtitle">追蹤感興趣的證券，掌握配息時程</p>
    </div>

    <!-- 追蹤清單頁常駐搜尋欄（頁面層，不受 header mobile 收合規則影響） -->
    <div class="watchlist-search" data-testid="watchlist-search">
      <SearchBar v-model="query" :results="results" @select="onStockSelect">
        <template #result-actions="{ result }">
          <WatchlistButton
            :code="result.code"
            :name="result.name"
            type="stock"
            size="sm"
          />
        </template>
      </SearchBar>
    </div>

    <!-- 追蹤清單視圖 -->
    <WatchlistView />
  </div>
</template>
