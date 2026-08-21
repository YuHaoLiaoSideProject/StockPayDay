<script setup lang="ts">
/**
 * 模式切換 Tab
 *
 * Props:
 *   - currentView: 'calendar' | 'list'
 *
 * Emits:
 *   - view-change(view: ViewMode)
 */
import type { ViewMode } from '../types/stock'

defineProps<{ currentView: ViewMode }>()

const emit = defineEmits<{
  'view-change': [view: ViewMode]
}>()
</script>

<template>
  <div class="view-switcher" role="tablist" aria-label="顯示模式">
    <button
      role="tab"
      data-view="calendar"
      :aria-selected="currentView === 'calendar'"
      :class="{ active: currentView === 'calendar' }"
      @click="emit('view-change', 'calendar')"
    >
      📅 行事曆
    </button>
    <button
      role="tab"
      data-view="list"
      :aria-selected="currentView === 'list'"
      :class="{ active: currentView === 'list' }"
      @click="emit('view-change', 'list')"
    >
      📋 列表
    </button>
  </div>
</template>
