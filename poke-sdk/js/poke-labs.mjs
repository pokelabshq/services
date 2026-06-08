/**
 * Poke Labs SDK for JavaScript (ESM) — Zero dependencies.
 * Works in Node 18+, Deno, Bun, Cloudflare Workers.
 *
 * Usage:
 *   import { Client } from './poke-labs.mjs'
 *   const c = new Client('http://localhost:8750')
 *   console.log(await c.preview('https://github.com'))
 */
export class Client {
  constructor(baseUrl = 'http://localhost:8750', apiKey = null) {
    this.base = baseUrl.replace(/\/$/, '')
    this.key = apiKey
  }

  async _req(method, path, data) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } }
    if (data) opts.body = JSON.stringify(data)
    if (this.key) opts.headers.Authorization = `Bearer ${this.key}`
    const r = await fetch(`${this.base}${path}`, opts)
    return { status: r.status, data: await r.json() }
  }

  health()  { return this._req('GET', '/api/health') }
  usage()   { return this._req('GET', '/api/usage') }
  preview(url) { return this._req('POST', '/preview/api/preview', { url }) }
  identity()   { return this._req('GET', '/id/api/identity') }
  agents()     { return this._req('GET', '/id/api/agents') }
  agent(name)  { return this._req('GET', `/id/api/agents/${name}`) }
  reputation(name) { return this._req('GET', `/id/api/reputation/${name}`) }
  feed(params = {}) {
    const q = new URLSearchParams(params).toString()
    return this._req('GET', `/id/api/feed${q ? '?'+q : ''}`)
  }
  event(service, type, message, meta) {
    return this._req('POST', '/id/api/events', { service, type, message, meta })
  }
}
