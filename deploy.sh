#!/bin/bash
# Google Cloud Run Deployment Script for Google Noculars

set -e

echo "🚀 Deploying Google Noculars to Cloud Run..."

# Configuration
PROJECT_ID="stellar-brace-463007-c0"
SERVICE_NAME="google-noculars"
REGION="asia-southeast1"

# Build and deploy
gcloud run deploy $SERVICE_NAME \
  --source . \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --timeout 900 \
  --set-env-vars NODE_ENV=production \
  --project $PROJECT_ID

echo "✅ Deployment complete!"
echo "🌐 Your service URL will be shown above"
echo "📋 Update your integration to use: https://your-service-url.com/client-sdk/tracker.js?key=demo-123"