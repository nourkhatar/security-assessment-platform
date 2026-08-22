FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3
COPY app.py .
# Non-root user (DOCKER-001)
RUN useradd -r -u 1001 -m appuser
USER appuser
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5001/health')" || exit 1
EXPOSE 5001
CMD ["python", "app.py"]
