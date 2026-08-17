/* =========================================================
   Afaq Real Estate Platform - Compare Module (js/compare.js)
   ========================================================= */

function getCompareList() {
    try {
        return JSON.parse(localStorage.getItem('afaq_compare') || '[]');
    } catch(e) { return []; }
}
window.getCompareList = getCompareList;

function updateCompareDrawer() {
    var drawer = document.getElementById('luxury-compare-drawer') || document.getElementById('compare-drawer');
    var badge = document.getElementById('compare-count-badge');
    var list = getCompareList();

    if (badge) badge.textContent = list.length;

    var itemsContainer = document.getElementById('compare-drawer-items');
    if (!itemsContainer) return;

    if (list.length === 0) {
        itemsContainer.innerHTML = '<p class="empty-msg">لم يتم اختيار أي عقارات للمقارنة</p>';
        return;
    }

    if (!window.allOffers) return;

    var compareOffers = window.allOffers.filter(function(o) { return list.includes(String(o.id || o.external_id)); });

    itemsContainer.innerHTML = compareOffers.map(function(o) {
        var title = window.escapeHtml(o.title || o.name || 'عقار');
        var img = (o.images && o.images[0]) || o.image || 'images/hero-bg.jpg';
        return '' +
        '<div class="compare-drawer-item">' +
            '<img src="' + window.escapeHtml(img) + '" alt="' + title + '" class="compare-thumb">' +
            '<div class="compare-item-info">' +
                '<h4>' + title + '</h4>' +
                '<span>' + (window.formatCurrency ? window.formatCurrency(o.price) : o.price) + '</span>' +
            '</div>' +
            '<button type="button" class="btn-remove-compare" onclick="window.toggleCardCompare(\'' + window.escapeHtml(o.id) + '\')"><i class="fas fa-times"></i></button>' +
        '</div>';
    }).join('');
}
window.updateCompareDrawer = updateCompareDrawer;
