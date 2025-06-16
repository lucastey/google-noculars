/**
 * Google Noculars - UX Tracking SDK
 * Lightweight JavaScript library for mouse movement and interaction tracking
 */

(function(window, document) {
    'use strict';

    class UXTracker {
        constructor(config = {}) {
            this.config = {
                apiEndpoint: config.apiEndpoint || '/api/track',
                batchSize: config.batchSize || 50,
                batchInterval: config.batchInterval || 10000, // 10 seconds
                mouseThrottleMs: config.mouseThrottleMs || 100, // 10 events/second max
                debug: config.debug || false,
                ...config
            };

            this.sessionId = this.generateSessionId();
            this.eventQueue = [];
            this.lastMouseEvent = 0;
            this.isInitialized = false;
            this.batchTimer = null;

            // Bind methods to maintain context
            this.handleMouseMove = this.throttle(this.handleMouseMove.bind(this), this.config.mouseThrottleMs);
            this.handleClick = this.handleClick.bind(this);
            this.handleScroll = this.throttle(this.handleScroll.bind(this), 200); // 5 events/second for scroll
            this.handlePageLoad = this.handlePageLoad.bind(this);
            this.handlePageUnload = this.handlePageUnload.bind(this);
        }

        init() {
            if (this.isInitialized) {
                this.log('Tracker already initialized');
                return;
            }

            this.log('Initializing UX Tracker', {
                sessionId: this.sessionId,
                config: this.config
            });

            this.attachEventListeners();
            this.startBatchTimer();
            this.trackPageLoad();
            this.isInitialized = true;

            this.log('UX Tracker initialized successfully');
        }

        generateSessionId() {
            // Simple UUID-like session ID generation
            return 'ux_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 9);
        }

        attachEventListeners() {
            // Mouse events
            document.addEventListener('mousemove', this.handleMouseMove, { passive: true });
            document.addEventListener('click', this.handleClick, { passive: true });
            
            // Scroll events
            window.addEventListener('scroll', this.handleScroll, { passive: true });
            
            // Page lifecycle events
            window.addEventListener('load', this.handlePageLoad, { passive: true });
            window.addEventListener('beforeunload', this.handlePageUnload);
            
            // Visibility change (tab switching)
            document.addEventListener('visibilitychange', () => {
                this.trackEvent('visibility_change', {
                    hidden: document.hidden
                });
            }, { passive: true });
        }

        handleMouseMove(event) {
            this.trackEvent('mouse_move', {
                x: event.clientX,
                y: event.clientY,
                target: this.getElementInfo(event.target)
            });
        }

        handleClick(event) {
            this.trackEvent('click', {
                x: event.clientX,
                y: event.clientY,
                target: this.getElementInfo(event.target),
                button: event.button
            });
        }

        handleScroll(event) {
            this.trackEvent('scroll', {
                scrollX: window.scrollX,
                scrollY: window.scrollY,
                target: this.getElementInfo(event.target)
            });
        }

        handlePageLoad() {
            this.trackEvent('page_load', {
                loadTime: performance.now(),
                referrer: document.referrer
            });
        }

        handlePageUnload() {
            // Send any remaining events before page unloads
            this.trackEvent('page_unload');
            this.sendBatch(true); // Force immediate send
        }

        trackPageLoad() {
            this.trackEvent('page_load', {
                url: window.location.href,
                title: document.title,
                referrer: document.referrer,
                userAgent: navigator.userAgent,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                }
            });
        }

        trackEvent(eventType, data = {}) {
            const baseEvent = {
                sessionId: this.sessionId,
                eventType: eventType,
                timestamp: new Date().toISOString(),
                pageUrl: window.location.href,
                pageTitle: document.title,
                viewportWidth: window.innerWidth,
                viewportHeight: window.innerHeight,
                userAgent: navigator.userAgent,
                referrer: document.referrer
            };

            // Map data to BigQuery schema
            const event = {
                ...baseEvent,
                xCoordinate: data.x || null,
                yCoordinate: data.y || null,
                scrollX: data.scrollX || null,
                scrollY: data.scrollY || null,
                elementTag: data.target?.tag || null,
                elementId: data.target?.id || null,
                elementClass: data.target?.class || null,
                elementText: data.target?.text || null,
                additionalData: JSON.stringify(data)
            };

            this.eventQueue.push(event);
            this.log('Event tracked:', eventType, event);

            // Send batch if queue is full
            if (this.eventQueue.length >= this.config.batchSize) {
                this.sendBatch();
            }
        }

        getElementInfo(element) {
            if (!element) return null;

            return {
                tag: element.tagName?.toLowerCase(),
                id: element.id || null,
                class: element.className || null,
                text: element.textContent?.trim().substring(0, 100) || null // Limit text length
            };
        }

        startBatchTimer() {
            if (this.batchTimer) {
                clearInterval(this.batchTimer);
            }

            this.batchTimer = setInterval(() => {
                if (this.eventQueue.length > 0) {
                    this.sendBatch();
                }
            }, this.config.batchInterval);
        }

        async sendBatch(forceSync = false) {
            if (this.eventQueue.length === 0) {
                return;
            }

            const events = [...this.eventQueue]; // Copy events
            this.eventQueue = []; // Clear queue

            this.log('Sending batch of', events.length, 'events');

            try {
                const response = await this.sendToAPI(events, forceSync);
                
                if (response.ok) {
                    this.log('Batch sent successfully');
                } else {
                    throw new Error(`API responded with status: ${response.status}`);
                }
            } catch (error) {
                this.log('Error sending batch:', error);
                
                // Re-queue events on failure (but limit retry queue size)
                if (this.eventQueue.length < this.config.batchSize) {
                    this.eventQueue.unshift(...events.slice(-this.config.batchSize));
                }
            }
        }

        async sendToAPI(events, forceSync = false) {
            const payload = {
                events: events,
                batchTimestamp: new Date().toISOString(),
                sessionId: this.sessionId
            };

            const options = {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            };

            if (forceSync && navigator.sendBeacon) {
                // Use sendBeacon for page unload to ensure delivery
                const blob = new Blob([JSON.stringify(payload)], { type: 'application/json' });
                navigator.sendBeacon(this.config.apiEndpoint, blob);
                return { ok: true }; // Assume success for beacon
            }

            return fetch(this.config.apiEndpoint, options);
        }

        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        }

        log(...args) {
            if (this.config.debug) {
                console.log('[UX Tracker]', ...args);
            }
        }

        // Public methods for manual tracking
        trackCustomEvent(eventName, data = {}) {
            this.trackEvent(`custom_${eventName}`, data);
        }

        // Cleanup method
        destroy() {
            if (this.batchTimer) {
                clearInterval(this.batchTimer);
            }

            // Send remaining events
            this.sendBatch(true);

            // Remove event listeners
            document.removeEventListener('mousemove', this.handleMouseMove);
            document.removeEventListener('click', this.handleClick);
            window.removeEventListener('scroll', this.handleScroll);
            window.removeEventListener('load', this.handlePageLoad);
            window.removeEventListener('beforeunload', this.handlePageUnload);

            this.isInitialized = false;
            this.log('UX Tracker destroyed');
        }
    }

    // Auto-initialize with default config
    const tracker = new UXTracker({
        debug: window.location.hostname === 'localhost' // Enable debug on localhost
    });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => tracker.init());
    } else {
        tracker.init();
    }

    // Expose tracker globally for manual control if needed
    window.UXTracker = UXTracker;
    window.uxTracker = tracker;

})(window, document);