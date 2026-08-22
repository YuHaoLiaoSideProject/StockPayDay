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
    <div class="empty-icon">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
      </svg>
    </div>

    <h2 class="empty-title">追蹤清單是空的</h2>

    <p class="empty-desc">
      在股票詳情頁或搜尋結果中點擊愛心按鈕，<br/>
      將感興趣的證券加入追蹤清單。
    </p>

    <div class="empty-actions">
      <button class="btn-primary" @click="goToSearch">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        搜尋股票
      </button>
      <button class="btn-secondary" @click="goHome">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>
        查看行事曆
      </button>
    </div>
  </div>
</template>
