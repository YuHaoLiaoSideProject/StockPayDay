<script setup lang="ts">
/**
 * WatchlistSyncSettings 同步設定（Phase 9 子任務 C）
 *
 * - 未配對：配對碼輸入框＋說明；空白輸入不可送出（表單 submit 阻擋）
 * - 已配對：同步狀態（同步中…／已同步＋上次同步時間／同步失敗＋錯誤訊息，含 429 退避）
 *           ＋「立即同步」＋「停用」（停用不刪本地清單）
 * - 匯出/匯入備援：匯出目前追蹤項目（不含已移除）；匯入貼上內容合併、依 code 去重、
 *   格式錯誤顯示錯誤且本地清單不變
 */
import { ref } from 'vue'
import { useWatchlistSync } from '../composables/useWatchlistSync'
import { useWatchlist } from '../composables/useWatchlist'
import {
  exportWatchlistToText,
  parseWatchlistImportText,
  WatchlistImportError,
} from '../composables/useWatchlistExport'

const { token, status, lastSyncedAt, lastError, setToken, clearToken, syncOnce } = useWatchlistSync()
const { items, add, isWatched } = useWatchlist()

const tokenInput = ref('')
const backupOpen = ref(false)
const exportText = ref('')
const importText = ref('')
const importError = ref('')
const importMessage = ref('')

const statusLabel: Record<string, string> = {
  disabled: '未啟用同步',
  idle: '已配對',
  syncing: '同步中…',
  synced: '已同步',
  error: '同步失敗',
}

function formatTime(ts: number | null): string | null {
  return ts ? new Date(ts).toLocaleTimeString() : null
}

/** 啟動：空白輸入不可送出（submit 阻擋） */
function onTokenSubmit() {
  if (!tokenInput.value.trim()) return
  setToken(tokenInput.value)
  tokenInput.value = ''
}

/** 匯出：目前追蹤項目（不含已移除墓碑） */
function handleExport() {
  exportText.value = exportWatchlistToText(items.value)
}

/** 匯入：貼上內容解析後合併進本地清單（依 code 去重）；格式錯誤顯示錯誤且本地不變 */
function handleImport() {
  importError.value = ''
  importMessage.value = ''
  if (!importText.value.trim()) {
    importError.value = '請先貼上匯出內容'
    return
  }
  try {
    const parsed = parseWatchlistImportText(importText.value)
    let addedCount = 0
    for (const item of parsed) {
      if (!isWatched(item.code)) {
        add(item.code, item.name, item.type)
        addedCount++
      }
    }
    importText.value = ''
    importMessage.value = addedCount > 0 ? `已合併 ${addedCount} 支證券` : '內容與本地清單相同，無新增'
  } catch (err) {
    importError.value =
      err instanceof WatchlistImportError ? err.message : '匯入失敗：內容無法解析'
  }
}
</script>

