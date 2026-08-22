import { createRouter, createWebHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'
import HomeView from '../views/HomeView.vue'
import StockView from '../views/StockView.vue'
import WatchlistPage from '../views/WatchlistView.vue'

const router = createRouter({
  // 使用 history mode（GitHub Pages 需要 404.html fallback）
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: LandingView,
    },
    {
      path: '/app',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/stock/:code',
      name: 'stock',
      component: StockView,
    },
    {
      path: '/watchlist',
      name: 'watchlist',
      component: WatchlistPage,
    },
  ],
})

export default router
