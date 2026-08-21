import { describe, it, expect, vi, beforeEach } from 'vitest'
import { nextTick } from 'vue'
import { useDarkMode } from '../useDarkMode'

describe('useDarkMode', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
  })

  it('should default to light mode when no stored preference', () => {
    // Mock matchMedia to return light
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
      matches: false,
    }))

    const { isDark } = useDarkMode()
    expect(isDark.value).toBe(false)
  })

  it('should default to dark when system prefers dark', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
      matches: true,
    }))

    const { isDark } = useDarkMode()
    expect(isDark.value).toBe(true)
  })

  it('should read from localStorage', () => {
    localStorage.setItem('stockpayday-dark-mode', 'true')

    const { isDark } = useDarkMode()
    expect(isDark.value).toBe(true)
  })

  it('should toggle dark mode', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
      matches: false,
    }))

    const { isDark, toggle } = useDarkMode()
    expect(isDark.value).toBe(false)

    toggle()
    expect(isDark.value).toBe(true)
    expect(localStorage.getItem('stockpayday-dark-mode')).toBe('true')
  })

  it('should apply dark class to html element', async () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({
      matches: false,
    }))

    const { toggle } = useDarkMode()
    toggle()

    // watchEffect needs nextTick to flush
    await nextTick()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })
})
