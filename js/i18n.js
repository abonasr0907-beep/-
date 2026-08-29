/**
 * Client-side Dynamic Language Switcher (i18n)
 * Afaq Al-Injaz Real Estate
 */

(function () {
  'use strict';

  const translations = {
    ar: {
      "nav_home": "الرئيسية",
      "nav_list_prop": "⭐ اعرض عقارك",
      "nav_offers": "العروض",
      "nav_services": "الخدمات",
      "nav_about": "عن المكتب",
      "nav_contact": "تواصل معنا",
      "hero_title": "مكتب أفاق الإنجاز العقاري بالخرج",
      "hero_subtitle": "عقارات، أراضي، مزارع، واستراحات فاخرة في الخرج والرياض",
      "office_location_title": "🏢 موقع المكتب الرئيسي",
      "office_directions": "📍 اتجاهات خرائط جوجل",
      "office_call": "📞 اتصل بالمكتب"
    },
    en: {
      "nav_home": "Home",
      "nav_list_prop": "⭐ List Property",
      "nav_offers": "Offers",
      "nav_services": "Services",
      "nav_about": "About Us",
      "nav_contact": "Contact",
      "hero_title": "Afaq Al-Injaz Real Estate Al-Kharj",
      "hero_subtitle": "Premium Land Plots, Farms, and Resthouses in Al-Kharj",
      "office_location_title": "🏢 Head Office Location",
      "office_directions": "📍 Google Maps Directions",
      "office_call": "📞 Call Office"
    }
  };

  let currentLang = localStorage.getItem('afaq_lang') || 'ar';

  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem('afaq_lang', lang);
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';

    const t = translations[lang] || translations.ar;

    // Translate navigation links if data-i18n attributes exist or by matching text
    const navLinks = document.querySelectorAll('.nav-menu a, nav a');
    if (navLinks.length >= 6) {
      if (navLinks[0]) navLinks[0].textContent = t.nav_home;
      if (navLinks[1]) navLinks[1].textContent = t.nav_list_prop;
      if (navLinks[2]) navLinks[2].textContent = t.nav_offers;
      if (navLinks[3]) navLinks[3].textContent = t.nav_services;
      if (navLinks[4]) navLinks[4].textContent = t.nav_about;
      if (navLinks[5]) navLinks[5].textContent = t.nav_contact;
    }

    const langBtn = document.getElementById('lang-switch-btn');
    if (langBtn) {
      langBtn.textContent = lang === 'ar' ? '🌐 English' : '🌐 العربية';
    }
  }

  function injectLangSwitcher() {
    if (document.getElementById('lang-switch-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'lang-switch-btn';
    btn.className = 'btn-lang-switcher';
    btn.style.cssText = 'position: fixed; top: 15px; left: 20px; z-index: 1300; background: rgba(20, 32, 43, 0.85); backdrop-filter: blur(8px); border: 1px solid rgba(199, 217, 181, 0.4); color: #c7d9b5; padding: 6px 14px; border-radius: 20px; font-weight: bold; font-size: 0.85rem; cursor: pointer; transition: all 0.2s ease;';
    btn.textContent = currentLang === 'ar' ? '🌐 English' : '🌐 العربية';

    btn.addEventListener('click', () => {
      const newLang = currentLang === 'ar' ? 'en' : 'ar';
      applyLanguage(newLang);
    });

    document.body.appendChild(btn);
  }

  document.addEventListener('DOMContentLoaded', () => {
    injectLangSwitcher();
    if (currentLang !== 'ar') {
      applyLanguage(currentLang);
    }
  });
})();
