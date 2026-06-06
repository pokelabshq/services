FROM python3:12-slim
WORKDIR /app
COPY server.py /app/
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3   CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1
CMD ["python3", "server.py"]
