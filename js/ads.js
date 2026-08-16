/**
 * Timid Ads System (M15 Growth)
 * Fetches data/ads.json and renders single ad banner in #ad-home / #ad-detail
 */
(function () {
  'use strict';

  const ADS_DATA_PATH = 'data/ads.json';
  const DISMISS_PREFIX = 'afaq_ad_closed_';
  const DISMISS_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours

  function isAdDismissed(adId) {
    try {
      const closedTime = localStorage.getItem(DISMISS_PREFIX + adId);
      if (!closedTime) return false;
      const elapsed = Date.now() - parseInt(closedTime, 10);
      return elapsed < DISMISS_DURATION_MS;
    } catch (e) {
      return false;
    }
  }

  function dismissAd(adId, container) {
    try {
      localStorage.setItem(DISMISS_PREFIX + adId, Date.now().toString());
    } catch (e) {}
    if (container) {
      container.classList.add('hidden');
      container.innerHTML = '';
    }
  }

  function isAdActive(ad) {
    if (!ad || ad.active === false) return false;
    const now = new Date();
    if (ad.from) {
      const fromDate = new Date(ad.from);
      if (now < fromDate) return false;
    }
    if (ad.to) {
      const toDate = new Date(ad.to);
      toDate.setHours(23, 59, 59, 999);
      if (now > toDate) return false;
    }
    return true;
  }

  async function renderAdBanner(containerId, placement) {
    const container = document.getElementById(containerId);
    if (!container) return;

    try {
      const resp = await fetch(ADS_DATA_PATH);
      if (!resp.ok) {
        container.classList.add('hidden');
        return;
      }
      const data = await resp.json();
      const adsList = (data && data.ads) || [];

      // Filter matching active & non-dismissed ad
      const eligibleAds = adsList.filter((ad) => {
        if (!isAdActive(ad)) return false;
        if (isAdDismissed(ad.id)) return false;
        if (ad.placement && ad.placement !== 'all' && ad.placement !== placement) {
          return false;
        }
        return true;
      });

      if (eligibleAds.length === 0) {
        container.classList.add('hidden');
        container.innerHTML = '';
        return;
      }

      // Pick the first matching ad
      const selectedAd = eligibleAds[0];

      const html = `
        <div class="timid-ad-box">
          <button class="timid-ad-close" title="إغلاق الإعلان لمدة 24 ساعة" aria-label="إغلاق">&times;</button>
          <a href="${selectedAd.link || '#'}" target="_blank" rel="noopener noreferrer" class="timid-ad-link">
            <img src="${selectedAd.image || 'images/logo.jpg'}" alt="${selectedAd.title || 'إعلان'}" class="timid-ad-img" loading="lazy">
            <div class="timid-ad-content">
              <div class="timid-ad-badge-wrap">
                <span class="timid-ad-badge">إعلان</span>
              </div>
              <h4 class="timid-ad-title">${selectedAd.title || ''}</h4>
            </div>
          </a>
        </div>
      `;

      container.innerHTML = html;
      container.classList.remove('hidden');

      const closeBtn = container.querySelector('.timid-ad-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          dismissAd(selectedAd.id, container);
        });
      }
    } catch (e) {
      container.classList.add('hidden');
      container.innerHTML = '';
    }
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderAdBanner('ad-home', 'home');
    renderAdBanner('ad-detail', 'detail');
  });
})();
