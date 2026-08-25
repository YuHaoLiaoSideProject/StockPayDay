import { createRouter, createWebHashHistory } from 'vue-router'
import LandingView from '../views/LandingView.vue'

// Lazy loading：避免首頁載入時觸發 useWatchlistSync 的 module-level 副作用
const HomeView = () => import('../views/HomeView.vue')
const StockView = () => import('../views/StockView.vue')
const WatchlistPage = () => import('../views/WatchlistView.vue')

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
      path: '/landing',
      name: 'landing-alt',
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
