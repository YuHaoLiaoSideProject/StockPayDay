<script setup lang="ts">
/**
 * 根組件
 *
 * 整合：
 * - Vue Router
 * - SearchBar（導覽列）
 * - 追蹤清單連結 + 徽章
 * - 深色模式切換
 */
import { useRouter } from 'vue-router'
import { useSearch } from './composables/useSearch'
import { useWatchlist } from './composables/useWatchlist'
import { useDarkMode } from './composables/useDarkMode'
import SearchBar from './components/SearchBar.vue'
import WatchlistButton from './components/WatchlistButton.vue'

const router = useRouter()
const { query, results } = useSearch()
const { watchedCodes } = useWatchlist()
const { isDark, toggle: toggleDark } = useDarkMode()

function onStockSelect(result: { code: string; name: string }) {
  router.push(`/stock/${result.code}`)
  query.value = ''
}

function goToWatchlist() {
  router.push('/watchlist')
}
</script>

<template>
  <div class="app-root" :class="{ dark: isDark }">
    <!-- Header -->
    <header class="app-header">
      <div class="header-inner">
      <div class="header-left">
        <a href="javascript:void(0)" @click="() => router.push('/')" class="app-logo">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span class="logo-text">StockPayDay++</span>
        </a>
      </div>
      <div class="header-right">
        <div class="header-icon-group">
          <button class="header-icon-btn" @click="goToWatchlist" aria-label="追蹤清單">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
            </svg>
            <span v-if="watchedCodes.size > 0" class="watchlist-badge">{{ watchedCodes.size }}</span>
          </button>

          <button class="theme-toggle" @click="toggleDark" :aria-label="isDark ? '切換為淺色模式' : '切換為深色模式'">
            <svg v-if="isDark" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
            <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          </button>
        </div>
      </div>
      </div>
    </header>

    <!-- Router View -->
    <main class="app-main">
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
      <router-view />
    </main>
  </div>
</template>
