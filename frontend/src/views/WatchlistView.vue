<script setup lang="ts">
/**
 * 追蹤清單頁面
 *
 * 路由：/watchlist
 * 功能：顯示追蹤股票的行事曆/列表視圖。
 */
import WatchlistView from '../components/WatchlistView.vue'
</script>

<template>
  <div class="watchlist-page">
    <!-- 頁面標題 -->
    <div class="watchlist-header">
      <h1 class="watchlist-title">❤️ 我的追蹤清單</h1>
      <p class="watchlist-subtitle">追蹤感興趣的證券，掌握配息時程</p>
    </div>

    <!-- 追蹤清單視圖 -->
    <WatchlistView />
  </div>
</template>
