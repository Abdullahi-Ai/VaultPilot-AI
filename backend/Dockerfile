# VaultPilot AI — Backend Containerfile for UGREEN UGOS Container Station
# Base Image: Python 3.10 slim Linux
# Security Profile: Unprivileged non-root (UID 1000), read-only compatible, no extra build tools in final layer.

FROM python:3.10-slim

# Prevent Python from writing .pyc files to immutable rootfs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/vaultpilot/.local/bin:$PATH"

# Install curl for Docker healthcheck and clean apt caches
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user and group matching UGOS standard UID 1000
RUN groupadd -g 1000 vaultpilot && \
    useradd -u 1000 -g vaultpilot -m -s /bin/bash vaultpilot

# Create mount points for persistent database and temporary files
RUN mkdir -p /vaultpilot_data /app /tmp && \
    chown -R vaultpilot:vaultpilot /vaultpilot_data /app /tmp && \
    chmod 1777 /tmp

WORKDIR /app

# Install Python dependencies as vaultpilot user
COPY --chown=vaultpilot:vaultpilot requirements.txt .
USER 1000:1000
RUN pip install --no-cache-dir --user -r requirements.txt

# Copy backend application source code
COPY --chown=vaultpilot:vaultpilot alembic.ini .
COPY --chown=vaultpilot:vaultpilot alembic/ alembic/
COPY --chown=vaultpilot:vaultpilot app/ app/

# Expose FastAPI HTTP port
EXPOSE 8000

# Health check probe validating HTTP responsiveness
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/projects || exit 1

# Launch ASGI server bound to all container interfaces
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
