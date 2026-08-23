/**
 * kvdb-proxy — Cloudflare Worker（Phase 9 跨裝置追蹤清單同步）
 *
 * 職責：作為前端與 kvdb.io 之間的 proxy，負責：
 * 1. 接收前端 POST { email } → 建立 kvdb bucket
 * 2. 設定 bucket 的 signing_key
 * 3. 產生 access token（限定 prefix: user:me:，權限 read,write，TTL 90 天）
 * 4. 回傳 { access_token, bucket_id } 給前端
 *
 * 安全性：SECRET_KEY / SIGNING_KEY 僅存在 Worker 環境變數中，前端永遠看不到。
 *
 * API：
 *   POST /
 *   Body: { "email": "user@example.com" }
 *   Response: { "access_token": "...", "bucket_id": "..." }
 *
 *   其他方法回傳 405 Method Not Allowed
 */

interface Env {
  SECRET_KEY: string
  SIGNING_KEY: string
  KVDB_BASE: string
}

// ── IP 速率限制（免費方案可用，記憶體級，cold start 後重置）──
// 每個 IP 每小時最多 5 次建立帳號（防止濫用建立大量 bucket）
const RATE_LIMIT_MAX = 5
const RATE_LIMIT_WINDOW_MS = 3_600_000 // 1 小時
const rateLimitMap = new Map<string, { count: number; resetAt: number }>()

function checkRateLimit(ip: string): { ok: boolean; remaining: number } {
  const now = Date.now()
  const entry = rateLimitMap.get(ip)
  if (!entry || now > entry.resetAt) {
    rateLimitMap.set(ip, { count: 1, resetAt: now + RATE_LIMIT_WINDOW_MS })
    return { ok: true, remaining: RATE_LIMIT_MAX - 1 }
  }
  if (entry.count >= RATE_LIMIT_MAX) {
    return { ok: false, remaining: 0 }
  }
  entry.count++
  return { ok: true, remaining: RATE_LIMIT_MAX - entry.count }
}

// 定期清理過期條目（避免記憶體洩漏）
setInterval(() => {
  const now = Date.now()
  for (const [ip, entry] of rateLimitMap) {
    if (now > entry.resetAt) rateLimitMap.delete(ip)
  }
}, 60_000)

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // CORS headers for frontend calls
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    }

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders })
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders })
    }

    let email: string
    try {
      const body = await request.json() as { email?: string }
      email = body.email?.trim() ?? ''
    } catch {
      return new Response('Invalid JSON', { status: 400, headers: corsHeaders })
    }

    if (!email) {
      return new Response('Email required', { status: 400, headers: corsHeaders })
    }

    // Basic email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return new Response('Invalid email format', { status: 400, headers: corsHeaders })
    }

    // IP 速率限制：每 IP 每小時最多 5 次建立帳號
    const clientIp = request.headers.get('cf-connecting-ip') || request.headers.get('x-forwarded-for')?.split(',')[0]?.trim() || 'unknown'
    const { ok: rateOk, remaining } = checkRateLimit(clientIp)
    if (!rateOk) {
      return new Response(
        JSON.stringify({ error: 'Rate limit exceeded. Please try again later.' }),
        {
          status: 429,
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
            'Retry-After': '3600',
          },
        }
      )
    }

    const kvdbBase = env.KVDB_BASE || 'https://kvdb.io'
    const authHeader = `Basic ${btoa(env.SECRET_KEY + ':')}`

    try {
      // 1. 建立 kvdb bucket
      const bucketRes = await fetch(kvdbBase, {
        method: 'POST',
        body: new URLSearchParams({ email }),
      })

      if (!bucketRes.ok) {
        const text = await bucketRes.text()
        return new Response(
          JSON.stringify({ error: `Failed to create bucket: ${bucketRes.status} ${text}` }),
          { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      const bucket = await bucketRes.json() as { id: string }

      // 2. 設定 signing_key
      const signingRes = await fetch(`${kvdbBase}/${bucket.id}`, {
        method: 'PATCH',
        headers: { Authorization: authHeader },
        body: new URLSearchParams({ signing_key: env.SIGNING_KEY }),
      })

      if (!signingRes.ok) {
        const text = await signingRes.text()
        return new Response(
          JSON.stringify({ error: `Failed to set signing key: ${signingRes.status} ${text}` }),
          { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      // 3. 產生 access token（prefix: user:me:，權限 read,write，TTL 90 天）
      const tokenRes = await fetch(`${kvdbBase}/${bucket.id}/tokens/`, {
        method: 'POST',
        headers: { Authorization: authHeader },
        body: new URLSearchParams({
          prefix: 'user:me:',
          permissions: 'read,write',
          ttl: '7776000', // 90 天
        }),
      })

      if (!tokenRes.ok) {
        const text = await tokenRes.text()
        return new Response(
          JSON.stringify({ error: `Failed to create token: ${tokenRes.status} ${text}` }),
          { status: 502, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
        )
      }

      const token = await tokenRes.json() as { access_token: string }

      // 4. 回傳 token + bucket_id
      return new Response(
        JSON.stringify({
          access_token: token.access_token,
          bucket_id: bucket.id,
        }),
        {
          status: 200,
          headers: {
            ...corsHeaders,
            'Content-Type': 'application/json',
            'X-RateLimit-Remaining': String(remaining),
          },
        }
      )
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Internal error'
      return new Response(
        JSON.stringify({ error: message }),
        { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }
  },
}
