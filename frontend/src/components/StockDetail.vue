<script setup lang="ts">
/**
 * 單股歷史配息表格元件
 *
 * 顯示：Loading / Error / 空狀態 / 歷史配息表格
 * 歷史依年份降序排列。
 */
import { computed } from 'vue'

interface DividendHistory {
  year: number
  ex_date: string
  dividend?: number
  cash_dividend?: number
  stock_dividend?: number
}

interface Props {
  stock: {
    code: string
    name: string
    history: DividendHistory[]
  } | null
  loading: boolean
  error: string | null
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'back-click': []
}>()

/** 歷史資料依年份降序排列 */
const sortedHistory = computed(() => {
  if (!props.stock?.history) return []
  return [...props.stock.history].sort((a, b) => b.year - a.year)
})

/** 取得配息金額（相容不同欄位名稱） */
function getDividend(item: DividendHistory): number {
  const rec = item as unknown as Record<string, unknown>
  return (item.dividend as number) ?? (rec['cash_dividend'] as number) ?? 0
}
</script>

<template>
  <!-- Loading State -->
  <div v-if="loading" class="stock-loading">
    <div class="spinner"></div>
    <p class="loading-text">載入中...</p>
  </div>

  <!-- Error State -->
  <div v-else-if="error" class="stock-error">
    <p class="error-text">{{ error }}</p>
    <button class="back-button" @click="emit('back-click')">← 返回</button>
  </div>

  <!-- Empty State -->
  <div v-else-if="stock && sortedHistory.length === 0" class="stock-empty">
    <p class="empty-text">暫無歷史配息資料</p>
    <button class="back-button" @click="emit('back-click')">← 返回</button>
  </div>

  <!-- Stock Detail -->
  <div v-else-if="stock" class="stock-detail">
    <div class="stock-header">
      <button class="back-button" @click="emit('back-click')">← 返回</button>
      <div class="stock-title">
        <span class="stock-code">{{ stock.code }}</span>
        <span class="stock-name">{{ stock.name }}</span>
      </div>
    </div>

    <h2 class="section-title">配息歷史</h2>

    <table class="history-table">
      <thead>
        <tr>
          <th class="col-year">年份</th>
          <th class="col-date">除權息日</th>
          <th class="col-amount">配息金額</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedHistory" :key="`${item.year}-${item.ex_date}`" class="history-row">
          <td>{{ item.year }}</td>
          <td>{{ item.ex_date }}</td>
          <td class="amount">${{ getDividend(item).toFixed(2) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
