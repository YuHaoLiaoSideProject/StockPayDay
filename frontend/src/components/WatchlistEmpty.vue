<script setup lang="ts">
/**
 * WatchlistEmpty 追蹤清單空狀態
 *
 * 當使用者尚未加入任何追蹤時顯示。
 * 提供引導至搜尋或首頁的連結。
 */
import { useRouter } from 'vue-router'

const router = useRouter()

function goToSearch() {
  // 聚焦搜尋欄（由 App.vue 處理）
  document.querySelector<HTMLInputElement>('.search-input')?.focus()
}

function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="watchlist-empty">
    <!-- 圖示 -->
    <div class="empty-icon">📋</div>

    <!-- 標題 -->
    <h2 class="empty-title">追蹤清單是空的</h2>

    <!-- 說明 -->
    <p class="empty-desc">
      在股票詳情頁或搜尋結果中點擊 ❤️ 按鈕，<br/>
      將感興趣的證券加入追蹤清單。
    </p>

    <!-- 操作按鈕 -->
    <div class="empty-actions">
      <button class="btn-primary" @click="goToSearch">
        🔍 搜尋股票
      </button>
      <button class="btn-secondary" @click="goHome">
        📅 查看行事曆
      </button>
    </div>
  </div>
</template>
