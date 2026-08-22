<script setup lang="ts">
/**
 * 搜尋欄元件
 *
 * 搜尋輸入框 + 即時篩選結果下拉列表。
 * 支援 v-model 綁定 query。
 * 使用 @blur + setTimeout 處理點擊外部關閉下拉。
 */
import { ref } from 'vue'

interface SearchResult {
  code: string
  name: string
}

defineProps<{
  results: SearchResult[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  select: [result: SearchResult]
}>()

const showDropdown = ref(false)
const inputRef = ref<HTMLInputElement | null>(null)
const isExpanded = ref(false)

/** Mobile: 展開搜尋列 */
function toggleExpand() {
  isExpanded.value = !isExpanded.value
  if (isExpanded.value) {
    setTimeout(() => inputRef.value?.focus(), 100)
  } else {
    emit('update:modelValue', '')
    showDropdown.value = false
  }
}

/** 輸入時更新 query 並顯示下拉 */
function onInput(e: Event) {
  const value = (e.target as HTMLInputElement).value
  emit('update:modelValue', value)
  showDropdown.value = true
}

/** 選擇搜尋結果 */
function onSelect(result: SearchResult) {
  emit('select', result)
  showDropdown.value = false
  emit('update:modelValue', '')
}

/** 清除輸入 */
function onClear() {
  emit('update:modelValue', '')
  showDropdown.value = false
  inputRef.value?.focus()
}

/**
 * 輸入框失去焦點時關閉下拉
 * 使用 setTimeout 允許點擊結果項目的 click 事件先觸發
 */
function onBlur() {
  setTimeout(() => {
    showDropdown.value = false
  }, 150)
}

/** Escape 關閉下拉 */
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    showDropdown.value = false
    inputRef.value?.blur()
  }
}

defineExpose({ toggleExpand })
</script>

<template>
  <div class="search-bar" :class="{ expanded: isExpanded }">
    <div class="search-input-wrapper">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input
        ref="inputRef"
        type="text"
        :value="modelValue"
        @input="onInput"
        @focus="showDropdown = true"
        @blur="onBlur"
        @keydown="onKeydown"
        placeholder="搜尋股票代號或名稱..."
        class="search-input"
        role="combobox"
        :aria-expanded="!!(showDropdown && (results.length > 0 || (modelValue && results.length === 0)))"
        aria-autocomplete="list"
        aria-label="搜尋股票"
      />
      <button
        v-if="modelValue"
        class="clear-btn"
        aria-label="清除搜尋"
        @click="onClear"
      >✕</button>
    </div>

    <!-- 搜尋結果下拉 -->
    <div
      v-if="showDropdown && results.length > 0"
      class="search-results"
      role="listbox"
      aria-label="搜尋結果"
    >
      <div
        v-for="result in results"
        :key="result.code"
        class="search-result-item"
        role="option"
        @mousedown.prevent="onSelect(result)"
      >
        <div class="result-main">
          <span class="result-code">{{ result.code }}</span>
          <span class="result-name">{{ result.name }}</span>
        </div>
        <!-- 具名 slot：父層注入 ❤️ 等操作（SearchBar 與 watchlist 領域解耦） -->
        <slot name="result-actions" :result="result" />
      </div>
    </div>

    <!-- 無結果提示 -->
    <div
      v-if="showDropdown && modelValue && results.length === 0"
      class="no-results"
      role="status"
    >
      找不到符合的證券
    </div>
  </div>
</template>
