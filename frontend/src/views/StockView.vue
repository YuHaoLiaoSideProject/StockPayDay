<script setup lang="ts">
/**
 * 單股歷史頁面
 *
 * 路由：/stock/:code
 * 整合 useStock、StockDetail、WatchlistButton。
 */
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStock } from '../composables/useStock'
import StockDetail from '../components/StockDetail.vue'
import WatchlistButton from '../components/WatchlistButton.vue'

const route = useRoute()
const router = useRouter()

const code = computed(() => route.params.code as string)
const { stock, loading, error } = useStock(code)

function goBack() {
  // 返回前一個頁面，若無歷史則回首頁
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}
</script>

<template>
  <div class="stock-view">
    <!-- 頂部操作列：返回 + 追蹤按鈕 -->
    <div class="stock-top-bar">
      <button class="back-button" @click="goBack">← 返回</button>
      <WatchlistButton
        v-if="stock"
        :code="stock.code"
        :name="stock.name"
        size="lg"
      />
    </div>

    <StockDetail
      :stock="stock"
      :loading="loading"
      :error="error"
      @back-click="goBack"
    />
  </div>
</template>
