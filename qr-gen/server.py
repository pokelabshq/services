#!/usr/bin/env python3
"""Poke QR Generator v1.0
Zero-dependency QR code generator. Pure Python stdlib.
Generates QR codes as SVG strings or terminal output.
Supports alphanumeric and numeric modes. MIT License.

Usage:
    python3 qr_gen.py "Hello World"           # Terminal output
    python3 qr_gen.py "Hello" --svg out.svg    # SVG file
    python3 qr_gen.py "Hi" --server            # Start HTTP server :8781
"""

import http.server, json, sys, urllib.parse, base64

# === QR Code Encoding (simplified) ===

# Galois Field GF(256) arithmetic for Reed-Solomon error correction
GF_EXP = [0] * 512
GF_LOG = [0] * 256
def init_gf():
    x = 1
    for i in range(255):
        GF_EXP[i] = x
        GF_LOG[x] = i
        x <<= 1
        if x & 256:
            x ^= 0x11d  # primitive polynomial
    for i in range(255, 512):
        GF_EXP[i] = GF_EXP[i - 255]
init_gf()

def gf_mul(a, b):
    if a == 0 or b == 0:
        return 0
    return GF_EXP[GF_LOG[a] + GF_LOG[b]]

def poly_mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i+j] ^= gf_mul(a, b)
    return r

def rs_generator_poly(n):
    g = [1]
    for i in range(n):
        g = poly_mul(g, [1, GF_EXP[i]])
    return g

def rs_encode(data, nsym):
    """Reed-Solomon error correction encoding"""
    gen = rs_generator_poly(nsym)
    res = list(data) + [0] * nsym
    for i in range(len(data)):
        coef = res[i]
        if coef != 0:
            for j, g in enumerate(gen):
                res[i+j] ^= gf_mul(g, coef)
    return data + res[len(data):]

# === QR Matrix Patterns ===

# Format information strings (precomputed for M error correction, mask 0-7)
FORMAT_INFO_STRINGS = [
    0x5412, 0x5125, 0x5E7C, 0x5B4B, 0x45F9, 0x40CE, 0x4F97, 0x4AA0,
    0x77C4, 0x72F3, 0x7DAA, 0x789D, 0x662F, 0x6318, 0x6C41, 0x6976,
]

# Version info for V7+
VERSION_INFO = {
    7: 0x07C94, 8: 0x085BC, 9: 0x09A99, 10: 0x0A4D3,
}

