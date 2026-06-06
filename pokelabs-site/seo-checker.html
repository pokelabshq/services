<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SEO Meta Checker — Poke Labs</title>
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{--purple:#667eea;--dark:#0a0a0f;--card:#151520;--border:#2a2a3a;--text:#e0e0e0;--muted:#888;--green:#4ade80;--yellow:#fbbf24;--red:#f87171}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:var(--dark);color:var(--text);line-height:1.7}
.container{max-width:900px;margin:0 auto;padding:0 2rem}
nav{display:flex;justify-content:space-between;align-items:center;padding:1.5rem 0;border-bottom:1px solid var(--border)}
nav .logo{font-size:1.4rem;font-weight:700;color:var(--text)}nav .logo span{color:var(--purple)}
nav a{color:var(--muted);text-decoration:none;font-size:0.95rem}nav a:hover{color:var(--text)}
h1{font-size:2.2rem;text-align:center;margin:3rem 0 0.5rem}
.subtitle{text-align:center;color:var(--muted);margin-bottom:2rem}
.input-row{display:flex;gap:0.75rem;max-width:700px;margin:0 auto 2rem}
.input-row input{flex:1;padding:0.8rem 1rem;border-radius:8px;border:1px solid var(--border);background:var(--card);color:var(--text);font-size:1rem;outline:none}
.input-row input:focus{border-color:var(--purple)}
.btn{padding:0.8rem 2rem;border-radius:8px;font-size:1rem;font-weight:600;cursor:pointer;border:none;color:#fff;background:linear-gradient(135deg,var(--purple),#764ba2)}
.btn:hover{opacity:0.85}
.result{max-width:700px;margin:0 auto}
.score-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:2rem;text-align:center;margin-bottom:1.5rem}
.score-card .score{font-size:4rem;font-weight:800}
.score-card .score.a{color:var(--green)}.score-card .score.b{color:#60a5fa}.score-card .score.c{color:var(--yellow)}.score-card .score.d{color:#f97316}.score-card .score.f{color:var(--red)}
.score-card .grade{font-size:1.5rem;color:var(--muted)}
.meta-table{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin-bottom:1.5rem}
.meta-table h3{margin-bottom:1rem}
.meta-table table{width:100%;border-collapse:collapse}
.meta-table td{padding:0.5rem;border-bottom:1px solid var(--border);font-size:0.9rem}
.meta-table td:first-child{color:var(--muted);width:40%}
.issues{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem}
.issues h3{margin-bottom:1rem;color:var(--yellow)}
.issues li{padding:0.4rem 0;color:var(--muted)}
.preview-card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:1.5rem;margin-bottom:1.5rem}
.preview-card h3{margin-bottom:1rem}
.preview-box{border:1px solid var(--border);border-radius:8px;padding:1rem;background:var(--dark)}
.preview-box .p-title{font-size:1.1rem;font-weight:600;color:#60a5fa;margin-bottom:0.25rem}
.preview-box .p-desc{color:var(--muted);font-size:0.9rem;margin-bottom:0.25rem}
.preview-box .p-url{color:var(--green);font-size:0.8rem}
.preview-box img{max-width:100%;border-radius:6px;margin-bottom:0.5rem}
.loading{text-align:center;padding:3rem;color:var(--muted)}
.error{color:var(--red);text-align:center;padding:1rem}
footer{text-align:center;padding:3rem 0;border-top:1px solid var(--border);color:var(--muted);font-size:0.9rem;margin-top:3rem}
</style>
</head>
<body>
<nav class="container"><div class="logo">poke<span>labs</span></div><a href="/">← Home</a></nav>
<div class="container">
<h1>🔍 SEO Meta Checker</h1>
<p class="subtitle">Check your Open Graph tags, Twitter Cards, and meta description. Free, no signup.</p>
<div class="input-row">
  <input type="text" id="urlInput" placeholder="Enter your URL... e.g. https://yoursite.com">
  <button class="btn" onclick="check()">Check SEO</button>
</div>
<div class="result" id="result"></div>
</div>
<footer><p>Built by <a href="https://github.com/pokelabshq" style="color:var(--purple)">Poke Labs</a> — Free & open source</p></footer>
<script>
async function check(){
  const url=document.getElementById('urlInput').value;
  const r=document.getElementById('result');
  if(!url){r.innerHTML='<div class="error">Please enter a URL</div>';return;}
  r.innerHTML='<div class="loading">Analyzing your page...</div>';
  try{
    const res=await fetch('/api/seo-audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url})});
    const d=await r.json();
    if(d.error==='limit'){r.innerHTML='<div class="error">Free limit reached! <a href="/#pricing" style="color:var(--purple)">Upgrade</a> for unlimited checks.</div>';return;}
    if(d.error){r.innerHTML='<div class="error">Error: '+d.error+'</div>';return;}
    const gc='score '+d.grade.toLowerCase();
    let html=`<div class="score-card"><div class="${gc}">${d.score}/100</div><div class="grade">Grade: ${d.grade} &mdash; ${d.checks_passed}/${d.checks_total} checks passed</div></div>`;
    if(d.meta){
      if(d.meta.image||d.meta.og_title){
        html+='<div class="preview-card"><h3>Social Preview</h3><div class="preview-box">';
        if(d.meta.image)html+='<img src="'+d.meta.image+'" />';
        html+='<div class="p-title">'+(d.meta.og_title||d.meta.title||'')+'</div>';
        html+='<div class="p-desc">'+(d.meta.og_description||d.meta.description||'')+'</div>';
        html+='<div class="p-url">'+d.url+'</div></div></div>';
      }
      html+='<div class="meta-table"><h3>Meta Tags Found</h3><table>';
      const labels={'title':'Title Tag','og_title':'og:title','description':'Meta Description','og_description':'og:description','image':'og:image','og_site_name':'og:site_name','favicon':'Favicon','twitter_title':'twitter:title','twitter_description':'twitter:description','twitter_image':'twitter:image'};
      for(const[k,v] of Object.entries(labels)){const val=d.meta[k]||'';html+='<tr><td>'+v+'</td><td>'+(val?('<code>'+val.substring(0,120)+(val.length>120?'...':'')+'</code>'):'<span style="color:var(--red)">Missing</span>')+'</td></tr>';}
      html+='</table></div>';
    }
    if(d.issues&&d.issues.length){
      html+='<div class="issues"><h3>⚠️ Issues ('+d.issues.length+')</h3><ul>';
      for(const i of d.issues)html+='<li>'+i+'</li>';
      html+='</ul></div>';
    } else if(d.issues) {
      html+='<div class="score-card" style="background:#1a3a2a;border-color:#22c55e"><div class="score a" style="font-size:2rem">🎉 All checks passed!</div></div>';
    }
    if(d.free_remaining!==undefined)html+='<p style="text-align:center;color:var(--muted);margin-top:1rem">'+d.free_remaining+' free checks remaining today</p>';
    r.innerHTML=html;
  }catch(e){r.innerHTML='<div class="error">Failed: '+e.message+'</div>';}
}
document.getElementById('urlInput').addEventListener('keydown',e=>{if(e.key==='Enter')check();});
</script>
</body>
</html>
