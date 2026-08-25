import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, type Router } from 'vue-router'
import App from '../../App.vue'
import { useWatchlist } from '../../composables/useWatchlist'

let router: Router

beforeEach(async () => {
  localStorage.clear()
  useWatchlist().reset()
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true,
    json: () => Promise.resolve([]),
  }))
  router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div>home</div>' } },
      { path: '/watchlist', component: { template: '<div>watchlist page</div>' } },
      { path: '/stock/:code', component: { template: '<div>stock page</div>' } },
    ],
  })
  await router.push('/')
})

async function mountApp(): Promise<VueWrapper> {
  const wrapper = mount(App, { global: { plugins: [router] } })
  await flushPromises()
  return wrapper
}

describe('App 導覽列徽章 — 功能 001（追蹤任意股票）', () => {
  it('無追蹤時不顯示徽章', async () => {
    const wrapper = await mountApp()

    expect(wrapper.find('.watchlist-badge').exists()).toBe(false)
  })

  it('徽章數字隨追蹤增減（+1 / -1）', async () => {
    const { add, remove } = useWatchlist()
    const wrapper = await mountApp()

    add('2330')
    await flushPromises()
    expect(wrapper.find('.watchlist-badge').text()).toBe('1')

    add('2317')
    await flushPromises()
    expect(wrapper.find('.watchlist-badge').text()).toBe('2')

    remove('2330')
    await flushPromises()
    expect(wrapper.find('.watchlist-badge').text()).toBe('1')
  })

  it('切換頁面時追蹤狀態與徽章保持一致（module-level singleton）', async () => {
    const { add } = useWatchlist()
    add('2330')
    const wrapper = await mountApp()
    expect(wrapper.find('.watchlist-badge').text()).toBe('1')

    await router.push('/watchlist')
    await flushPromises()
    expect(wrapper.find('.watchlist-badge').text()).toBe('1')

    await router.push('/stock/2330')
    await flushPromises()
    expect(wrapper.find('.watchlist-badge').text()).toBe('1')
  })
})


