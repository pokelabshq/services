/**
 * Poke Labs SDK for JavaScript (CJS/UMD) — Zero dependencies.
 * Works everywhere: Node, browsers, bundlers.
 */
(function(root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory()
  else root.PokeLabs = factory()
})(typeof self !== 'undefined' ? self : this, function() {
  'use strict'

  class Client {
    constructor(baseUrl, apiKey) {
      this.base = (baseUrl || 'http://localhost:8750').replace(/\/$/, '')
      this.key = apiKey || null
    }
    _req(method, path, data) {
      return new Promise(function(resolve, reject) {
        var xhr = new XMLHttpRequest()
        xhr.open(method, this.base + path, true)
        xhr.setRequestHeader('Content-Type', 'application/json')
        if (this.key) xhr.setRequestHeader('Authorization', 'Bearer ' + this.key)
        xhr.onload = function() {
          try { resolve({ status: xhr.status, data: JSON.parse(xhr.responseText) }) }
          catch(e) { resolve({ status: xhr.status, data: xhr.responseText }) }
        }
        xhr.onerror = function() { reject(new Error('Network error')) }
        xhr.send(data ? JSON.stringify(data) : null)
      }.bind(this))
    }
    health() { return this._req('GET', '/api/health') }
    usage() { return this._req('GET', '/api/usage') }
    preview(url) { return this._req('POST', '/preview/api/preview', { url }) }
    identity() { return this._req('GET', '/id/api/identity') }
    agents() { return this._req('GET', '/id/api/agents') }
    agent(name) { return this._req('GET', '/id/api/agents/' + name) }
    reputation(name) { return this._req('GET', '/id/api/reputation/' + name) }
    feed(params) {
      var q = ''
      if (params) {
        var parts = []
        Object.keys(params).forEach(function(k) { if (params[k] != null) parts.push(k + '=' + encodeURIComponent(params[k])) })
        q = parts.length ? '?' + parts.join('&') : ''
      }
      return this._req('GET', '/id/api/feed' + q)
    }
    event(service, type, message, meta) {
      return this._req('POST', '/id/api/events', { service: service, type: type, message: message, meta: meta })
    }
  }

  return { Client: Client }
})
