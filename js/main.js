/* =========================================================
   Afaq Real Estate Platform - Main Orchestrator (js/main.js)
   ========================================================= */

document.addEventListener('DOMContentLoaded', function() {
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
