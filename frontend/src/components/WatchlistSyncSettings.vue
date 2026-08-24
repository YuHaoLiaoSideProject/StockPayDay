<script setup lang="ts">
/**
 * WatchlistSyncSettings 同步設定（Phase 9 子任務 C）
 *
 * - 未配對：email 輸入框（主要）+ 配對碼直接輸入（備援）＋說明；空白輸入不可送出
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

const {
  bucketId,
  status,
  lastSyncedAt,
  lastError,
  syncActive,
  createAccount,
  confirmVerification,
  setToken,
  clearToken,
  syncOnce,
} = useWatchlistSync()
const { items, add, isWatched } = useWatchlist()

const emailInput = ref('')
const tokenInput = ref('')
const showTokenInput = ref(false)
const creating = ref(false)  // createAccount 進行中
const createError = ref('')  // createAccount 錯誤訊息
const createdBucketId = ref('')  // createAccount 成功後的 bucket ID
const copied = ref(false)
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

/** Email 啟動：直連 kvdb.io 建立 bucket */
async function onEmailSubmit() {
  if (!emailInput.value.trim() || creating.value) return
  creating.value = true
  createError.value = ''
  try {
    const result = await createAccount(emailInput.value)
    createdBucketId.value = result.bucketId
    emailInput.value = ''
  } catch (err) {
    createError.value = err instanceof Error ? err.message : '建立失敗，請檢查網路連線'
  } finally {
    creating.value = false
  }
}

/** 複製 bucket ID 到剪貼簿 */
async function onCopyBucketId() {
  try {
    await navigator.clipboard.writeText(createdBucketId.value)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    // fallback: textarea 選取複製
    const ta = document.createElement('textarea')
    ta.value = createdBucketId.value
    ta.style.position = 'fixed'
    ta.style.opacity = '0'
    document.body.appendChild(ta)
    ta.select()
    document.execCommand('copy')
    document.body.removeChild(ta)
    copied.value = true
    setTimeout(() => { copied.value = false }, 2000)
  }
}

/** 確認 email 已驗證，啟動同步 */
function onConfirmVerification() {
  confirmVerification()
}

/** 配對碼直接輸入（備援：使用者已有 token 時可直接貼上） */
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
    <!-- 未配對：email 輸入（主要）+ 配對碼備援 -->
    <div v-if="!bucketId && !createdBucketId" class="sync-pairing">
      <h3 class="sync-title">🔄 跨裝置同步（選配）</h3>
      <p class="sync-desc">
        輸入 email 後，系統自動建立雲端空間。驗證 email 後即可跨裝置同步。不設定則完全不影響現有功能。
      </p>

      <!-- Email 啟動（主要方式） -->
      <form class="sync-token-form" @submit.prevent="onEmailSubmit">
        <input
          v-model="emailInput"
          class="sync-input"
          type="email"
          placeholder="輸入 email 啟動同步"
          aria-label="email"
          required
          :disabled="creating"
          data-testid="sync-email-input"
        />
        <button
          class="btn-primary"
          type="submit"
          :disabled="creating || !emailInput.trim()"
          data-testid="sync-email-submit"
        >
          {{ creating ? '建立中…' : '建立' }}
        </button>
      </form>

      <!-- 建立帳號錯誤訊息 -->
      <p v-if="createError" class="sync-error" data-testid="sync-create-error">
        {{ createError }}
      </p>

      <!-- 配對碼備援（已有 token 時直接貼上） -->
      <div class="sync-token-fallback">
        <button
          type="button"
          class="sync-fallback-toggle"
          data-testid="sync-token-toggle"
          @click="showTokenInput = !showTokenInput"
        >
          {{ showTokenInput ? '收起配對碼輸入' : '已有同步碼？直接貼上' }}
        </button>
        <form v-if="showTokenInput" class="sync-token-form" @submit.prevent="onTokenSubmit">
          <input
            v-model="tokenInput"
            class="sync-input"
            type="text"
            placeholder="貼上同步碼（Bucket ID）"
            aria-label="同步碼"
            required
            data-testid="sync-token-input"
          />
          <button class="btn-primary" type="submit" data-testid="sync-token-submit">啟動</button>
        </form>
      </div>
    </div>

    <!-- Bucket 已建立：顯示 ID + 驗證提示 -->
    <div v-else-if="createdBucketId && !syncActive" class="sync-pairing">
      <h3 class="sync-title">✅ 同步空間已建立</h3>

      <div class="bucket-id-display">
        <label class="bucket-label">同步碼（Bucket ID）：</label>
        <div class="bucket-id-row">
          <code class="bucket-id-code" data-testid="bucket-id-display">{{ createdBucketId }}</code>
          <button class="btn-copy" @click="onCopyBucketId" data-testid="copy-bucket-id">
            {{ copied ? '已複製 ✓' : '複製' }}
          </button>
        </div>
        <p class="sync-desc">請將此同步碼貼到其他裝置的設定區，即可跨裝置同步追蹤清單。</p>
      </div>

      <div class="verify-notice">
        <p>📧 <strong>重要</strong>：請到 <a href="https://kvdb.io/login" target="_blank" rel="noopener">kvdb.io/login</a> 用此 email 登入以啟用帳號。啟用後點下方按鈕開始同步。</p>
        <button class="btn-primary" @click="onConfirmVerification" data-testid="confirm-verification">
          我已完成啟用，開始同步
        </button>
      </div>
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

.sync-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.sync-token-fallback {
  margin-top: 0.5rem;
}

.sync-fallback-toggle {
  border: none;
  background: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 0.75rem;
  padding: 0.125rem 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.sync-fallback-toggle:hover {
  color: var(--tab-active-bg);
}

.bucket-id-display {
  margin: 0.75rem 0;
  padding: 0.75rem;
  background: var(--surface-2);
  border-radius: 8px;
  border: 1px solid var(--border);
}

.bucket-label {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text);
  display: block;
  margin-bottom: 0.375rem;
}

.bucket-id-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.bucket-id-code {
  flex: 1;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 1rem;
  font-weight: 600;
  color: var(--tab-active-bg);
  padding: 0.5rem 0.75rem;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 6px;
  word-break: break-all;
  user-select: all;
}

.btn-copy {
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  font-size: 0.8125rem;
  white-space: nowrap;
  transition: all var(--transition-fast);
}

.btn-copy:hover {
  background: var(--surface-2);
  border-color: var(--tab-active-bg);
}

.verify-notice {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(59, 130, 246, 0.08);
  border: 1px solid rgba(59, 130, 246, 0.2);
  border-radius: 8px;
}

.verify-notice p {
  margin: 0 0 0.5rem;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.verify-notice .btn-primary {
  width: 100%;
}
</style>