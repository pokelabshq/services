FROM python:3.12-slim
WORKDIR /app
COPY server.py /app/
RUN pip install --no-cache-dir requests 2>/dev/null || true
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["python3", "server.py"]
