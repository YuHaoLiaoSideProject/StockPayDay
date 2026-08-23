/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

interface ImportMetaEnv {
  /** Cloudflare Worker URL（kvdb-proxy）；未設定時使用預設 placeholder */
  readonly VITE_SYNC_WORKER_URL: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