<template>
  <section class="watchlist-sync-settings" data-testid="watchlist-sync-settings">
    <!-- 未配對：配對碼輸入 -->
    <div v-if="!token" class="sync-pairing">
      <h3 class="sync-title">🔄 跨裝置同步（選配）</h3>
      <p class="sync-desc">
        貼上配對碼後，追蹤清單會在本裝置與其他裝置間自動同步。不設定則完全不影響現有功能。
      </p>
      <form class="sync-token-form" @submit.prevent="onTokenSubmit">
        <input
          v-model="tokenInput"
          class="sync-input"
          type="text"
          placeholder="貼上配對碼（access token）"
          aria-label="配對碼"
          required
          data-testid="sync-token-input"
        />
        <button class="btn-primary" type="submit" data-testid="sync-token-submit">啟動</button>
      </form>
    </div>

    <!-- 已配對：同步狀態 + 操作 -->
    <div v-else class="sync-status-row">
      <div class="sync-status-info">
        <span class="sync-title">🔄 同步狀態：{{ statusLabel[status] }}</span>
        <span v-if="lastSyncedAt" class="sync-last-synced">
          上次同步 {{ formatTime(lastSyncedAt) }}
        </span>
        <p v-if="lastError" class="sync-error" data-testid="watchlist-sync-error">{{ lastError }}</p>
      </div>
      <div class="sync-actions">
        <button class="btn-secondary" @click="syncOnce">立即同步</button>
        <button class="btn-danger" data-testid="sync-token-clear" @click="clearToken">停用</button>
      </div>
    </div>

    <!-- 匯出/匯入備援 -->
    <div class="sync-backup">
      <button
        type="button"
        class="sync-backup-toggle"
        data-testid="sync-backup-toggle"
        @click="backupOpen = !backupOpen"
      >
        📤 匯出/匯入備援{{ backupOpen ? '（收合）' : '' }}
      </button>

      <div v-if="backupOpen" class="sync-backup-body" data-testid="sync-backup-body">
        <div class="sync-backup-block">
          <h4 class="sync-block-title">匯出追蹤清單</h4>
          <p class="sync-desc">將目前追蹤的證券匯出成文字，可在其他裝置貼回合併。</p>
          <button
            class="btn-secondary"
            data-testid="sync-export-button"
            type="button"
            @click="handleExport"
          >
            匯出追蹤清單
          </button>
          <textarea
            v-if="exportText"
            class="sync-textarea"
            data-testid="sync-export-text"
            :value="exportText"
            readonly
            rows="6"
          ></textarea>
        </div>

        <div class="sync-backup-block">
          <h4 class="sync-block-title">匯入合併</h4>
          <p class="sync-desc">貼上其他裝置匯出的內容，重複的證券不會重複加入。</p>
          <textarea
            v-model="importText"
            class="sync-textarea"
            rows="6"
            placeholder="貼上匯出內容…"
            data-testid="sync-import-text"
          ></textarea>
          <button
            class="btn-primary"
            data-testid="sync-import-submit"
            type="button"
            @click="handleImport"
          >
            匯入
          </button>
          <p v-if="importError" class="sync-error" data-testid="sync-import-error">{{ importError }}</p>
          <p v-if="importMessage" class="sync-success" data-testid="sync-import-message">
            {{ importMessage }}
          </p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.watchlist-sync-settings {
  margin-bottom: 1rem;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  padding: 0.875rem 1rem;
}

.sync-title {
  margin: 0 0 0.25rem;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text);
}

.sync-desc {
  margin: 0 0 0.5rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.sync-token-form {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.375rem;
}

.sync-input {
  flex: 1;
  min-width: 0;
  height: 36px;
  padding: 0 0.625rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-2);
  color: var(--text);
  font-size: 0.875rem;
  box-sizing: border-box;
  transition: border-color var(--transition-fast);
}

.sync-input:focus {
  outline: none;
  border-color: var(--tab-active-bg);
}

.sync-status-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.sync-status-info {
  min-width: 0;
}

.sync-last-synced {
  margin-left: 0.5rem;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.sync-error {
  margin: 0.25rem 0 0;
  font-size: 0.8125rem;
  color: #dc2626;
}

.sync-success {
  margin: 0.5rem 0 0;
  font-size: 0.8125rem;
  color: var(--amount-color);
}

.sync-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-danger {
  padding: 0.5rem 1rem;
  border: 1px solid #f87171;
  border-radius: 8px;
  background: transparent;
  color: #dc2626;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all var(--transition-fast);
}

.btn-danger:hover {
  background: rgba(220, 38, 38, 0.08);
}

.sync-backup {
  margin-top: 0.75rem;
  border-top: 1px dashed var(--border);
  padding-top: 0.625rem;
}

.sync-backup-toggle {
  border: none;
  background: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.8125rem;
  padding: 0.125rem 0;
}

.sync-backup-toggle:hover {
  color: var(--tab-active-bg);
}

.sync-backup-body {
  display: grid;
  gap: 1rem;
  margin-top: 0.625rem;
}

@media (min-width: 640px) {
  .sync-backup-body {
    grid-template-columns: 1fr 1fr;
  }
}

.sync-block-title {
  margin: 0 0 0.25rem;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text);
}

.sync-textarea {
  display: block;
  width: 100%;
  margin: 0.5rem 0;
  padding: 0.5rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface-2);
  color: var(--text);
  font-size: 0.8125rem;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  box-sizing: border-box;
  resize: vertical;
}

.sync-textarea:focus {
  outline: none;
  border-color: var(--tab-active-bg);
}
</style>