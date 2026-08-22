import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import StockView from '../views/StockView.vue'
import WatchlistPage from '../views/WatchlistView.vue'

const router = createRouter({
  // 使用 history mode
  history: createWebHistory(),
  routes: [
    {
      path: '/',
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
