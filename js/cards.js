/* =========================================================
   Afaq Real Estate Platform - Cards Module (js/cards.js - v6)
   Unified Bayut-Style Renderer v5
   ========================================================= */

var CARD_BASE_URL = window.SITE_BASE_URL || 'https://abonasr0907-beep.github.io/-/';

function normalizeImgSrc(src) {
    if (!src || src === 'undefined' || src === 'null' || src === '–') {
        return CARD_BASE_URL + 'images/hero-bg.jpg';
    }
    var str = String(src).trim();
    if (str.startsWith('http://') || str.startsWith('https://') || str.startsWith('data:')) {
        return str;
    }
    if (str.startsWith('/')) {
        return CARD_BASE_URL + str.substring(1);
    }
    return CARD_BASE_URL + str;
}
window.normalizeImgSrc = normalizeImgSrc;

// Favorites logic
function isCardFav(id) {
    try {
        var favs = JSON.parse(localStorage.getItem('afaq_favs') || '[]');
        return favs.includes(String(id));
    } catch (e) { return false; }
}
window.isCardFav = isCardFav;

function toggleCardFav(id, btn) {
    try {
        var favs = JSON.parse(localStorage.getItem('afaq_favs') || '[]');
        var strId = String(id);
        var idx = favs.indexOf(strId);
        var isFavNow = false;
        if (idx >= 0) {
            favs.splice(idx, 1);
        } else {
            favs.push(strId);
            isFavNow = true;
        }
        localStorage.setItem('afaq_favs', JSON.stringify(favs));

        if (btn) {
            btn.classList.toggle('active', isFavNow);
            var icon = btn.querySelector('i');
            if (icon) {
                icon.className = isFavNow ? 'fas fa-heart' : 'far fa-heart';
            }
        }
        if (window.showToast) window.showToast(isFavNow ? 'تمت الإضافة للمفضلة' : 'تمت الإزالة من المفضلة', 'info');
    } catch (e) { console.warn('Fav toggle error', e); }
}
window.toggleCardFav = toggleCardFav;

// Comparison logic
function isCardCompare(id) {
    try {
        var comps = JSON.parse(localStorage.getItem('afaq_compare') || '[]');
        return comps.includes(String(id));
    } catch (e) { return false; }
}
window.isCardCompare = isCardCompare;

function toggleCardCompare(id, btn) {
    try {
        var comps = JSON.parse(localStorage.getItem('afaq_compare') || '[]');
        var strId = String(id);
        var idx = comps.indexOf(strId);
        var isCompNow = false;
        if (idx >= 0) {
            comps.splice(idx, 1);
        } else {
            if (comps.length >= 4) {
                if (window.showToast) window.showToast('يمكنك مقارنة 4 عقارات كحد أقصى', 'warning');
                return;
            }
            comps.push(strId);
            isCompNow = true;
        }
        localStorage.setItem('afaq_compare', JSON.stringify(comps));

        if (btn) {
            btn.classList.toggle('active', isCompNow);
        }
        if (window.showToast) window.showToast(isCompNow ? 'تمت إضافة العقار للمقارنة' : 'تمت إزالة العقار من المقارنة', 'info');
        if (window.updateCompareDrawer) window.updateCompareDrawer();
    } catch (e) { console.warn('Compare toggle error', e); }
}
window.toggleCardCompare = toggleCardCompare;

// Inspection Modal Helper
function openInspectionModal(id, title) {
    if (window.openBookingModal) {
        window.openBookingModal(id, title);
    } else {
        var msg = 'طلب حجز معاينة للعقار رقم ' + id + (title ? ' (' + title + ')' : '');
        var waPhone = (window.OFFICE_DATA && window.OFFICE_DATA.whatsapp) ? window.OFFICE_DATA.whatsapp : '0545888931';
        if (window.openWhatsAppFast) {
            window.openWhatsAppFast(waPhone, msg);
        } else {
            window.open('https://wa.me/966' + waPhone.replace(/^0/, '') + '?text=' + encodeURIComponent(msg), '_blank');
        }
    }
}
window.openInspectionModal = openInspectionModal;