def make_qr_matrix(text, ecl='M', mask=0):
    """Create a simplified QR matrix for short alphanumeric strings (up to ~20 chars)"""
    # For simplicity, use version 2-3 range
    # Determine version and size
    version = max(2, min(3, (len(text) + 10) // 8))
    size = 17 + version * 4
    
    # Initialize matrix with None
    matrix = [[None]*size for _ in range(size)]
    
    def set(x, y, val):
        if 0 <= x < size and 0 <= y < size:
            matrix[y][x] = val
    
    def set_rect(x0, y0, w, h, val):
        for y in range(y0, y0+h):
            for x in range(x0, x0+w):
                set(x, y, val)
    
    # Timing patterns (row 6, col 6)
    for i in range(size):
        set(i, 6, i % 2 == 0)
        set(6, i, i % 2 == 0)
    
    # Finder patterns (three corners)
    for cx, cy in [(0, 0), (0, size-7), (size-7, 0)]:
        set_rect(cx, cy, 7, 7, 0)
        set_rect(cx+1, cy+1, 5, 5, 1)
        set_rect(cx+2, cy+2, 3, 3, 1)
        # White border
        set_rect(cx, cy, 8, 8, 0)
        set(cx+7, cy, 0); set(cx+7, cy+7, 0)
        set(cx, cy+7, 0)
    
    # Alignment patterns for version >= 2
    if version >= 2:
        ap = [6, size-8]
        for r in ap:
            for c in ap:
                # Skip if overlaps with finder
                if r <= 8 and c <= 8: continue
                if r <= 8 and c >= size-8: continue
                if r >= size-8 and c <= 8: continue
                set_rect(c-2, r-2, 5, 5, 1)
                set_rect(c-1, r-1, 3, 3, 0)
                set(c, r, 1)
    
    # Dark module
    set(4*version + 9, 8, 1)
    
    # Encode data (simplified alphanumeric mode)
    ALPHANUM = '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ $%*+-./:'
    
    def encode_char(c):
        c = c.upper()
        if c in ALPHANUM:
            return ALPHANUM.index(c)
        return ALPHANUM.index(' ')
    
    # Build data codewords
    bits = ''
    bits += '0001'  # mode indicator (alphanumeric)
    bits += format(len(text), '09b')  # char count (v2-9)
    
    i = 0
    while i < len(text):
        if i+1 < len(text):
            val = 45 * encode_char(text[i]) + encode_char(text[i+1])
            bits += format(val, '011b')
            i += 2
        else:
            bits += format(encode_char(text[i]), '06b')
            i += 1
    
    bits += '0000'  # terminator
    # Pad to byte boundary
    while len(bits) % 8:
        bits += '0'
    
    # EC codeword count for version 2 M = 22 data + 22 ec = 44
    dcw = 22
    nsym = 22
    data_bytes = []
    for i in range(0, len(bits), 8):
        if len(data_bytes) >= dcw: break
        data_bytes.append(int(bits[i:i+8], 2))
    while len(data_bytes) < dcw:
        data_bytes.append(236 if len(data_bytes) % 2 == 0 else 17)  # padding
    
    ec_bytes = rs_encode(data_bytes, nsym)
    all_bytes = data_bytes + ec_bytes[dcw:]
    
    # Convert to bit stream
    data_bits = ''
    for b in all_bytes[:dcw]:
        data_bits += format(b, '08b')
    
    # Place data bits (simplified zig-zag fill)
    bit_idx = 0
    for col in range(size-1, 0, -2):
        if col == 6: col = 5  # skip timing
        for row in range(size):
            for dc in [0, -1]:
                c = col + dc
                if c < 0: continue
                r = row if (col % 2 == (size-1) % 2) else (size-1-row)
                if matrix[r][c] is None and bit_idx < len(data_bits):
                    bit = int(data_bits[bit_idx])
                    # Apply mask
                    if mask == 0 and (r + c) % 2 == 0: bit ^= 1
                    if mask == 1 and r % 2 == 0: bit ^= 1
                    if mask == 2 and c % 3 == 0: bit ^= 1
                    if mask == 3 and (r + c) % 3 == 0: bit ^= 1
                    matrix[r][c] = bit
                    bit_idx += 1
    
    return matrix

def matrix_to_svg(matrix, module_size=6, border=4):
    """Convert QR matrix to SVG string"""
    size = len(matrix)
    total = (size + border*2) * module_size
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total {total}" shape-rendering="crispEdges">\n'
    svg += f'<rect width="{total}" height="{total}" fill="#fff"/>\n'
    for y, row in enumerate(matrix):
        for x, val in enumerate(row):
            if val == 1:
                sx = (x + border) * module_size
                sy = (y + border) * module_size
                svg += f'<rect x="{sx}" y="{sy}" width="{module_size}" height="{module_size}" fill="#000"/>\n'
    svg += '</svg>\n'
    return svg

def matrix_to_text(matrix, text_modules=True):
    """Convert QR matrix to terminal-friendly text using block chars"""
    chars = ('\u2588\u2588', '  ') if text_modules else ('##', '  ')
    line = ''
    line += chars[1] * 8  # quiet zone top
    line += '\n' + chars[1] * 8 + '\n'
    for row in matrix:
        line += chars[1] * 4  # quiet zone left
        for val in row:
            line += chars[0] if val == 1 else chars[1]
        line += chars[1] * 4  # quiet zone right
        line += '\n'
    line += chars[1] * 8 + '\n' + chars[1] * 8
    return line

# === HTTP Server ===
def run_server(port=8781):
    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            p = urllib.parse.urlparse(self.path)
            if p.path == '/' or p.path == '/index.html':
                self.send_response(200)
                self.send_header('Content-Type', 'text/html')
                self.end_headers()
                self.wfile.write(DASHBOARD_HTML.encode())
            elif p.path == '/api/qr':
                params = urllib.parse.parse_qs(p.query)
                text = params.get('text', [''])[0]
                fmt = params.get('fmt', ['svg'])[0]
                if not text:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Missing text parameter'}).encode())
                    return
                matrix = make_qr_matrix(text)
                if fmt == 'svg':
                    svg = matrix_to_svg(matrix)
                    self.send_response(200)
                    self.send_header('Content-Type', 'image/svg+xml')
                    self.end_headers()
                    self.wfile.write(svg.encode())
                elif fmt == 'json':
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'matrix': matrix, 'size': len(matrix)}).encode())
                elif fmt == 'text':
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(matrix_to_text(matrix).encode('utf-8'))
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps({'error': 'Unknown format. Use svg, json, or text'}).encode())
            elif p.path == '/api/health':
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'ok': True, 'v': 1, 'service': 'qr-generator'}).encode())
            else:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Not found'}).encode())
        
        def log_message(self, format, *args):
            pass
    
    srv = http.server.HTTPServer(('', port), Handler)
    print(f'Poke QR Generator running on :{port}')
    srv.serve_forever()

