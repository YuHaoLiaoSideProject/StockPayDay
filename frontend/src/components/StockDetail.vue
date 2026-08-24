<script setup lang="ts">
/**
 * 單股歷史配息表格元件
 *
 * 顯示：Loading / Error / 空狀態 / 歷史配息表格
 * 歷史依年份降序排列。
 */
import { computed } from 'vue'

interface DividendHistory {
  ex_date: string
  pay_date?: string
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

/** 歷史資料依除息日降序排列（新的在前） */
const sortedHistory = computed(() => {
  if (!props.stock?.history) return []
  return [...props.stock.history].sort((a, b) => b.ex_date.localeCompare(a.ex_date))
})

/** 取得配息金額（相容不同欄位名稱） */
function getDividend(item: DividendHistory): number {
  const rec = item as unknown as Record<string, unknown>
  return (item.dividend as number) ?? (rec['cash_dividend'] as number) ?? 0
}

/** 最大配息金額（用於 bar chart 比例） */
const maxDividend = computed(() => {
  const amounts = sortedHistory.value.map(h => getDividend(h))
  return Math.max(...amounts, 1)
})

/** bar 寬度百分比 */
function barWidth(item: DividendHistory): number {
  return (getDividend(item) / maxDividend.value) * 100
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
      <div class="stock-title">
        <span class="stock-code">{{ stock.code }}</span>
        <span class="stock-name">{{ stock.name }}</span>
      </div>
    </div>

    <h2 class="section-title">配息歷史</h2>

    <table class="history-table">
      <thead>
        <tr>
          <th class="col-date col-ex-date">除息日</th>
          <th class="col-date col-pay-date">配息日</th>
          <th class="col-amount">配息金額</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in sortedHistory" :key="item.ex_date" class="history-row">
          <td class="col-date col-ex-date">{{ item.ex_date }}</td>
          <td class="col-date col-pay-date">{{ item.pay_date || '-' }}</td>
          <td class="amount">
            ${{ getDividend(item).toFixed(2) }}
            <span class="amount-bar" :style="{ width: barWidth(item) + '%' }"></span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>
