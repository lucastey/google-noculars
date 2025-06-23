# Google Cloud Run Dockerfile for Google Noculars
FROM node:18-slim

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Copy application files
COPY server.js ./
COPY client-sdk/ ./client-sdk/
COPY demo.html ./
COPY dashboard.html ./
COPY DEMO_API_KEYS.md ./

# Note: In Cloud Run, we use the default service account
# No need to copy service-account-key.json

# Set environment variables
ENV PORT=8080
ENV NODE_ENV=production

# Expose port
EXPOSE 8080

# Install curl for health check
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["node", "server.js"]