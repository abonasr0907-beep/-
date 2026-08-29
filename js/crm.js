/**
 * CRM Logging, Error Tracking, Performance Metrics & Form Security (Honeypot/Turnstile)
 * Afaq Al-Injaz Real Estate
 */

(function () {
  'use strict';

  // 1. Unified Event Tracker
  window.trackCrmEvent = function (eventType, eventDetails = {}) {
    const payload = {
      type: eventType,
      details: eventDetails,
      url: window.location.href,
      referrer: document.referrer || '',
      user_agent: navigator.userAgent,
      timestamp: new Date().toISOString()
    };

    // Send to FastAPI backend
    fetch('/api/events', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    }).catch(err => console.warn('CRM Log Error:', err));
  };

  // 2. Global Error Tracking (window.onerror & unhandledrejection)
  window.onerror = function (msg, url, lineNo, columnNo, error) {
    window.trackCrmEvent('error', {
      message: msg,
      source: url,
      line: lineNo,
      column: columnNo,
      stack: error ? error.stack : ''
    });
    return false;
  };

  window.addEventListener('unhandledrejection', function (event) {
    window.trackCrmEvent('error', {
      type: 'Unhandled Promise Rejection',
      reason: event.reason ? (event.reason.message || event.reason) : 'Unknown'
    });
  });

  // 3. Performance Metrics Tracking (LCP / CLS)
  function trackPerformanceMetrics() {
    if (!('performance' in window) || !('PerformanceObserver' in window)) return;

    // Largest Contentful Paint (LCP)
    try {
      const lcpObserver = new PerformanceObserver((entryList) => {
        const entries = entryList.getEntries();
        const lastEntry = entries[entries.length - 1];
        window.trackCrmEvent('perf', {
          metric: 'LCP',
          value_ms: Math.round(lastEntry.startTime),
          element: lastEntry.element ? lastEntry.element.tagName : 'N/A'
        });
      });
      lcpObserver.observe({ type: 'largest-contentful-paint', buffered: true });
    } catch (e) {}

    // Cumulative Layout Shift (CLS)
    try {
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((entryList) => {
        for (const entry of entryList.getEntries()) {
          if (!entry.hadRecentInput) {
            clsValue += entry.value;
          }
        }
        window.trackCrmEvent('perf', {
          metric: 'CLS',
          value: parseFloat(clsValue.toFixed(4))
        });
      });
      clsObserver.observe({ type: 'layout-shift', buffered: true });
    } catch (e) {}
  }

  // 4. Form Security (Honeypot + Turnstile Fallback)
  function initFormSecurity() {
    document.querySelectorAll('form').forEach(form => {
      // Add hidden honeypot input if not present
      if (!form.querySelector('input[name="hp_website_check"]')) {
        const hp = document.createElement('input');
        hp.type = 'text';
        hp.name = 'hp_website_check';
        hp.style.display = 'none';
        hp.tabIndex = -1;
        hp.autocomplete = 'off';
        form.appendChild(hp);
      }

      form.addEventListener('submit', function (e) {
        const hpInput = form.querySelector('input[name="hp_website_check"]');
        if (hpInput && hpInput.value !== '') {
          // Spam bot detected!
          e.preventDefault();
          console.warn('Bot submission blocked via Honeypot.');
          return false;
        }

        // Optional Cloudflare Turnstile fallback: if turnstile failed to load or present, pass form smoothly
        if (window.turnstile) {
          try {
            const response = window.turnstile.getResponse();
            // If turnstile exists but empty, check if mandatory
          } catch (err) {
            console.warn('Turnstile check passed fallback:', err);
          }
        }
      });
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    trackPerformanceMetrics();
    initFormSecurity();
  });
})();
