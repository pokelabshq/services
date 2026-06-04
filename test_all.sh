#!/bin/bash
# Poke Labs — Full Service Test Suite
# Tests all 12 services + gateway routing
# Run: bash test_all.sh

PASS=0
FAIL=0
PORTS="link-preview:8765 keyword:8766 summarize:8767 qr:8768 dns:8769 portal:8770 color:8771 url:8772 template-gen:8773 health-agg:8774 json2ts:8775 github-webhook:8776"
GW=8770

echo "🧪 Poke Labs Test Suite"
echo "========================"

# Health checks
echo ""
echo "--- Health Checks ---"
for svc in $PORTS; do
  name="${svc%%:*}"
  port="${svc##*:}"
  if curl -sf "http://localhost:$port/api/health" > /dev/null 2>&1; then
    echo "  ✅ $name (port $port)"
    PASS=$((PASS+1))
  else
    echo "  ❌ $name (port $port) — NOT RUNNING"
    FAIL=$((FAIL+1))
  fi
done

echo ""
echo "--- Gateway Routing ---"
# Test gateway routes
code=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8700/link-preview/api/health")
if [ "$code" = "200" ]; then echo "  ✅ /link-preview -> 8765"; PASS=$((PASS+1)); else echo "  ❌ /link-preview (got $code)"; FAIL=$((FAIL+1)); fi

code=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8700/qr/api/health")
if [ "$code" = "200" ]; then echo "  ✅ /qr -> 8768"; PASS=$((PASS+1)); else echo "  ❌ /qr (got $code)"; FAIL=$((FAIL+1)); fi

code=$(curl -so /dev/null -w "%{http_code}" "http://localhost:8700/health-agg/api/status")
if [ "$code" = "200" ]; then echo "  ✅ /health-agg -> 8774"; PASS=$((PASS+1)); else echo "  ❌ /health-agg (got $code)"; FAIL=$((FAIL+1)); fi

echo ""
echo "--- API Functional Tests ---"
# Link Preview (free tier)
resp=$(curl -sf -X POST "http://localhost:8765/api/preview" -H "Content-Type: application/json" -d '{"url":"https://github.com"}')
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'title' in d" 2>/dev/null; then
  echo "  ✅ Link Preview returns title"; PASS=$((PASS+1))
else
  echo "  ❌ Link Preview failed"; FAIL=$((FAIL+1))
fi

# Keyword Extractor
resp=$(curl -sf -X POST "http://localhost:8766/api/extract" -H "Content-Type: application/json" -d '{"text":"The quick brown fox jumps over the lazy dog"}')
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'keywords' in d" 2>/dev/null; then
  echo "  ✅ Keyword Extractor returns keywords"; PASS=$((PASS+1))
else
  echo "  ❌ Keyword Extractor failed"; FAIL=$((FAIL+1))
fi

# Summarize
resp=$(curl -sf -X POST "http://localhost:8767/api/summarize" -H "Content-Type: application/json" -d '{"text":"Machine learning is a subset of artificial intelligence. It involves training algorithms on data to make predictions. Deep learning is a type of machine learning using neural networks."}')
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'summary' in d" 2>/dev/null; then
  echo "  ✅ Summarizer returns summary"; PASS=$((PASS+1))
else
  echo "  ❌ Summarizer failed"; FAIL=$((FAIL+1))
fi

# QR Code
resp=$(curl -sf -X POST "http://localhost:8768/api/qr" -H "Content-Type: application/json" -d '{"text":"https://pokelabs.org"}')
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'qr' in d or 'image' in d" 2>/dev/null; then
  echo "  ✅ QR Generator returns QR"; PASS=$((PASS+1))
else
  echo "  ❌ QR Generator failed"; FAIL=$((FAIL+1))
fi

# DNS Checker
resp=$(curl -sf -X POST "http://localhost:8769/api/query" -H "Content-Type: application/json" -d '{"domain":"github.com","type":"A"}')
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'records' in d or 'answer' in d" 2>/dev/null; then
  echo "  ✅ DNS Checker returns records"; PASS=$((PASS+1))
else
  echo "  ❌ DNS Checker failed"; FAIL=$((FAIL+1))
fi

# Health Agg
resp=$(curl -sf "http://localhost:8774/api/status")
if echo "$resp" | python3 -c "import sys,json; d=json.load(sys.stdin); assert 'services' in d" 2>/dev/null; then
  echo "  ✅ Health Agg returns services"; PASS=$((PASS+1))
else
  echo "  ❌ Health Agg failed"; FAIL=$((FAIL+1))
fi

echo ""
echo "========================"
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && echo "🎉 ALL TESTS PASSED" || echo "⚠️  Some tests failed"
