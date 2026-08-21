import { ref, watchEffect } from 'vue'

const STORAGE_KEY = 'stockpayday-dark-mode'

/**
 * 深色模式管理 composable
 *
 * 1. 優先讀取 localStorage
 * 2. 無設定時偵測系統偏好 (prefers-color-scheme)
 * 3. 切換時寫入 localStorage 並更新 <html> class
 */
export function useDarkMode() {
  const isDark = ref<boolean>(initDarkMode())

  watchEffect(() => {
    applyDarkMode(isDark.value)
  })

  /** 切換深色/淺色 */
  function toggle(): void {
    isDark.value = !isDark.value
    localStorage.setItem(STORAGE_KEY, String(isDark.value))
  }

  return { isDark, toggle }
}

function initDarkMode(): boolean {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored !== null) return stored === 'true'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyDarkMode(dark: boolean): void {
  document.documentElement.classList.toggle('dark', dark)
}
