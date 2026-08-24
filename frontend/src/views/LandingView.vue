<script setup lang="ts">
/**
 * LandingView — 商業化首頁
 *
 * Hero → How It Works → CTA → Footer
 */
</script>

<template>
  <div class="landing">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-content">
        <div class="hero-icon" aria-hidden="true">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
        </div>
        <h1>你的股利，不再錯過。</h1>
        <p class="hero-subtitle">StockPayDay 幫你掌握每一筆配息時程。<br class="hero-br-desktop">一目了然的行事曆，讓你精準掌握投資節奏。</p>
        <div class="hero-actions">
          <a href="#/app" class="landing-btn landing-btn-primary">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
              <line x1="16" y1="2" x2="16" y2="6"/>
              <line x1="8" y1="2" x2="8" y2="6"/>
              <line x1="3" y1="10" x2="21" y2="10"/>
            </svg>
            立即查看配息行事曆
          </a>
          <a href="#how-it-works" class="landing-btn landing-btn-secondary">了解更多 ↓</a>
        </div>
        <p class="social-proof">
          <span class="star" aria-hidden="true">★</span>
          已追蹤超過 2,000 支股票的配息時程
        </p>
      </div>
    </section>

    <!-- How It Works -->
    <section id="how-it-works" class="how-it-works">
      <div class="section-header">
        <h2>使用方式超簡單</h2>
        <p>三個步驟，開始掌握你的配息</p>
      </div>
      <div class="steps">
        <div class="step">
          <div class="step-number">1</div>
          <h3>搜尋股票</h3>
          <p>輸入代號或名稱，快速找到標的</p>
        </div>
        <div class="step-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="step">
          <div class="step-number">2</div>
          <h3>加入追蹤</h3>
          <p>點擊愛心，加入你的追蹤清單</p>
        </div>
        <div class="step-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="step">
          <div class="step-number">3</div>
          <h3>掌握時程</h3>
          <p>行事曆自動標示配息日期</p>
        </div>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="cta-section">
      <h2>準備好掌握了嗎？</h2>
      <a href="#/app" class="landing-btn landing-btn-primary landing-btn-large">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        開始使用 StockPayDay
      </a>
      <p class="cta-note">免費使用 · 無需註冊 · 資料每日更新</p>
    </section>

    <!-- Footer -->
    <footer class="landing-footer">
      <div class="footer-brand">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
          <line x1="16" y1="2" x2="16" y2="6"/>
          <line x1="8" y1="2" x2="8" y2="6"/>
          <line x1="3" y1="10" x2="21" y2="10"/>
        </svg>
        <span>StockPayDay++</span>
      </div>
      <p class="footer-desc">提醒投資人股利發放日期的工具</p>
      <div class="footer-links">
        <a href="#how-it-works">功能介紹</a>
        <a href="#/app">開始使用</a>
        <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
      </div>
      <p class="footer-copy">© 2026 StockPayDay++ · MIT License</p>
    </footer>
  </div>
</template>
