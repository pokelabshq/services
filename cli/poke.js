#!/usr/bin/env node
const http = require('http');
const fs = require('fs');
const path = require('path');

const WALLET = '0xca3d86e4EDE205E6d72496BC2919c88b994B6beF';
const SERVICES = [
  { name: 'link-preview', port: 8765, emoji: '🔗' },
  { name: 'pokelabs-site', port: 8766, emoji: '🏠' },
  { name: 'poke-hub', port: 8775, emoji: '🐾' },
  { name: 'skills-marketplace', port: 8781, emoji: '🛍' },
];
const SKILLS = [
  { id: 'link-preview-api', name: 'Link Preview API', category: 'api' },
  { id: 'poke-hub', name: 'Poke Hub', category: 'github' },
  { id: 'poke-bot', name: 'Poke Bot', category: 'github' },
  { id: 'github-reply-bot', name: 'GitHub Reply Bot', category: 'github' },
  { id: 'council', name: 'AI Council', category: 'automation' },
  { id: 'auto-merge-pr', name: 'Auto-Merge Dependabot', category: 'github' },
  { id: 'pokelabs-site', name: 'Poke Labs Site', category: 'web' },
];

function httpGet(url) {
  return new Promise((resolve, reject) => {
    http.get(url, { timeout: 5000 }, res => {
      let d = ''; res.on('data', c => d += c); res.on('end', () => resolve({ ok: res.statusCode < 400, data: d }));
    }).on('error', () => resolve({ ok: false }));
  });
}

async function cmdStatus() {
  console.log('\n🐾 Poke Labs CLI — Status\n');
  for (const s of SERVICES) {
    const h = await httpGet(`http://localhost:${s.port}/api/health`);
    const icon = h.ok ? '🟢' : '🔴';
    const detail = h.ok ? JSON.parse(h.data).v : 'offline';
    console.log(`  ${icon} ${s.name} (:${s.port}) — v${detail}`);
  }
  console.log(`\n  Wallet: ${WALLET}\n`);
}

async function cmdSkills() {
  console.log('\n🐾 Poke Labs CLI — Skills\n');
  for (const s of SKILLS) console.log(`  ${s.id}\t[${s.category}]\t${s.name}`);
  console.log(`\n  Install: poke install <id>\n`);
}

async function cmdInstall(id) {
  const skill = SKILLS.find(s => s.id === id);
  if (!skill) { console.log(`Skill not found: ${id}`); process.exit(1); }
  const dir = path.join(process.env.HOME, '.pokelabs', 'skills', id);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'SKILL.md'), `# ${skill.name}\nCategory: ${skill.category}\n`);
  console.log(`✅ Installed ${skill.name} → ${dir}`);
}

async function cmdPreview(url) {
  const post = JSON.stringify({ url });
  const result = await new Promise((resolve) => {
    const req = http.request({ hostname: 'localhost', port: 8765, path: '/api/preview', method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Content-Length': post.length }, timeout: 10000 },
      res => { let d = ''; res.on('data', c => d += c); res.on('end', () => resolve(d)); });
    req.on('error', () => resolve(null));
    req.write(post); req.end();
  });
  console.log(result ? JSON.stringify(JSON.parse(result), null, 2) : 'Link Preview API unavailable');
}

async function main() {
  const [, , cmd, arg] = process.argv;
  if (cmd === 'status') await cmdStatus();
  else if (cmd === 'skills') await cmdSkills();
  else if (cmd === 'install') await cmdInstall(arg);
  else if (cmd === 'preview') await cmdPreview(arg || 'https://pokelabs.org');
  else { console.log('Usage: poke <status|skills|install|preview> [arg]'); }
}
main();
