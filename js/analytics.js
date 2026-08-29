/**
 * Analytics & GA4/GTM DataLayer Tracker
 * Afaq Al-Injaz Real Estate
 */

(function () {
  'use strict';

  // Initialize dataLayer safely
  window.dataLayer = window.dataLayer || [];

  function gtag() {
    window.dataLayer.push(arguments);
  }

  // Auto push pageview event
  window.dataLayer.push({
    event: 'page_view',
    page_title: document.title,
    page_location: window.location.href,
    page_path: window.location.pathname
  });

  // Track button interactions across the site
  document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', (e) => {
      const btn = e.target.closest('a, button, .btn, .card, [role="button"]');
      if (!btn) return;

      const btnText = (btn.innerText || btn.textContent || btn.getAttribute('aria-label') || '').trim();
      const btnHref = btn.getAttribute('href') || '';
      const btnId = btn.id || btn.className || '';

      // Determine action type
      let actionType = 'button_click';
      if (btnHref.includes('wa.me') || btnHref.includes('whatsapp')) {
        actionType = 'whatsapp_click';
        if (window.trackCrmEvent) window.trackCrmEvent('whatsapp_click', { text: btnText, target: btnHref });
      } else if (btnHref.startsWith('tel:')) {
        actionType = 'phone_click';
        if (window.trackCrmEvent) window.trackCrmEvent('inquiry', { type: 'phone', text: btnText });
      } else if (btn.classList.contains('star-fav-btn') || btnText.includes('⭐') || btnText.includes('مفضلة')) {
        actionType = 'favorite';
        if (window.trackCrmEvent) window.trackCrmEvent('favorite', { text: btnText });
      } else if (btnText.includes('مشاركة') || btnText.includes('share')) {
        actionType = 'share';
        if (window.trackCrmEvent) window.trackCrmEvent('share', { text: btnText });
      }

      window.dataLayer.push({
        event: actionType,
        button_text: btnText,
        button_target: btnHref,
        button_identifier: btnId,
        page_path: window.location.pathname
      });
    });
  });
})();
