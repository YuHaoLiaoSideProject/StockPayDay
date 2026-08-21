<script setup lang="ts">
/**
 * 列表項目
 *
 * 顯示：日期、代號、名稱、金額
 */
import type { UpcomingDividend } from '../types/stock'

defineProps<{ dividend: UpcomingDividend }>()
</script>

<template>
  <div class="list-item">
    <span class="item-date">{{ dividend.ex_date }}</span>
    <span class="item-code">{{ dividend.code }}</span>
    <span class="item-name">{{ dividend.name }}</span>
    <span class="item-amount">${{ dividend.dividend.toFixed(2) }}</span>
  </div>
</template>
