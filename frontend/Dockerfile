# Multi-Stage Production Dockerfile for MediLens AI Frontend
# Stage 1: Build React + TypeScript static distribution
FROM node:20-alpine AS build

WORKDIR /app

# Copy dependency specifications and install cleanly
COPY package*.json ./
RUN npm ci

# Copy application source code
COPY . .

# Build production assets
RUN npm run build

# Stage 2: Serve compiled SPA with high-performance NGINX Alpine
FROM nginx:alpine AS production

# Remove default nginx configurations
RUN rm -rf /etc/nginx/conf.d/*

# Copy custom production nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy compiled frontend static assets from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose standard web ports
EXPOSE 80

# Healthcheck probe for NGINX container
HEALTHCHECK --interval=15s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
