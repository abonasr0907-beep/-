/**
 * PWA Install Prompt & Cookie Consent Manager
 * Afaq Al-Injaz Real Estate
 */

(function () {
  'use strict';

  // Config constants
  const CONFIG = {
    SHOW_DELAY_MS: 2000,      // 2 seconds delay before showing
    DISMISS_DURATION_MS: 10000, // 10 seconds display time
    REPEAT_INTERVAL_MS: 120000  // Repeat every 2 minutes until installed
  };

  let deferredPrompt = null;
  let promptTimer = null;
  let autoDismissTimer = null;
  let isInstalled = false;

  // Check if app is already running in standalone mode (installed)
  if (window.matchMedia('(display-mode: standalone)').matches || window.navigator.standalone === true) {
    isInstalled = true;
  }

  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
  });

  window.addEventListener('appinstalled', () => {
    isInstalled = true;
    hideInstallPrompt();
    if (window.trackCrmEvent) {
      window.trackCrmEvent('pwa_installed', { timestamp: new Date().toISOString() });
    }
  });

  function showInstallPrompt() {
    if (isInstalled || document.getElementById('pwa-install-prompt-el')) return;

    const promptEl = document.createElement('div');
    promptEl.id = 'pwa-install-prompt-el';
    promptEl.className = 'pwa-install-prompt';

    const lang = document.documentElement.lang || 'ar';
    const isEn = lang === 'en';

    promptEl.innerHTML = `
      <div class="pwa-prompt-header">
        <img src="/images/logo.png" alt="Afaq Al-Injaz Logo" class="pwa-prompt-icon" onerror="this.src='../images/logo.png'">
        <div class="pwa-prompt-text">
          <h4>${isEn ? 'Install Afaq Al-Injaz App' : 'تثبيت تطبيق آفاق الإنجاز'}</h4>
          <p>${isEn ? 'Fast access to Al-Kharj real estate listings' : 'وصول سريع ومباشر لعقارات ومزارع الخرج'}</p>
        </div>
      </div>
      <div class="pwa-prompt-actions">
        <button id="pwa-dismiss-btn" class="btn-pwa-dismiss">${isEn ? 'Later' : 'لاحقاً'}</button>
        <button id="pwa-install-btn" class="btn-pwa-install">${isEn ? 'Install' : 'تثبيت الآن'}</button>
      </div>
    `;

    document.body.appendChild(promptEl);

    if (window.trackCrmEvent) {
      window.trackCrmEvent('install_prompt_shown', { timestamp: new Date().toISOString() });
    }

    document.getElementById('pwa-install-btn').addEventListener('click', async () => {
      if (deferredPrompt) {
        deferredPrompt.prompt();
        const { outcome } = await deferredPrompt.userChoice;
        if (outcome === 'accepted') {
          isInstalled = true;
        }
        deferredPrompt = null;
      }
      hideInstallPrompt();
    });

    document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
      if (window.trackCrmEvent) {
        window.trackCrmEvent('install_prompt_dismissed', { timestamp: new Date().toISOString() });
      }
      hideInstallPrompt();
    });

    // Auto-dismiss after CONFIG.DISMISS_DURATION_MS (10s)
    autoDismissTimer = setTimeout(() => {
      hideInstallPrompt();
    }, CONFIG.DISMISS_DURATION_MS);
  }

  function hideInstallPrompt() {
    const promptEl = document.getElementById('pwa-install-prompt-el');
    if (promptEl) {
      promptEl.remove();
    }
    if (autoDismissTimer) {
      clearTimeout(autoDismissTimer);
      autoDismissTimer = null;
    }
  }

  function schedulePromptLoop() {
    // Initial trigger after 2 seconds
    setTimeout(() => {
      showInstallPrompt();

      // Repeat interval every 2 minutes (120,000 ms)
      promptTimer = setInterval(() => {
        if (!isInstalled) {
          showInstallPrompt();
        } else {
          clearInterval(promptTimer);
        }
      }, CONFIG.REPEAT_INTERVAL_MS);
    }, CONFIG.SHOW_DELAY_MS);
  }

  // Cookie Consent Banner Implementation
  function initCookieConsent() {
    if (localStorage.getItem('afaq_cookie_consent') === 'true') return;

    const consentBar = document.createElement('div');
    consentBar.id = 'cookie-consent-bar';
    consentBar.className = 'cookie-consent-bar';

    const lang = document.documentElement.lang || 'ar';
    const isEn = lang === 'en';

    consentBar.innerHTML = `
      <div class="cookie-consent-text">
        ${isEn
          ? 'We use cookies to enhance your experience. By continuing, you agree to our <a href="/privacy.html">Privacy Policy</a>.'
          : 'نستخدم ملفات تعريف الارتباط لتصفيح أفضل وقياس الأداء. بمتابعتك، أنت توافق على <a href="/privacy.html">سياسة الخصوصية</a>.'}
      </div>
      <button id="cookie-accept-btn" class="btn-cookie-accept">${isEn ? 'Accept' : 'موافقة'}</button>
    `;

    document.body.appendChild(consentBar);

    document.getElementById('cookie-accept-btn').addEventListener('click', () => {
      localStorage.setItem('afaq_cookie_consent', 'true');
      consentBar.remove();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    schedulePromptLoop();
    initCookieConsent();
  });
})();
