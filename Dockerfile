FROM python:3.12-alpine
RUN apk add --no-cache ca-certificates
RUN pip install --no-cache-dir certifi
WORKDIR /app
COPY app.py .
COPY templates /templates
RUN addgroup -S app \
    && adduser -S app -G app \
    && mkdir -p /data \
    && chown app:app /data
USER app
CMD ["python", "/app/app.py"]