// Share Helper
function shareOfferLink(id, title, url) {
    var fullUrl = url.startsWith('http') ? url : CARD_BASE_URL + url.replace(/^\//, '');
    if (navigator.share) {
        navigator.share({ title: title || 'عرض عقاري', url: fullUrl }).catch(function(){});
    } else if (navigator.clipboard) {
        navigator.clipboard.writeText(fullUrl).then(function() {
            if (window.showToast) window.showToast('تم نسخ رابط العرض', 'info');
        });
    }
}
window.shareOfferLink = shareOfferLink;

// Specs Chips Builder - STRICTLY drops missing/undefined/– values
function buildSpecChipsHTML(offer) {
    if (!offer) return '';
    var chips = [];

    // Area / المساحة
    var area = offer.area || offer.land_area || offer.building_area || offer.size || offer.size_sqm;
    if (area && area !== 'undefined' && area !== '–' && !isNaN(parseFloat(area)) && parseFloat(area) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-ruler-combined"></i> ' + escapeHtml(area) + ' م²</span>');
    }

    // Rooms / الغرف
    var rooms = offer.rooms || offer.bedrooms || offer.beds;
    if (rooms && rooms !== 'undefined' && rooms !== '–' && !isNaN(parseInt(rooms)) && parseInt(rooms) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-bed"></i> ' + escapeHtml(rooms) + ' غرف</span>');
    }

    // Bathrooms / دورات المياه
    var baths = offer.bathrooms || offer.baths;
    if (baths && baths !== 'undefined' && baths !== '–' && !isNaN(parseInt(baths)) && parseInt(baths) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-bath"></i> ' + escapeHtml(baths) + ' حمامات</span>');
    }

    // Street Width / عرض الشارع
    var street = offer.street_width || offer.street;
    if (street && street !== 'undefined' && street !== '–' && !isNaN(parseFloat(street)) && parseFloat(street) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-road"></i> شارع ' + escapeHtml(street) + 'م</span>');
    }

    // Age / العمر
    var age = offer.age || offer.building_age;
    if (age && age !== 'undefined' && age !== '–' && age !== 'جديد' && !isNaN(parseInt(age)) && parseInt(age) >= 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-calendar"></i> ' + (parseInt(age) === 0 ? 'جديد' : escapeHtml(age) + ' سنوات') + '</span>');
    } else if (age === 'جديد') {
        chips.push('<span class="spec-chip"><i class="fas fa-sparkles"></i> جديد</span>');
    }

    return chips.join('');
}
window.buildSpecChipsHTML = buildSpecChipsHTML;

// Unified Card Renderer v5
function createOfferCardHTML(offer, index) {
    if (!offer) return '';
    var id = offer.id || offer.external_id || index;
    var extId = offer.external_id || offer.id || id;
    var detailUrl = window.offerDetailLink ? window.offerDetailLink(offer) : 'property.html?id=' + extId;

    // Images
    var imgs = [];
    if (Array.isArray(offer.images) && offer.images.length > 0) {
        imgs = offer.images.filter(Boolean);
    } else if (offer.image) {
        imgs = [offer.image];
    }
    if (imgs.length === 0) {
        imgs = [CARD_BASE_URL + 'images/hero-bg.jpg'];
    }

    var isFav = isCardFav(id);
    var isComp = isCardCompare(id);
    var isSold = offer.status === 'مباع' || offer.sold === true;
    var isVerified = offer.verified !== false;
    var title = offer.title || offer.name || offer.type || offer.category || 'عرض عقاري مميز';
    if (title === 'undefined' || title === '–') title = 'عرض عقاري مميز';

    var priceSAR = offer.price || offer.total_price || 0;
    var priceFormatted = offer.price_text;
    if (!priceFormatted || priceFormatted === 'undefined' || priceFormatted === '–') {
        priceFormatted = priceSAR ? (window.formatCurrency ? window.formatCurrency(priceSAR) : (priceSAR + ' ر.س')) : 'السعر عند الاتصال';
    }

    var city = offer.city;
    if (!city || city === 'undefined' || city === '–') city = 'الخرج';
    var neighborhood = offer.neighborhood || offer.district || offer.area || '';
    if (neighborhood === 'undefined' || neighborhood === '–') neighborhood = '';
    var locationText = (neighborhood ? neighborhood + '، ' : '') + city;

    var videoUrl = offer.video_url || offer.youtube_url || offer.video || '';
    if (videoUrl === 'undefined' || videoUrl === '–') videoUrl = '';

    var fallbackImg = CARD_BASE_URL + 'images/hero-bg.jpg';

    // Gallery Track HTML
    var slidesHTML = imgs.map(function(src, i) {
        var fullSrc = normalizeImgSrc(src);
        return '<div class="gallery-slide"><img src="' + escapeHtml(fullSrc) + '" onerror="this.onerror=null;this.src=\'' + escapeHtml(fallbackImg) + '\';" alt="' + escapeHtml(title) + '" class="gallery-slide-img" loading="' + (i === 0 ? 'eager' : 'lazy') + '"></div>';
    }).join('');

    // Dots HTML
    var dotsHTML = '';
    if (imgs.length > 1) {
        dotsHTML = '<div class="gallery-dots">' + imgs.map(function(_, i) {
            return '<span class="dot ' + (i === 0 ? 'active' : '') + '"></span>';
        }).join('') + '</div>';
    }

    var specChips = buildSpecChipsHTML(offer);
    var waPhone = (window.OFFICE_DATA && window.OFFICE_DATA.whatsapp) ? window.OFFICE_DATA.whatsapp : '0545888931';
    var mapLink = offer.map_link || 'https://urldra.cloud.huawei.com/BExUoXngu4';

    return '' +
    '<a href="' + escapeHtml(detailUrl) + '" class="property-card-bayut ' + (isSold ? 'sold-card' : '') + '" data-id="' + escapeHtml(id) + '">' +
        '<div class="card-gallery-wrapper">' +
            '<div class="gallery-track" onscroll="handleGalleryScroll(this)">' +
                slidesHTML +
            '</div>' +
            dotsHTML +
            '<div class="card-badges-top">' +
                (isVerified ? '<span class="afaq-verified-badge"><i class="fas fa-check-circle"></i> موثّق آفاق ✔</span>' : '') +
                (isSold ? '<span class="sold-badge"><i class="fas fa-tag"></i> مُباع</span>' : '') +
            '</div>' +
            '<div class="card-actions-overlay">' +
                '<button type="button" class="btn-action-touch btn-fav ' + (isFav ? 'active' : '') + '" title="حفظ العرض" onclick="event.preventDefault(); event.stopPropagation(); toggleCardFav(\'' + escapeHtml(id) + '\', this);">' +
                    '<i class="' + (isFav ? 'fas' : 'far') + ' fa-heart"></i>' +
                '</button>' +
                (videoUrl ? '<button type="button" class="btn-action-touch btn-video" title="جولة فيديو" onclick="event.preventDefault(); event.stopPropagation(); openVideoModal(\'' + escapeHtml(videoUrl) + '\');"><i class="fas fa-play"></i> 🎬</button>' : '') +
                '<button type="button" class="btn-action-touch btn-wa" title="تواصل واتساب" onclick="event.preventDefault(); event.stopPropagation(); openWhatsAppFast(\'' + waPhone + '\', \'استفسار عن العرض رقم ' + escapeHtml(id) + ': ' + escapeHtml(title) + '\');">' +
                    '<i class="fab fa-whatsapp"></i>' +
                '</button>' +
            '</div>' +
        '</div>' +
        '<div class="card-content-body">' +
            '<div class="card-price-22">' + escapeHtml(priceFormatted) + '</div>' +
            '<h3 class="card-title-15">' + escapeHtml(title) + '</h3>' +
            '<div class="card-location-text"><i class="fas fa-map-marker-alt"></i> ' + escapeHtml(locationText) + '</div>' +
            (specChips ? '<div class="card-specs-12">' + specChips + '</div>' : '') +
        '</div>' +
        '<div class="card-bottom-actions-bar" onclick="event.preventDefault(); event.stopPropagation();">' +
            '<button type="button" class="card-action-bar-btn btn-appointment" title="حجز معاينة" onclick="event.preventDefault(); event.stopPropagation(); openInspectionModal(\'' + escapeHtml(id) + '\', \'' + escapeHtml(title) + '\');">' +
                '<i class="fas fa-calendar-check"></i> حجز معاينة' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-wa-bar" title="واتساب" onclick="event.preventDefault(); event.stopPropagation(); openWhatsAppFast(\'' + waPhone + '\', \'استفسار عن العرض رقم ' + escapeHtml(id) + ': ' + escapeHtml(title) + '\');">' +
                '<i class="fab fa-whatsapp"></i> واتساب' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-call-bar" title="اتصال" onclick="event.preventDefault(); event.stopPropagation(); window.location.href=\'tel:0544699933\';">' +
                '<i class="fas fa-phone-alt"></i> اتصال' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-fav-bar ' + (isFav ? 'active' : '') + '" title="حفظ" onclick="event.preventDefault(); event.stopPropagation(); toggleCardFav(\'' + escapeHtml(id) + '\', this);">' +
                '<i class="' + (isFav ? 'fas' : 'far') + ' fa-heart"></i> المفضلة' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-compare-bar ' + (isComp ? 'active' : '') + '" title="مقارنة" onclick="event.preventDefault(); event.stopPropagation(); toggleCardCompare(\'' + escapeHtml(id) + '\', this);">' +
                '<i class="fas fa-balance-scale"></i> مقارنة' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-video-bar" title="جولة فيديو" onclick="event.preventDefault(); event.stopPropagation(); ' + (videoUrl ? 'openVideoModal(\'' + escapeHtml(videoUrl) + '\');' : 'alert(\'لا يوجد فيديو متاح لهذا العرض\');') + '">' +
                '<i class="fas fa-play-circle"></i> فيديو' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-map-bar" title="الخريطة" onclick="event.preventDefault(); event.stopPropagation(); window.open(\'' + escapeHtml(mapLink) + '\', \'_blank\');">' +
                '<i class="fas fa-map-marked-alt"></i> الخريطة' +
            '</button>' +
            '<button type="button" class="card-action-bar-btn btn-share-bar" title="مشاركة" onclick="event.preventDefault(); event.stopPropagation(); shareOfferLink(\'' + escapeHtml(id) + '\', \'' + escapeHtml(title) + '\', \'' + escapeHtml(detailUrl) + '\');">' +
                '<i class="fas fa-share-alt"></i> مشاركة' +
            '</button>' +
        '</div>' +
    '</a>';
}
window.createOfferCardHTML = createOfferCardHTML;

// Gallery dots scroll listener
function handleGalleryScroll(track) {
    var dots = track.parentElement.querySelectorAll('.gallery-dots .dot');
    if (!dots || dots.length === 0) return;
    var index = Math.round(track.scrollLeft / track.clientWidth);
    dots.forEach(function(dot, idx) {
        dot.classList.toggle('active', idx === index);
    });
}
window.handleGalleryScroll = handleGalleryScroll;

// Most Viewed Bar
function trackOfferView(id) {
    try {
        var views = JSON.parse(localStorage.getItem('afaq_weekly_views') || '{}');
        views[id] = (views[id] || 0) + 1;
        localStorage.setItem('afaq_weekly_views', JSON.stringify(views));
    } catch (e) {}
}
window.trackOfferView = trackOfferView;

function renderMostViewedBar() {
    var container = document.getElementById('most-viewed-container');
    if (!container || !window.allOffers) return;
    try {
        var views = JSON.parse(localStorage.getItem('afaq_weekly_views') || '{}');
        var sorted = window.allOffers.slice().sort(function(a, b) {
            return (views[b.id] || 0) - (views[a.id] || 0);
        }).slice(0, 5);
        if (sorted.length > 0) {
            container.innerHTML = sorted.map(function(o) {
                return '<a href="' + window.offerDetailLink(o) + '" class="most-viewed-chip"><i class="fas fa-fire"></i> ' + escapeHtml(o.title || o.name || 'عرض مميز') + '</a>';
            }).join('');
        }
    } catch (e) {}
}
window.renderMostViewedBar = renderMostViewedBar;

// Lightbox
function initLightbox() {}
window.initLightbox = initLightbox;

// Detail Page Touch Swipe Gesture (50px threshold, 250ms slide, progress dots)
function initDetailSwipeGesture() {
    var container = document.querySelector('.property-detail-container') || document.querySelector('.property-container') || document.getElementById('property-detail');
    if (!container) return;

    var startX = 0, startY = 0, deltaX = 0, deltaY = 0;
    var threshold = 50;

    var progressContainer = document.getElementById('detail-swipe-progress');
    if (!progressContainer) {
        progressContainer = document.createElement('div');
        progressContainer.id = 'detail-swipe-progress';
        progressContainer.className = 'detail-swipe-progress';
        if (container.firstChild) {
            container.insertBefore(progressContainer, container.firstChild);
        } else {
            container.appendChild(progressContainer);
        }
    }

    var offersList = window.allOffers && window.allOffers.length > 0 ? window.allOffers : (window.getDefaultOffers ? window.getDefaultOffers() : []);
    var currentOfferId = window.currentProperty ? String(window.currentProperty.id || window.currentProperty.external_id) : '';
    var currentIndex = offersList.findIndex(function(o) {
        return String(o.id || o.external_id) === currentOfferId;
    });
    if (currentIndex < 0) currentIndex = 0;

    progressContainer.innerHTML = offersList.slice(0, 8).map(function(_, idx) {
        return '<span class="swipe-progress-dot ' + (idx === currentIndex ? 'active' : '') + '"></span>';
    }).join('');

    container.addEventListener('touchstart', function(e) {
        if (e.touches.length !== 1) return;
        startX = e.touches[0].clientX;
        startY = e.touches[0].clientY;
        deltaX = 0;
        deltaY = 0;
    }, { passive: true });

    container.addEventListener('touchmove', function(e) {
        if (e.touches.length !== 1) return;
        deltaX = e.touches[0].clientX - startX;
        deltaY = e.touches[0].clientY - startY;
    }, { passive: true });

    container.addEventListener('touchend', function(e) {
        if (Math.abs(deltaX) >= threshold && Math.abs(deltaX) > Math.abs(deltaY)) {
            container.style.transition = 'transform 250ms ease-in-out, opacity 250ms ease-in-out';
            if (deltaX < 0) {
                var nextIndex = (currentIndex + 1) % offersList.length;
                var nextOffer = offersList[nextIndex];
                container.style.transform = 'translateX(-100px)';
                container.style.opacity = '0.4';
                setTimeout(function() {
                    window.location.href = window.offerDetailLink ? window.offerDetailLink(nextOffer) : 'property.html?id=' + (nextOffer.external_id || nextOffer.id);
                }, 250);
            } else {
                var prevIndex = (currentIndex - 1 + offersList.length) % offersList.length;
                var prevOffer = offersList[prevIndex];
                container.style.transform = 'translateX(100px)';
                container.style.opacity = '0.4';
                setTimeout(function() {
                    window.location.href = window.offerDetailLink ? window.offerDetailLink(prevOffer) : 'property.html?id=' + (prevOffer.external_id || prevOffer.id);
                }, 250);
            }
        }
    }, { passive: true });
}
window.initDetailSwipeGesture = initDetailSwipeGesture;
