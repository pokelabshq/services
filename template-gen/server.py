#!/usr/bin/env python3
"""
Landing Page Generator v1
Generates beautiful landing pages from JSON config.
No dependencies — stdlib only.
"""

import http.server, json, re, os
from datetime import datetime

PORT = 8710

# HTML template with placeholders
PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:system-ui,-apple-system,sans-serif;background:{bg_color};color:{text_color};line-height:1.6}}
.container{{max-width:1100px;margin:0 auto;padding:0 24px}}
nav{{padding:20px 0;display:flex;justify-content:space-between;align-items:center}}
nav .logo{{font-size:1.4rem;font-weight:800;color:{accent_color}}}
nav a{{color:{text_color};text-decoration:none;margin-left:24px;opacity:0.8}}
nav a:hover{{opacity:1}}
.hero{{padding:80px 0;text-align:center}}
.hero h1{{font-size:clamp(2rem,5vw,3.5rem);font-weight:800;margin-bottom:16px;background:linear-gradient(135deg,{accent_color},{accent2_color});-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.hero p{{font-size:1.2rem;opacity:0.7;max-width:600px;margin:0 auto 32px}}
.cta{{display:inline-block;padding:14px 36px;background:{accent_color};color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.1rem;transition:transform .2s,box-shadow .2s}}
.cta:hover{{transform:translateY(-2px);box-shadow:0 8px 30px {accent_color}40}}
.features{{padding:60px 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px}}
.card{{background:{card_bg};border-radius:16px;padding:32px;border:1px solid {border_color}}}
.card h3{{font-size:1.3rem;margin-bottom:8px;color:{accent_color}}}
.card p{{opacity:0.7;font-size:0.95rem}}
.pricing{{padding:60px 0;text-align:center}}
.pricing h2{{font-size:2rem;margin-bottom:40px}}
.pricing-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px}}
.price-card{{background:{card_bg};border-radius:16px;padding:32px;border:2px solid {border_color}}}
.price-card.featured{{border-color:{accent_color}}}
.price-card h3{{font-size:1.2rem;margin-bottom:8px}}
.price-card .price{{font-size:2.5rem;font-weight:800;color:{accent_color};margin:16px 0}}
.price-card .price span{{font-size:1rem;opacity:0.5}}
.price-card ul{{list-style:none;padding:0;margin:24px 0;text-align:left}}
.price-card li{{padding:8px 0;opacity:0.8;border-bottom:1px solid {border_color}}
.footer{{padding:40px 0;text-align:center;opacity:0.5;font-size:0.9rem;border-top:1px solid {border_color};margin-top:40px}}
</style>
</head>
<body>
<nav><div class="container" style="display:flex;justify-content:space-between;align-items:center;width:100%">
<div class="logo">{nav_logo}</div>
<div>{nav_links}</div>
</div></nav>

<section class="hero"><div class="container">
<h1>{hero_title}</h1>
<p>{hero_subtitle}</p>
{hero_cta}
</div></section>

<section class="features"><div class="container">
<div class="features-grid">{features}</div>
</div></section>

{pricing_section}

<footer class="footer"><div class="container">
<p>© {year} {footer_text}. Built with 🐾 Poke Labs</p>
</div></footer>
</body>
</html>"""

# Creator web UI
CREATOR_HTML = """<!DOCTYPE html>
<html><head><title>Landing Page Creator | Poke Labs</title>
<style>
body{font-family:system-ui,sans-serif;max-width:900px;margin:40px auto;padding:0 20px;background:#0f0f23;color:#e0e0e0}
h1{color:#a78bfa;margin-bottom:4px}
.sub{color:#666;margin-bottom:32px}
label{display:block;margin:16px 0 4px;font-weight:600;color:#a78bfa;font-size:0.85rem;text-transform:uppercase;letter-spacing:0.5px}
input,textarea,select{width:100%;padding:10px 14px;border:1px solid #333;border-radius:8px;background:#1a1a2e;color:#e0e0e0;font-size:1rem}
textarea{min-height:80px;resize:vertical}
.row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.btn{margin-top:24px;padding:14px 32px;background:#a78bfa;color:#fff;border:none;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer}
.btn:hover{background:#8b5cf6}
.preview{display:none;margin-top:32px}
.preview iframe{width:100%;height:600px;border:1px solid #333;border-radius:8px;background:#fff}
.tabs{display:flex;gap:8px;margin-top:24px}
.tab{padding:8px 20px;background:#1a1a2e;border:1px solid #333;border-radius:8px;cursor:pointer;color:#888}
.tab.active{background:#a78bfa;color:#fff;border-color:#a78bfa}
</style></head>
<body>
<h1>🐾 Landing Page Creator</h1>
<p class="sub">Build beautiful landing pages in seconds. Fill in your details, generate, and deploy.</p>

<form id="form">
<div class="row">
<div><label>Brand / Company Name</label><input name="nav_logo" value="MyBrand"></div>
<div><label>Page Title (meta)</label><input name="title" value="MyBrand — Ship Fast"></div>
</div>
<div class="row">
<div><label>Hero Title</label><input name="hero_title" value="Build something amazing"></div>
<div><label>Hero Subtitle</label><input name="hero_subtitle" value="The modern platform for teams who ship fast."></div>
</div>
<label>Description (meta)</label><input name="description" value="The modern platform for teams who ship fast.">
<label>Hero CTA Text</label><input name="hero_cta_text" value="Get Started Free">

<div class="row">
<div><label>Accent Color</label><input name="accent_color" type="color" value="#a78bfa"></div>
<div><label>Accent 2 Color</label><input name="accent2_color" type="color" value="#f472b6"></div>
</div>
<div class="row">
<div><label>Background Color</label><input name="bg_color" type="color" value="#0f0f23"></div>
<div><label>Text Color</label><input name="text_color" type="color" value="#e0e0e0"></div>
</div>

<h2 style="margin-top:32px;color:#a78bfa">Features</h2>
<div id="features-editor">
<div class="feature-row">
<div class="row">
<div><label>Feature 1 Title</label><input name="feat_title_0" value="Lightning Fast"></div>
<div><label>Feature 1 Desc</label><input name="feat_desc_0" value="Optimized for speed from day one."></div>
</div>
</div>
<div class="feature-row">
<div class="row">
<div><label>Feature 2 Title</label><input name="feat_title_1" value="Developer First"></div>
<div><label>Feature 2 Desc</label><input name="feat_desc_1" value="TypeScript, great docs, and clean APIs."></div>
</div>
</div>
<div class="feature-row">
<div class="row">
<div><label>Feature 3 Title</label><input name="feat_title_2" value="Open Source"></div>
<div><label>Feature 3 Desc</label><input name="feat_desc_2" value="MIT licensed. Fork it, ship it, own it."></div>
</div>
</div>
</div>

<h2 style="margin-top:32px;color:#a78bfa">Pricing (optional)</h2>
<div class="row">
<div><label>Show Pricing Section?</label><select name="show_pricing"><option value="yes">Yes</option><option value="no">No</option></select></div>
<div><label>Footer Text</label><input name="footer_text" value="MyBrand Inc."></div>
</div>

<button type="submit" class="btn" id="genBtn">Generate Landing Page</button>
</form>

<div class="preview" id="preview">
<div class="tabs">
<div class="tab active" onclick="showTab('preview',this)">Preview</div>
<div class="tab" onclick="showTab('html',this)">HTML Source</div>
</div>
<iframe id="preview-frame"></iframe>
<pre id="html-source" style="display:none;background:#1a1a2e;padding:16px;border-radius:8px;overflow:auto;max-height:600px;font-size:0.85em"></pre>
</div>

<script>
function showTab(tab,el){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('preview-frame').style.display=tab==='preview'?'block':'none';
  document.getElementById('html-source').style.display=tab==='html'?'block':'none';
}

document.getElementById('form').onsubmit = async (e) => {
  e.preventDefault();
  const btn = document.getElementById('genBtn');
  btn.textContent = 'Generating...';
  btn.disabled = true;
  const form = new FormData(e.target);
  const obj = {};
  for (const [k,v] of form.entries()) obj[k] = v;
  // Collect features
  obj.features = [];
  for (let i = 0; i < 6; i++) {
    if (obj['feat_title_'+i]) {
      obj.features.push({title: obj['feat_title_'+i], desc: obj['feat_desc_'+i]||''});
    }
  }
  try {
    const resp = await fetch('/api/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(obj)
    });
    const data = await resp.json();
    if (data.html) {
      document.getElementById('preview').style.display = 'block';
      const frame = document.getElementById('preview-frame');
      frame.srcdoc = data.html;
      document.getElementById('html-source').textContent = data.html;
      document.getElementById('preview').scrollIntoView({behavior:'smooth'});
    } else {
      alert('Error: ' + (data.error || 'Unknown'));
    }
  } catch(e) {
    alert('Failed: ' + e.message);
  }
  btn.textContent = 'Generate Landing Page';
  btn.disabled = false;
};
</script></body></html>"""

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        if self.path == "/" or self.path == "/creator":
            resp = CREATOR_HTML
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(resp.encode())
            return

        if self.path == "/api/health":
            self.send_json(200, {"ok": True, "v": 1, "service": "landing-page-gen"})
            return

        self.send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/api/generate":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            try:
                html = self.generate_page(body)
                self.send_json(200, {"html": html})
            except Exception as e:
                self.send_json(500, {"error": str(e)})
            return

        self.send_json(404, {"error": "not found"})

    def generate_page(self, cfg):
        accent = cfg.get("accent_color", "#a78bfa")
        accent2 = cfg.get("accent2_color", "#f472b6")
        bg = cfg.get("bg_color", "#0f0f23")
        text = cfg.get("text_color", "#e0e0e0")
        card_bg = cfg.get("card_bg", "#1a1a2e")
        border = cfg.get("border_color", "#333")

        # Nav links
        nav_links = ""
        for label, href in [("Features", "#features"), ("Pricing", "#pricing"), ("GitHub", "https://github.com")]:
            nav_links += f'<a href="{href}" style="color:{text};text-decoration:none;margin-left:24px;opacity:0.8">{label}</a>'

        # Hero CTA
        cta_text = cfg.get("hero_cta_text", "Get Started")
        hero_cta = f'<a href="#pricing" class="cta" style="display:inline-block;padding:14px 36px;background:{accent};color:#fff;border-radius:8px;text-decoration:none;font-weight:600;font-size:1.1rem">{cta_text}</a>'

        # Features
        features_html = ""
        for feat in cfg.get("features", []):
            if feat.get("title"):
                features_html += f'''<div class="card" style="background:{card_bg};border-radius:16px;padding:32px;border:1px solid {border}">
<h3 style="font-size:1.3rem;margin-bottom:8px;color:{accent}">{feat['title']}</h3>
<p style="opacity:0.7;font-size:0.95rem">{feat.get('desc','')}</p></div>'''

        # Pricing
        pricing_section = ""
        if cfg.get("show_pricing", "yes") == "yes":
            pricing_cards = ""
            for plan in [
                {"name": "Starter", "price": "0", "period": "forever", "features": ["3 projects", "1GB storage", "Community support"]},
                {"name": "Pro", "price": "19", "period": "/mo", "features": ["Unlimited projects", "100GB storage", "Priority support", "Custom domain"], "featured": True},
                {"name": "Enterprise", "price": "99", "period": "/mo", "features": ["Everything in Pro", "SSO", "SLA", "Dedicated support"]},
             = []
                featured_class = ' featured' if plan.get('featured') else ''
                features_list = ''.join(f'<li style="padding:8px 0;opacity:0.8;border-bottom:1px solid {border}">{f}</li>' for f in plan['features'])
                pricing_cards += f'''<div class="price-card{featured_class}" style="background:{card_bg};border-radius:16px;padding:32px;border:2px solid {border}{';border-color:'+accent if plan.get('featured') else ''}">
<h3 style="font-size:1.2rem;margin-bottom:8px">{plan['name']}</h3>
<div class="price" style="font-size:2.5rem;font-weight:800;color:{accent};margin:16px 0">${plan['price']}<span style="font-size:1rem;opacity:0.5">{plan['period']}</span></div>
<ul style="list-style:none;padding:0;margin:24px 0;text-align:left">{features_list}</ul>
<a href="#" class="cta" style="display:block;padding:12px;text-align:center;background:{accent};color:#fff;border-radius:8px;text-decoration:none;font-weight:600">Choose {plan['name']}</a></div>'''

            pricing_section = f'''<section class="pricing" style="padding:60px 0;text-align:center" id="pricing">
<div class="container" style="max-width:1100px;margin:0 auto;padding:0 24px">
<h2 style="font-size:2rem;margin-bottom:40px">Simple Pricing</h2>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px">{pricing_cards}</div>
</div></section>'''

        return PAGE_TEMPLATE.format(
            title=cfg.get("title", "Landing Page"),
            description=cfg.get("description", ""),
            bg_color=bg,
            text_color=text,
            accent_color=accent,
            accent2_color=accent2,
            card_bg=card_bg,
            border_color=border,
            nav_logo=cfg.get("nav_logo", "Brand"),
            nav_links=nav_links,
            hero_title=cfg.get("hero_title", "Build Something"),
            hero_subtitle=cfg.get("hero_subtitle", ""),
            hero_cta=hero_cta,
            features=features_html,
            pricing_section=pricing_section,
            year=str(datetime.utcnow().year),
            footer_text=cfg.get("footer_text", ""),
        )

    def send_json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Landing Page Generator on :{PORT}")
    server.serve_forever()