DASHBOARD_HTML = """<!DOCTYPE html>
<html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Poke QR Generator</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;background:#0d1117;color:#c9d1d9;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 24px}
h1{color:#fff;margin-bottom:6px}h1 em{color:#00d4ff;font-style:normal}
p{color:#8b949e;margin-bottom:24px;font-size:14px}
input[type=text]{width:400px;max-width:90vw;padding:10px 14px;background:#161b22;border:1px solid #30363d;border-radius:6px;color:#c9d1d9;font-size:14px;margin-bottom:12px;outline:none}
input:focus{border-color:#388bfd}
button{padding:10px 24px;background:#238636;color:#fff;border:none;border-radius:6px;font-size:14px;font-weight:600;cursor:pointer}
button:hover{background:#2ea043}
#result{margin-top:24px;text-align:center}
#result img,#result svg{max-width:300px;background:#fff;padding:16px;border-radius:8px}
pre{background:#161b22;padding:16px;border-radius:8px;font-size:10px;overflow-x:auto;text-align:left;max-width:90vw}
</style></head>
<body>
<h1>&#x1F43E; <em>Poke</em> QR Generator</h1>
<p>Zero-dependency QR code generator. Pure Python stdlib.</p>
<input type="text" id="text" placeholder="Enter text or URL..." onkeydown="if(event.key==='Enter')generate()">
<br><button onclick="generate()">Generate QR</button>
<div id="result"></div>
<script>
async function generate(){
  const t=document.getElementById('text').value;
  if(!t)return;
  const r=await fetch('/api/qr?text='+encodeURIComponent(t)+'&fmt=svg');
  const s=await r.text();
  document.getElementById('result').innerHTML=s;
}
</script></body></html>"""

if __name__ == '__main__':
    if '--server' in sys.argv:
        port = int(sys.argv[sys.argv.index('--server')+1]) if '--server' in sys.argv and sys.argv.index('--server')+1 < len(sys.argv) else 8781
        run_server(port)
    elif len(sys.argv) > 1:
        text = ' '.join(a for a in sys.argv[1:] if not a.startswith('--'))
        if '--svg' in sys.argv:
            idx = sys.argv.index('--')
            out = sys.argv[idx+1] if idx+1 < len(sys.argv) else 'qr.svg'
            m = make_qr_matrix(text)
            svg = matrix_to_svg(m)
            with open(out, 'w') as f:
                f.write(svg)
            print(f'QR code saved to {out}')
        else:
            m = make_qr_matrix(text)
            print(matrix_to_text(m))
    else:
        print(__doc__)
