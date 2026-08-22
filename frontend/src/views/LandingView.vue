<script setup lang="ts">
/**
 * LandingView — 首頁（README 風格）
 *
 * 顯示專案介紹，引導用戶進入股票配息行事曆。
 */
import { useRouter } from 'vue-router'

const router = useRouter()

function goToApp() {
  router.push('/app')
}
</script>

<template>
  <div class="landing">
    <div class="landing-container">
      <h1>📅 StockPayDay++</h1>
      <p class="subtitle">提醒投資人股利發放日期的工具。</p>

      <section>
        <h2>✨ 功能</h2>
        <ul>
          <li><strong>Crawler</strong>：從臺灣證券交易所（TWSE）抓取股利發放資料</li>
          <li><strong>Processor</strong>：處理原始資料、產生靜態 JSON API</li>
          <li><strong>Frontend</strong>：Vue 3 + Vite 靜態站台</li>
        </ul>
      </section>

      <section>
        <h2>🚀 立即使用</h2>
        <button class="cta" @click="goToApp">進入股票配息行事曆 →</button>
      </section>

      <section>
        <h2>⚙️ 快速開始</h2>
        <p><strong>後端</strong></p>
        <pre><code>python -m venv venv
source venv/bin/activate
pip install -r requirements.txt</code></pre>
        <p><strong>前端</strong></p>
        <pre><code>cd frontend
npm install
npm run dev</code></pre>
      </section>

      <section>
        <h2>🔄 自動部署</h2>
        <ul>
          <li>Push 到 <code>master</code> → 自動建構並部署至 GitHub Pages</li>
          <li>每日排程（UTC 08:00）→ 自動爬取最新資料</li>
        </ul>
      </section>

      <footer>
        StockPayDay++ &copy; 2026 · MIT License
      </footer>
    </div>
  </div>
</template>

<style scoped>
.landing {
  min-height: calc(100vh - 60px);
  background: var(--color-bg, #0d1117);
  color: var(--color-text, #e6edf3);
}

.landing-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 3rem 1.5rem;
}

h1 {
  font-size: 2.2rem;
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--color-text-muted, #8b949e);
  font-size: 1.1rem;
  margin-bottom: 2.5rem;
}

h2 {
  font-size: 1.4rem;
  margin-top: 2.5rem;
  margin-bottom: 1rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid var(--color-border, #30363d);
}

ul {
  list-style: none;
  margin-bottom: 1rem;
}

ul li {
  padding: 0.3rem 0;
  padding-left: 1.5rem;
  position: relative;
}

ul li::before {
  content: "▸";
  position: absolute;
  left: 0;
  color: var(--color-green, #3fb950);
}

strong {
  color: var(--color-text, #e6edf3);
}

code {
  background: var(--color-code-bg, #1c2128);
  padding: 0.15em 0.4em;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: "SFMono-Regular", Consolas, monospace;
}

pre {
  background: var(--color-code-bg, #1c2128);
  border: 1px solid var(--color-border, #30363d);
  border-radius: 6px;
  padding: 1rem 1.2rem;
  overflow-x: auto;
  margin-bottom: 1rem;
  font-size: 0.88em;
  line-height: 1.5;
}

pre code {
  background: none;
  padding: 0;
}

.cta {
  display: inline-block;
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: var(--color-accent, #58a6ff);
  color: var(--color-bg, #0d1117);
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}

.cta:hover {
  background: var(--color-accent-hover, #79c0ff);
}

footer {
  margin-top: 4rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--color-border, #30363d);
  color: var(--color-text-muted, #8b949e);
  font-size: 0.85rem;
  text-align: center;
}
</style>
