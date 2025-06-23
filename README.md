# Google Noculars
*Real-time UX insights powered by AI*

A complete UX analytics platform built with Google ADK and Gemini 2.0 Flash that tracks user behavior and generates actionable recommendations.

## Quick Test (3 minutes)

**Live Demo:** https://google-noculars-71430128784.asia-southeast1.run.app

### Step 1: Generate Activity (1 min)
1. Open demo page: `/demo.html`
2. Move mouse, click buttons, scroll around
3. Data auto-tracks to BigQuery every 10 seconds

### Step 2: View Analytics (2 min)
1. Open dashboard: `/dashboard.html`
2. Click "🔄 Refresh Data" to see your activity
3. Check **Activity Timeline** - shows your real-time interactions
4. View **AI Recommendations** - Gemini-powered insights
5. Try different tenants in dropdown

## Key Features
- **Real-time tracking** - Mouse, clicks, scroll data
- **AI insights** - Gemini 2.0 Flash recommendations  
- **Google Cloud** - BigQuery + ADK agents + Cloud Run
- **Multi-tenant** - Isolated data per client

## Architecture
User → JS SDK → BigQuery → ADK Agents → AI Insights → Dashboard

## Expected Results
- Live metrics update with your session data
- Activity timeline shows individual events with timestamps
- AI generates specific UX improvement recommendations
- Multi-tenant data isolation works

## Troubleshooting
- If no data: Wait 15 seconds, refresh dashboard
- If issues: Check browser console, try incognito mode

## Local Development
```bash
npm install
npm start
# Open http://localhost:3000/demo.html and http://localhost:3000/dashboard.html
```

---
*Built for the Google ADK Hackathon 2025*
