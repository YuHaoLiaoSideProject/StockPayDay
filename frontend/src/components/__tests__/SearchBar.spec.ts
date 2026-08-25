import { describe, it, expect, beforeEach } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import { h } from 'vue'
import SearchBar from '../SearchBar.vue'
import WatchlistButton from '../WatchlistButton.vue'
import { useWatchlist } from '../../composables/useWatchlist'

const results = [
  { code: '2330', name: '台積電' },
  { code: '2317', name: '鴻海' },
]

function mountSearchBar(modelValue = '', resultList = results) {
  return mount(SearchBar, {
    props: {
      modelValue,
      results: resultList,
    },
    slots: {
      // 父層（App / 追蹤清單頁）注入的具名 slot：❤️ WatchlistButton
      'result-actions': ({ result }: { result: { code: string; name: string } }) =>
        h(WatchlistButton, {
          code: result.code,
          size: 'sm',
        }),
    },
  })
}

async function openDropdown(wrapper: VueWrapper) {
  await wrapper.find('.search-input').trigger('focus')
}

describe('SearchBar — 功能 001（追蹤任意股票）', () => {
  beforeEach(() => {
    localStorage.clear()
    useWatchlist().reset()
  })

  it('結果列每行右側渲染 ❤️ 按鈕（slot 注入）', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const rows = wrapper.findAll('.search-result-item')
    expect(rows).toHaveLength(2)
    expect(wrapper.findAll('.search-result-item .watchlist-btn')).toHaveLength(2)
  })

  it('未追蹤 ❤️ 為空心（aria-pressed=false）、已追蹤為實心（aria-pressed=true）', async () => {
    const { toggle } = useWatchlist()
    toggle('2330')

    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const buttons = wrapper.findAll('.search-result-item .watchlist-btn')
    expect(buttons[0].attributes('aria-pressed')).toBe('true')
    expect(buttons[0].classes()).toContain('watched')
    expect(buttons[1].attributes('aria-pressed')).toBe('false')
    expect(buttons[1].classes()).not.toContain('watched')
  })

  it('點 ❤️ 加入追蹤：❤️ 實心、不觸發 select、下拉保持顯示', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const heart = wrapper.find('.search-result-item .watchlist-btn')
    await heart.trigger('mousedown')
    await heart.trigger('click')

    const { isWatched } = useWatchlist()
    expect(isWatched('2330')).toBe(true)
    expect(wrapper.emitted('select')).toBeUndefined()
    expect(wrapper.find('.search-results').exists()).toBe(true)
  })

  it('再次點 ❤️ 移除追蹤（回到空心）', async () => {
    const { toggle } = useWatchlist()
    toggle('2330')

    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    await wrapper.find('.search-result-item .watchlist-btn').trigger('click')

    const { isWatched } = useWatchlist()
    expect(isWatched('2330')).toBe(false)
  })

  it('❤️ 上的 mousedown 被 WatchlistButton 攔截，不冒泡觸發結果列 select', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const btnEl = wrapper.find('.search-result-item .watchlist-btn').element as HTMLButtonElement
    // 手動派發可冒泡的 mousedown（模擬真實瀏覽器事件流）
    btnEl.dispatchEvent(new MouseEvent('mousedown', { bubbles: true, cancelable: true }))

    expect(wrapper.emitted('select')).toBeUndefined()
  })

  it('點結果列（名稱區）仍觸發 select（導航行為不變）', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const rows = wrapper.findAll('.search-result-item')
    await rows[1].trigger('mousedown')

    const selectEvents = wrapper.emitted('select')
    expect(selectEvents).toBeDefined()
    expect(selectEvents?.[0]?.[0]).toEqual({ code: '2317', name: '鴻海' })
  })

  it('搜尋無結果顯示「找不到符合的證券」', async () => {
    const wrapper = mountSearchBar('XXXXX', [])
    await openDropdown(wrapper)

    expect(wrapper.text()).toContain('找不到符合的證券')
  })

  it('按 Escape 關閉下拉', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)
    expect(wrapper.find('.search-results').exists()).toBe(true)

    await wrapper.find('.search-input').trigger('keydown', { key: 'Escape' })

    expect(wrapper.find('.search-results').exists()).toBe(false)
  })

  it('輸入框 blur 後關閉下拉（既有行為回歸）', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)
    expect(wrapper.find('.search-results').exists()).toBe(true)

    await wrapper.find('.search-input').trigger('blur')
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(wrapper.find('.search-results').exists()).toBe(false)
  })

  it('點 ❤️ 後下拉在 blur 延遲窗口後仍保持顯示', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const heart = wrapper.find('.search-result-item .watchlist-btn')
    await heart.trigger('mousedown')
    await heart.trigger('click')
    await new Promise(resolve => setTimeout(resolve, 200))

    expect(wrapper.find('.search-results').exists()).toBe(true)
  })

  it('注入的 ❤️ 為 sm 尺寸（配合 mobile 觸控目標覆寫）', async () => {
    const wrapper = mountSearchBar()
    await openDropdown(wrapper)

    const heart = wrapper.find('.search-result-item .watchlist-btn')
    expect(heart.classes()).toContain('watchlist-btn--sm')
  })
})