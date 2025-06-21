#!/usr/bin/env node
/**
 * Google Noculars - Backend API Server
 * Express.js server to receive tracking data and store in BigQuery
 */

const express = require('express');
const cors = require('cors');
const { BigQuery } = require('@google-cloud/bigquery');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

// Initialize BigQuery client
const bigquery = new BigQuery({
    keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS || './service-account-key.json',
    projectId: process.env.GOOGLE_CLOUD_PROJECT_ID
});

const dataset = bigquery.dataset('ux_insights');
const mouseTrackingTable = dataset.table('mouse_tracking');

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.static('.')); // Serve static files from root directory
app.use('/client-sdk', express.static('client-sdk')); // Also serve client-sdk specifically

// Demo API Key to Tenant ID mapping (for hackathon)
const API_KEY_TO_TENANT = {
    'demo-123': 'tenant_demo_company',
    'test-456': 'tenant_test_startup', 
    'hackathon-789': 'tenant_hackathon_example',
    'demo-default': 'tenant_default'
};

// Helper function to extract tenant ID from API key
function getTenantIdFromApiKey(apiKey) {
    const tenantId = API_KEY_TO_TENANT[apiKey];
    if (!tenantId) {
        console.warn(`Unknown API key: ${apiKey}, using default tenant`);
        return 'tenant_default';
    }
    return tenantId;
}

// Logging middleware
app.use((req, res, next) => {
    console.log(`${new Date().toISOString()} - ${req.method} ${req.path}`);
    next();
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        service: 'google-noculars-api'
    });
});

// Main tracking endpoint
app.post('/api/track', async (req, res) => {
    try {
        const { events, batchTimestamp, sessionId, apiKey } = req.body;

        if (!events || !Array.isArray(events) || events.length === 0) {
            return res.status(400).json({ 
                error: 'Invalid request: events array is required' 
            });
        }

        // Extract tenant ID from API key
        const tenantId = getTenantIdFromApiKey(apiKey);

        console.log(`Received batch of ${events.length} events for session ${sessionId} (tenant: ${tenantId})`);

        // Transform events to match BigQuery schema with tenant isolation
        const transformedEvents = events.map(event => ({
            session_id: event.sessionId || sessionId,
            page_url: event.pageUrl,
            user_agent: event.userAgent,
            viewport_width: event.viewportWidth,
            viewport_height: event.viewportHeight,
            event_type: event.eventType,
            timestamp: event.timestamp,
            x_coordinate: event.xCoordinate,
            y_coordinate: event.yCoordinate,
            scroll_x: event.scrollX,
            scroll_y: event.scrollY,
            element_tag: event.elementTag,
            element_id: event.elementId,
            element_class: event.elementClass,
            element_text: event.elementText,
            page_title: event.pageTitle,
            referrer: event.referrer,
            tenant_id: tenantId,  // Add tenant isolation
            created_at: new Date().toISOString()
        }));

        // Insert into BigQuery
        await insertEventsToBigQuery(transformedEvents);

        res.json({
            success: true,
            eventsProcessed: events.length,
            batchTimestamp: batchTimestamp,
            message: 'Events stored successfully'
        });

    } catch (error) {
        console.error('Error processing tracking data:', error);
        res.status(500).json({
            error: 'Internal server error',
            message: error.message
        });
    }
});

// Function to insert events into BigQuery
async function insertEventsToBigQuery(events) {
    try {
        console.log(`Inserting ${events.length} events into BigQuery...`);
        
        const [response] = await mouseTrackingTable.insert(events);
        
        console.log(`Successfully inserted ${events.length} events into BigQuery`);
        return response;
        
    } catch (error) {
        console.error('BigQuery insertion error:', error);
        
        // Log detailed error information
        if (error.errors && error.errors.length > 0) {
            console.error('BigQuery errors:', JSON.stringify(error.errors, null, 2));
        }
        
        throw error;
    }
}

// Analytics endpoint to query tracking data
app.get('/api/analytics/:sessionId', async (req, res) => {
    try {
        const { sessionId } = req.params;
        
        const query = `
            SELECT 
                event_type,
                COUNT(*) as event_count,
                MIN(timestamp) as first_event,
                MAX(timestamp) as last_event
            FROM \`ux_insights.mouse_tracking\`
            WHERE session_id = @sessionId
            GROUP BY event_type
            ORDER BY event_count DESC
        `;

        const [rows] = await bigquery.query({
            query: query,
            params: { sessionId: sessionId }
        });

        res.json({
            sessionId: sessionId,
            eventSummary: rows,
            totalEvents: rows.reduce((sum, row) => sum + row.event_count, 0)
        });

    } catch (error) {
        console.error('Error querying analytics:', error);
        
        // Check if it's a permission error
        if (error.message.includes('bigquery.jobs.create')) {
            res.status(403).json({
                error: 'BigQuery permission required',
                message: 'Service account needs bigquery.jobs.create permission for analytics queries',
                suggestion: 'Analytics endpoints are disabled until proper permissions are granted',
                tracking_status: 'Data insertion is working correctly'
            });
        } else {
            res.status(500).json({
                error: 'Failed to retrieve analytics',
                message: error.message
            });
        }
    }
});

// Get recent sessions
app.get('/api/sessions', async (req, res) => {
    try {
        const query = `
            SELECT 
                session_id,
                page_url,
                MIN(timestamp) as session_start,
                MAX(timestamp) as session_end,
                COUNT(*) as total_events
            FROM \`ux_insights.mouse_tracking\`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
            GROUP BY session_id, page_url
            ORDER BY session_start DESC
            LIMIT 50
        `;

        const [rows] = await bigquery.query(query);

        res.json({
            sessions: rows,
            count: rows.length
        });

    } catch (error) {
        console.error('Error querying sessions:', error);
        
        // Check if it's a permission error
        if (error.message.includes('bigquery.jobs.create')) {
            res.status(403).json({
                error: 'BigQuery permission required',
                message: 'Service account needs bigquery.jobs.create permission for analytics queries',
                suggestion: 'Analytics endpoints are disabled until proper permissions are granted',
                tracking_status: 'Data insertion is working correctly'
            });
        } else {
            res.status(500).json({
                error: 'Failed to retrieve sessions',
                message: error.message
            });
        }
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Unhandled error:', error);
    res.status(500).json({
        error: 'Internal server error',
        message: error.message
    });
});

// 404 handler
app.use((req, res) => {
    res.status(404).json({
        error: 'Not found',
        path: req.path
    });
});

// Start server
app.listen(port, () => {
    console.log(`🚀 Google Noculars API Server running on port ${port}`);
    console.log(`📊 Tracking endpoint: http://localhost:${port}/api/track`);
    console.log(`💡 Health check: http://localhost:${port}/health`);
    console.log(`📈 Analytics: http://localhost:${port}/api/analytics/{sessionId}`);
    console.log(`🔍 Recent sessions: http://localhost:${port}/api/sessions`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
    console.log('Received SIGTERM, shutting down gracefully...');
    process.exit(0);
});

process.on('SIGINT', () => {
    console.log('Received SIGINT, shutting down gracefully...');
    process.exit(0);
});

module.exports = app;