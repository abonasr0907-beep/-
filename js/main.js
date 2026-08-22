/* =========================================================
   Afaq Real Estate Platform - Main Orchestrator (js/main.js)
   Extended: inject site-wide SEO metadata + footer social/map
   ========================================================= */

document.addEventListener('DOMContentLoaded', function() {
    // Inject SEO metadata and footer social/map where missing
    try {
        if (typeof injectSeo === 'function') injectSeo();
    } catch(e) { /* ignore */ }

    // 1. Initialize utilities & settings
    if (window.initWhatsappChannel) window.initWhatsappChannel();
    if (window.initDarkMode) window.initDarkMode();
    if (window.setupMobileSidebar) window.setupMobileSidebar();
    if (window.cleanCanonicalUrl) window.cleanCanonicalUrl();
    if (window.initGoogleSiteVerification) window.initGoogleSiteVerification();

    // 2. Load Offers & render UI components
    if (window.loadOffers) {
        window.loadOffers().then(function() {
            if (window.renderRecentlyViewed) window.renderRecentlyViewed();
            if (window.renderStories) window.renderStories();
            if (window.renderMostViewedBar) window.renderMostViewedBar();
        });
    }

    // 3. Initialize Interactive Features
    if (window.initVoiceSearch) window.initVoiceSearch();
    if (window.initFloatingMapToggle) window.initFloatingMapToggle();
    if (window.updateCompareDrawer) window.updateCompareDrawer();

    // 4. Bind Search & Filter Listeners
    var searchInput = document.getElementById('search-input');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            if (window.filterOffers) window.filterOffers();
        });
    }

    var filterElements = document.querySelectorAll('#filter-status, #filter-area, #filter-category, #filter-sort');
    filterElements.forEach(function(el) {
        el.addEventListener('change', function() {
            if (window.filterOffers) window.filterOffers();
        });
    });

    console.log('Afaq Platform JS initialized successfully.');
});

// === SEO injection helper ===
function injectSeo() {
    // Add Open Graph / Twitter meta tags if missing
    var head = document.head || document.getElementsByTagName('head')[0];
    if (!head) return;

    function ensureMeta(property, attr, content) {
        var sel = (attr === 'property') ? 'meta['+attr+'="'+property+'"]' : 'meta[name="'+property+'"]';
        if (!document.querySelector(sel)) {
            var m = document.createElement('meta');
            m.setAttribute(attr, property);
            m.setAttribute('content', content);
            head.appendChild(m);
        }
    }

    ensureMeta('og:title', 'property', 'مكتب آفاق الإنجاز العقاري | مزارع واستراحات وأراضي بالخرج');
    ensureMeta('og:description', 'property', 'رخصة فال 1100004208 — مزارع، استراحات، أراضي سكنية في الخرج والرياض');
    ensureMeta('og:image', 'property', 'https://abonasr0907-beep.github.io/-/images/logo.jpg');
    ensureMeta('og:url', 'property', window.location.origin + '/-/');
    ensureMeta('og:type', 'property', 'website');
    ensureMeta('og:locale', 'property', 'ar_SA');

    ensureMeta('twitter:card', 'name', 'summary_large_image');
    ensureMeta('twitter:title', 'name', 'مكتب آفاق الإنجاز العقاري');
    ensureMeta('twitter:description', 'name', 'رخصة فال 1100004208 — الخرج والرياض');
    ensureMeta('twitter:image', 'name', 'https://abonasr0907-beep.github.io/-/images/logo.jpg');

    // Add RealEstateAgent JSON-LD if not present
    if (!document.getElementById('site-realestateagent-jsonld')) {
        var ld = {
            "@context": "https://schema.org",
            "@type": "RealEstateAgent",
            "name": "مكتب آفاق الإنجاز العقاري",
            "alternateName": "آفاق الإنجاز العقاري",
            "url": window.location.origin + '/-/',
            "logo": window.location.origin + '/-/images/logo.jpg',
            "image": window.location.origin + '/-/images/logo.jpg',
            "telephone": "+966545888931",
            "priceRange": "$$",
            "address": {"@type":"PostalAddress","addressLocality":"الخرج","addressRegion":"منطقة الرياض","addressCountry":"SA"},
            "geo": {"@type":"GeoCoordinates","latitude":"24.1500","longitude":"47.3333"},
            "openingHours":"Mo-Su 08:00-22:00",
            "sameAs":["https://www.instagram.com/afaqalanqaz","https://www.tiktok.com/@whatyouarelookingforisw3","https://www.snapchat.com/add/mmnf2278"],
            "areaServed":["الخرج","الدلم","الرحمانية","الهياثم","الضبيعة","العفجة"],
            "description":"مكتب آفاق الإنجاز العقاري — رخصة فال 1100004208. مزارع، استراحات، أراضي سكنية في الخرج والرياض."
        };
        var s = document.createElement('script');
        s.type = 'application/ld+json';
        s.id = 'site-realestateagent-jsonld';
        s.textContent = JSON.stringify(ld);
        head.appendChild(s);
    }

    // Inject footer social links + google maps iframe if footer exists and not already injected
    var footer = document.querySelector('footer.footer');
    if (footer && !footer.classList.contains('seo-injected')) {
        var socialHtml = '\n  <div style="max-width:1200px;margin:12px auto 0;display:flex;gap:12px;align-items:center;justify-content:space-between;">\n    <div style="display:flex;gap:12px;align-items:center;">\n      <a href="https://www.instagram.com/afaqalanqaz" target="_blank">📸 Instagram</a>\n      <a href="https://www.tiktok.com/@whatyouarelookingforisw3" target="_blank">🎵 TikTok</a>\n      <a href="https://www.snapchat.com/add/mmnf2278" target="_blank">👻 Snapchat</a>\n    </div>\n  </div>\n  <div style="max-width:1200px;margin:12px auto 0;">\n    <iframe src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3624.5!2d47.3333!3d24.1500!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x0%3A0x0!2z2YXYtdmI2LHYqSDYp9mE2YXYqtmI2K8g2KfZhNmC2LnZh9ix!5e0!3m2!1sar!2ssa!4v1724163600000!5m2!1sar!2ssa" width="100%" height="200" style="border:0;" allowfullscreen="" loading="lazy"></iframe>\n  </div>\n';
        footer.insertAdjacentHTML('beforeend', socialHtml);
        footer.classList.add('seo-injected');
    }
}
