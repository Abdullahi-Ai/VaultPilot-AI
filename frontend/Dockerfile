# VaultPilot AI — Frontend Multi-Stage Containerfile for UGREEN UGOS
# Security Profile: Multi-stage build, minimal Alpine runtime, unprivileged non-root user (UID 1000).

# ------------------------------------------------------------------------------
# Stage 1: Build Production Bundle
# ------------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies deterministically
COPY package.json package-lock.json ./
RUN npm ci

# Copy configuration and source files
COPY tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.js postcss.config.js index.html ./
COPY src/ src/

# Compile TypeScript and build production bundle with Vite
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Unprivileged Nginx Web Server
# ------------------------------------------------------------------------------
FROM nginx:alpine

# Remove default configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy hardened custom Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy compiled static assets from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Prepare directories for unprivileged user operation and tmpfs mounts
RUN mkdir -p /var/cache/nginx /var/run /tmp/client_temp && \
    touch /tmp/nginx.pid && \
    chown -R 1000:1000 /var/cache/nginx /var/run /tmp /usr/share/nginx/html /etc/nginx

USER 1000:1000

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
