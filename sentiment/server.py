#!/usr/bin/env python3
"""Sentiment Analysis Service — Poke Labs Council Platform. Port: 8777"""

import http.server
import json
import re
import urllib.parse
import os

POSITIVE_WORDS = {
    "good": 3, "great": 3, "excellent": 4, "amazing": 4, "wonderful": 4,
    "fantastic": 4, "awesome": 4, "love": 3, "like": 2, "happy": 3,
    "joy": 3, "beautiful": 3, "best": 3, "brilliant": 4, "cool": 2,
    "enjoy": 2, "excited": 3, "fun": 3, "glad": 3, "grateful": 3,
    "impressive": 3, "incredible": 4, "nice": 2, "perfect": 4, "pleasant": 2,
    "positive": 2, "recommend": 2, "satisfied": 3, "superb": 4,
    "thank": 2, "thanks": 2, "useful": 2, "valuable": 3, "win": 3,
    "winner": 3, "winning": 3, "worthy": 3, "outstanding": 4,
    "remarkable": 3, "splendid": 4, "stellar": 4, "terrific": 4,
    "delightful": 3, "helpful": 2, "effective": 2, "efficient": 2,
    "reliable": 2, "smooth": 2, "easy": 2, "fast": 2, "quick": 2,
    "secure": 2, "innovative": 3, "creative": 3, "elegant": 3,
    "solid": 2, "strong": 2, "alpha": 2, "bullish": 3, "moon": 3,
    "hodl": 2, "gem": 3, "fire": 2, "lit": 2, "epic": 3,
}

NEGATIVE_WORDS = {
    "bad": -3, "terrible": -4, "awful": -4, "horrible": -4, "hate": -3,
    "dislike": -2, "sad": -3, "angry": -3, "annoying": -2, "boring": -2,
    "broken": -3, "bug": -2, "bugs": -2, "crash": -3, "crashes": -3,
    "difficult": -2, "disappointed": -3, "disappointing": -3, "error": -2,
    "errors": -2, "fail": -3, "failed": -3, "failure": -3, "fault": -2,
    "frustrating": -3, "hard": -1, "issue": -2, "issues": -2, "lack": -2,
    "lacking": -2, "limit": -1, "limited": -1, "problem": -2, "problems": -2,
    "slow": -2, "stupid": -3, "ugly": -3, "unhappy": -3, "unreliable": -3,
    "useless": -3, "waste": -3, "worst": -4, "wrong": -2, "pain": -3,
    "painful": -3, "poor": -2, "regret": -3, "reject": -2, "rejected": -2,
    "ridiculous": -3, "scare": -2, "scary": -2, "sucks": -3, "suck": -3,
    "unfortunately": -2, "weak": -2, "worse": -3, "worry": -2, "worried": -2,
    "bearish": -3, "dump": -3, "scam": -4, "rugpull": -4,
}

INTENSIFIERS = {
    "very": 1.5, "really": 1.5, "extremely": 2.0, "absolutely": 2.0,
    "totally": 1.5, "completely": 1.5, "highly": 1.5, "incredibly": 1.5,
    "quite": 1.25, "so": 1.25, "super": 1.5, "utterly": 1.5,
}

NEGATORS = {"not","no","never","neither","nobody","nothing","nowhere","nor",
    "cannot","can't","don't","doesn't","didn't","won't","wouldn't",
    "shouldn't","couldn't","isn't","aren't","wasn't","weren't",
    "hasn't","haven't","hadn't"}

def analyze_sentiment(text):
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return {"score": 0, "label": "neutral", "confidence": 0, "word_count": 0}

    score = 0.0
    pos_count = 0
    neg_count = 0
    pos_words = []
    neg_words = []

    for i, word in enumerate(words):
        multiplier = 1.0
        if i > 0 and words[i-1] in INTENSIFIERS:
            multiplier = INTENSIFIERS[words[i-1]]
        negated = any(w in NEGATORS for w in words[max(0,i-3):i])

        if word in POSITIVE_WORDS:
            val = POSITIVE_WORDS[word] * multiplier
            if negated: val = -val
            score += val; pos_count += 1; pos_words.append(word)
        elif word in NEGATIVE_WORDS:
            val = NEGATIVE_WORDS[word] * multiplier
            if negated: val = -val
            score += val; neg_count += 1; neg_words.append(word)

    max_possible = max(len(words) * 4, 1)
    normalized = max(-1.0, min(1.0, score / max_possible * 5))
    label = "positive" if normalized > 0.1 else ("negative" if normalized < -0.1 else "neutral")
    confidence = min(1.0, (pos_count + neg_count) / max(len(words), 1) * 3)

    return {
        "score": round(normalized, 4), "label": label,
        "confidence": round(confidence, 4), "word_count": len(words),
        "positive_words": pos_count, "negative_words": neg_count,
        "positive_found": pos_words, "negative_found": neg_words,
    }

PORT = int(os.environ.get("PORT", 8777))
FREE_LIMIT = 3
ip_usage = {}

class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args): pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            self._respond(200, {"ok": True, "service": "sentiment", "v": 1})
        elif parsed.path == "/api/usage":
            ip = self.client_address[0]
            self._respond(200, {"used": ip_usage.get(ip, 0), "limit": FREE_LIMIT})
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != "/api/analyze":
            self._respond(404, {"error": "not found"}); return
        ip = self.client_address[0]
        if ip_usage.get(ip, 0) >= FREE_LIMIT:
            self._respond(402, {"error": "free limit exceeded", "wallet": "0xca3d86e4EDE205E6d72496BC2919c88b994B6beF", "chain": "base"}); return
        data = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        text = data.get("text", "")
        if not text or not isinstance(text, str):
            self._respond(400, {"error": "missing or invalid 'text' field"}); return
        result = analyze_sentiment(text)
        result["text_preview"] = text[:200] + ("..." if len(text) > 200 else "")
        ip_usage[ip] = ip_usage.get(ip, 0) + 1
        self._respond(200, result)

    def _respond(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"Sentiment service on port {PORT}")
    server.serve_forever()
