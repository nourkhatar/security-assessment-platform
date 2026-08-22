FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir flask==3.0.3
COPY app.py .
# Intentional: no USER directive -> runs as root (DOCKER-001)
# Intentional: no HEALTHCHECK (DOCKER-010)
EXPOSE 5000
CMD ["python", "app.py"]
