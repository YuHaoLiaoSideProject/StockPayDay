<script setup lang="ts">
/**
 * LandingView — 商業化首頁
 *
 * Hero → How It Works + CTA → Footer
 */

function scrollToSection(id: string) {
  document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
}
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
          <a href="#how-it-works" class="landing-btn landing-btn-secondary" @click.prevent="scrollToSection('how-it-works')">了解更多 ↓</a>
        </div>
        <p class="social-proof">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="#f59e0b" stroke="none" aria-hidden="true"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>
          已追蹤超過 2,000 支股票的配息時程
        </p>
      </div>

      <!-- Hero Visual: Calendar Mockup -->
      <div class="hero-visual" aria-hidden="true">
        <div class="hero-mockup">
          <div class="mockup-header">
            <div class="mockup-dots"><span></span><span></span><span></span></div>
            <span class="mockup-title">StockPayDay++</span>
          </div>
          <div class="mockup-calendar">
            <div class="mockup-month">2026 年 8 月</div>
            <div class="mockup-weekdays">
              <span>日</span><span>一</span><span>二</span><span>三</span><span>四</span><span>五</span><span>六</span>
            </div>
            <div class="mockup-grid">
              <div class="mockup-day"><span>18</span></div>
              <div class="mockup-day"><span>19</span></div>
              <div class="mockup-day today"><span>20</span></div>
              <div class="mockup-day"><span>21</span></div>
              <div class="mockup-day"><span>22</span></div>
              <div class="mockup-day div-day"><span>23</span><div class="mockup-div"></div></div>
              <div class="mockup-day div-day watched"><span>24</span><div class="mockup-div w"></div><div class="mockup-div"></div></div>
              <div class="mockup-day div-day"><span>25</span><div class="mockup-div w"></div></div>
              <div class="mockup-day"><span>26</span></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section id="how-it-works" class="how-it-works">
      <div class="section-header">
        <h2>使用方式超簡單</h2>
        <p>三個步驟，開始掌握你的配息</p>
      </div>
      <div class="steps">
        <div class="step-card">
          <div class="step-number">1</div>
          <h3>搜尋股票</h3>
          <p>輸入代號或名稱，快速找到標的</p>
          <div class="step-visual">
            <div class="mini-search">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
              <span>搜尋股票</span>
            </div>
            <div class="mini-stock">
              <span class="mini-stock-code">2330</span>
              <span class="mini-stock-name">台積電</span>
            </div>
          </div>
        </div>
        <div class="step-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="step-card">
          <div class="step-number">2</div>
          <h3>加入追蹤</h3>
          <p>點擊愛心，加入你的追蹤清單</p>
          <div class="step-visual">
            <div class="mini-stock mini-stock--watched">
              <span class="mini-stock-code">2330</span>
              <span class="mini-stock-name">台積電</span>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#ef4444" stroke="#ef4444" stroke-width="2" aria-hidden="true"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
            </div>
          </div>
        </div>
        <div class="step-arrow" aria-hidden="true">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
            <line x1="5" y1="12" x2="19" y2="12"/>
            <polyline points="12 5 19 12 12 19"/>
          </svg>
        </div>
        <div class="step-card">
          <div class="step-number">3</div>
          <h3>掌握時程</h3>
          <p>行事曆自動標示配息日期</p>
          <div class="step-visual">
            <div class="mini-cal">
              <div class="mini-cal-month">8 月 25 日</div>
              <div class="mini-cal-dots">
                <span class="mini-dot mini-dot--normal"></span>
                <span class="mini-dot mini-dot--watched"></span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- CTA（整合進 How It Works 底部）-->
      <div class="cta-inline">
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
      </div>
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
        <a href="#how-it-works" @click.prevent="scrollToSection('how-it-works')">功能介紹</a>
        <a href="#/app">開始使用</a>
        <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
      </div>
      <p class="footer-copy">© 2026 StockPayDay++ · MIT License</p>
    </footer>
  </div>
</template>
