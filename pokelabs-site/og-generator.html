<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OG Image Generator — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--purple:#667eea;--dark:#0a0a0f;--card:#151520;--border:#2a2a3a;--text:#e0e0e0;--muted:#888;--green:#4ade80;--yellow:#fbbf24;--red:#f87171}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--dark);color:var(--text);line-height:1.6}
.container{max-width:900px;margin:0 auto;padding:0 2rem}
nav{display:flex;justify-content:space-between;align-items:center;padding:1.5rem 0;border-bottom:1px solid var(--border)}
nav .logo{font-size:1.4rem;font-weight:700;color:var(--text)}nav .logo span{color:var(--purple)}
nav a{color:var(--muted);text-decoration:none;font-size:0.95rem}nav a:hover{color:var(--text)}
h1{font-size:2.2rem;text-align:center;margin:3rem 0 0.5rem}
.subtitle{text-align:center;color:var(--muted);margin-bottom:2rem}
.builder{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:2rem;margin-bottom:2rem}
.form-row{margin-bottom:1.25rem}
.form-row label{display:block;font-size:0.85rem;color:var(--muted);margin-bottom:0.4rem;text-transform:uppercase;letter-spacing:0.05em}
.form-row input,.form-row textarea{width:100%;padding:0.7rem 1rem;border-radius:8px;border:1px solid var(--border);background:var(--dark);color:var(--text);font-size:1rem;outline:none;font-family:inherit}
.form-row input:focus,.form-row textarea:focus{border-color:var(--purple)}
.form-row textarea{resize:vertical;min-height:60px}
.form-row .color-row{display:flex;gap:0.75rem;align-items:center}
.form-row .color-row input[type=color]{width:50px;height:40px;padding:2px;border-radius:6px;cursor:pointer;border:1px solid var(--border)}
.form-row .color-row input[type=text]{width:120px}
.presets{display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.75rem}
.preset{width:30px;height:30px;border-radius:6px;cursor:pointer;border:2px solid transparent;transition:transform .15s}
.preset:hover{transform:scale(1.15);border-color:var(--text)}
.btn{padding:0.8rem 2rem;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;border:none;color:#fff;background:linear-gradient(135deg,var(--purple),#764ba2)}
.btn:hover{opacity:0.85}
.btn-row{display:flex;gap:1rem;justify-content:center;margin-top:1.5rem}
.preview-area{max-width:700px;margin:0 auto}
.preview-box{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;text-align:center}
.preview-box h3{margin-bottom:1rem}
.preview-box img{max-width:100%;border-radius:8px;box-shadow:0 4px 20px rgba(0,0,0,0.3)}
.api-block{background:var(--dark);border:1px solid var(--border);border-radius:8px;padding:1rem;margin-top:1.5rem;text-align:left;font-family:'SF Mono',Monaco,monospace;font-size:0.85rem;overflow-x:auto;color:var(--muted)}
.api-block .k{color:var(--purple)}.api-block .s{color:var(--green)}.api-block .c{color:#666}
.loading{color:var(--muted);padding:2rem;text-align:center}
.error{color:var(--red);padding:1rem;text-align:center}
footer{text-align:center;padding:3rem 0;border-top:1px solid var(--border);color:var(--muted);font-size:0.9rem;margin-top:3rem}
</style>
</head>
<body>
<nav class="container"><div class="logo">poke<span>labs</span></div><a href="/">← Home</a></nav>
<div class="container">
<h1>🖼️ OG Image Generator</h1>
<p class="subtitle">Create beautiful 1200×630 social preview images. Free, no signup, no watermark.</p>

<div class="builder">
  <div class="form-row"><label>Title</label><input type="text" id="ogTitle" placeholder="Your Page Title" value="Hello World"></div>
  <div class="form-row"><label>Description (optional)</label><textarea id="ogDesc" placeholder="A short description...">Build something amazing today.</textarea></div>
  <div class="form-row"><label>Site Name (optional)</label><input type="text" id="ogSite" placeholder="yourbrand.com"></div>
  <div class="form-row">
    <label>Background</label>
    <div class="color-row">
      <input type="color" id="ogBgColor1" value="#667eea">
      <span style="color:var(--muted)">→</span>
      <input type="color" id="ogBgColor2" value="#764ba2">
    </div>
    <div class="presets">
      <div class="preset" style="background:linear-gradient(135deg,#667eea,#764ba2)" onclick="setPreset('#667eea','#764ba2')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#f093fb,#f5576c)" onclick="setPreset('#f093fb','#f5576c')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#4facfe,#00f2fe)" onclick="setPreset('#4facfe','#00f2fe')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#43e97b,#38f9d7)" onclick="setPreset('#43e97b','#38f9d7')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#fa709a,#fee140)" onclick="setPreset('#fa709a','#fee140')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#a18cd1,#fbc2eb)" onclick="setPreset('#a18cd1','#fbc2eb')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#0c0c0c,#1a1a2e)" onclick="setPreset('#0c0c0c','#1a1a2e')"></div>
      <div class="preset" style="background:linear-gradient(135deg,#ffecd2,#fcb69f)" onclick="setPreset('#ffecd2','#fcb69f')"></div>
    </div>
  </div>
  <div class="form-row">
    <label>Layout</label>
    <div class="presets" id="layoutPresets">
      <div class="preset" style="width:60px;background:var(--dark);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:0.6rem" onclick="setLayout('center')" title="Center">⊕</div>
      <div class="preset" style="width:60px;background:var(--dark);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:0.6rem" onclick="setLayout('left')" title="Left">◧</div>
      <div class="preset" style="width:60px;background:var(--dark);border:1px solid var(--border);display:flex;align-items:center;justify-content:center;font-size:0.6rem" onclick="setLayout('split')" title="Split">◫</div>
    </div>
  </div>
  <div class="btn-row">
    <button class="btn" onclick="generate()">Generate Image</button>
    <button class="btn" style="background:var(--card);color:var(--text);border:1px solid var(--border)" onclick="downloadImg()">Download PNG</button>
  </div>
</div>

<div class="preview-area" id="previewArea"></div>
</div>
<footer><p>Free tool by <a href="https://github.com/pokelabshq" style="color:var(--purple)">Poke Labs</a> — MIT licensed</p></footer>

<script>
let currentBlob=null;
function setPreset(c1,c2){document.getElementById('ogBgColor1').value=c1;document.getElementById('ogBgColor2').value=c2;}
let currentLayout='center';
function setLayout(l){currentLayout=l;}

async function generate(){
  const params=new URLSearchParams({
    title:document.getElementById('ogTitle').value,
    desc:document.getElementById('ogDesc').value,
    site:document.getElementById('ogSite').value,
    bg1:document.getElementById('ogBgColor1').value,
    bg2:document.getElementById('ogBgColor2').value,
    layout:currentLayout
  });
  const prev=document.getElementById('previewArea');
  prev.innerHTML='<div class="loading">Generating...</div>';
  try{
    const r=await fetch('/api/og-generate?'+params);
    if(r.status===402){prev.innerHTML='<div class="error">Free limit reached! <a href="/#pricing" style="color:var(--purple)">Upgrade</a> for unlimited.</div>';return;}
    if(!r.ok){const t=await r.text();prev.innerHTML='<div class="error">Error: '+t+'</div>';return;}
    const blob=await r.blob();
    currentBlob=blob;
    const url=URL.createObjectURL(blob);
    prev.innerHTML='<div class="preview-box"><h3>Your OG Image (1200×630)</h3><img src="'+url+'" alt="OG Image"/><div class="api-block"><span class="c">// Embed in your &lt;head&gt;:</span><br/><span class="s">"&lt;meta property=</span><span class="s">"og:image"</span> <span class="s">content=</span><span class="s">"https://pokelabs.org/api/og-generate?title=Hello+World"</span><span class="s">" /&gt;"</span></div></div>';
  }catch(e){prev.innerHTML='<div class="error">Failed: '+e.message+'</div>';}
}

function downloadImg(){
  if(!currentBlob)return;
  const a=document.createElement('a');
  a.href=URL.createObjectURL(currentBlob);
  a.download='og-image.png';
  a.click();
}
</script>
</body>
</html>
