# Stage 1: Build stage
FROM python:3.12-alpine AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install build dependencies
RUN apk update && \
    apk add --no-cache --virtual .build-deps build-base libffi-dev && \
    python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies - copying only requirements.txt for better cache utilization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del .build-deps

# Stage 2: Runtime stage
FROM python:3.12-alpine

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install runtime dependencies in a single layer
RUN apk update && \
    apk add --no-cache \
    nss \
    alsa-lib \
    libx11 \
    libxcomposite \
    libxdamage \
    libxrandr \
    libxinerama \
    libxshmfence \
    libxext \
    gtk+3.0 \
    pango \
    ttf-freefont \
    ttf-opensans \
    curl \
    xvfb && \
    rm -rf /var/cache/apk/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code and config files
COPY . .