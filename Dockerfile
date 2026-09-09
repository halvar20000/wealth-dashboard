# Small, no build step, no compiler at runtime. `cryptography` ships
# manylinux wheels, so the slim image is enough on amd64 and arm64.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    WD_DATA_DIR=/data \
    WD_HOST=0.0.0.0 \
    WD_PORT=8000

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

# The image holds no data. Everything the user owns is in the volume,
# which is what makes "back up /data" a complete instruction.
VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz',timeout=3).status==200 else 1)"

CMD ["python", "-m", "app"]
