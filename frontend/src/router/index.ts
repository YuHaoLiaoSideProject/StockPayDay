import { createRouter, createWebHashHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'
import HomeView from '../views/HomeView.vue'
import StockView from '../views/StockView.vue'
import WatchlistPage from '../views/WatchlistView.vue'

const router = createRouter({
  // 使用 hash mode 以相容 GitHub Pages 靜態部署
  history: createWebHashHistory(),
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
