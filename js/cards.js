/* =========================================================
   Afaq Real Estate Platform - Cards Module (js/cards.js)
   Bayut-Style Card Rendering & Specs Formatting
   ========================================================= */

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
        window.showToast(isFavNow ? 'تمت الإضافة للمفضلة' : 'تمت الإزالة من المفضلة', 'info');
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
                window.showToast('يمكنك مقارنة 4 عقارات كحد أقصى', 'warning');
                return;
            }
            comps.push(strId);
            isCompNow = true;
        }
        localStorage.setItem('afaq_compare', JSON.stringify(comps));

        if (btn) {
            btn.classList.toggle('active', isCompNow);
        }
        window.showToast(isCompNow ? 'تمت إضافة العقار للمقارنة' : 'تمت إزالة العقار من المقارنة', 'info');
        if (window.updateCompareDrawer) window.updateCompareDrawer();
    } catch (e) { console.warn('Compare toggle error', e); }
}
window.toggleCardCompare = toggleCardCompare;

// Specs Chips Builder - STRICTLY drops missing values
function buildSpecChipsHTML(offer) {
    if (!offer) return '';
    var chips = [];

    // Area / المساحة
    var area = offer.area || offer.land_area || offer.building_area || offer.size;
    if (area && !isNaN(parseFloat(area)) && parseFloat(area) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-ruler-combined"></i> ' + escapeHtml(area) + ' م²</span>');
    }

    // Rooms / الغرف
    var rooms = offer.rooms || offer.bedrooms || offer.beds;
    if (rooms && !isNaN(parseInt(rooms)) && parseInt(rooms) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-bed"></i> ' + escapeHtml(rooms) + ' غرف</span>');
    }

    // Bathrooms / دورات المياه
    var baths = offer.bathrooms || offer.baths;
    if (baths && !isNaN(parseInt(baths)) && parseInt(baths) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-bath"></i> ' + escapeHtml(baths) + ' حمامات</span>');
    }

    // Street Width / عرض الشارع
    var street = offer.street_width || offer.street;
    if (street && !isNaN(parseFloat(street)) && parseFloat(street) > 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-road"></i> شارع ' + escapeHtml(street) + 'م</span>');
    }

    // Age / العمر
    var age = offer.age || offer.building_age;
    if (age && age !== 'جديد' && !isNaN(parseInt(age)) && parseInt(age) >= 0) {
        chips.push('<span class="spec-chip"><i class="fas fa-calendar"></i> ' + (parseInt(age) === 0 ? 'جديد' : escapeHtml(age) + ' سنوات') + '</span>');
    } else if (age === 'جديد') {
        chips.push('<span class="spec-chip"><i class="fas fa-sparkles"></i> جديد</span>');
    }

    return chips.join('');
}
window.buildSpecChipsHTML = buildSpecChipsHTML;

// Bayut Card Renderer
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
        imgs = ['images/hero-bg.jpg'];
    }

    var isFav = isCardFav(id);
    var isComp = isCardCompare(id);
    var isSold = offer.status === 'مباع';
    var isVerified = offer.verified !== false; // Default true for Afaq properties
    var title = offer.title || offer.name || offer.type || 'عرض عقاري مميز';
    var priceSAR = offer.price || offer.total_price || 0;
    var priceFormatted = window.formatCurrency ? window.formatCurrency(priceSAR) : (priceSAR + ' ر.س');
    var city = offer.city || 'الخرج';
    var neighborhood = offer.neighborhood || offer.district || '';
    var locationText = (neighborhood ? neighborhood + '، ' : '') + city;
    var videoUrl = offer.video_url || offer.youtube_url || offer.video;

    // Gallery Track HTML
    var slidesHTML = imgs.map(function(src, i) {
        return '<div class="gallery-slide" style="background-image: url(\'' + escapeHtml(src) + '\');"></div>';
    }).join('');

    // Dots HTML
    var dotsHTML = '';
    if (imgs.length > 1) {
        dotsHTML = '<div class="gallery-dots">' + imgs.map(function(_, i) {
            return '<span class="dot ' + (i === 0 ? 'active' : '') + '"></span>';
        }).join('') + '</div>';
    }

    var specChips = buildSpecChipsHTML(offer);

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
                (videoUrl ? '<button type="button" class="btn-action-touch btn-video" title="جولة فيديو" onclick="event.preventDefault(); event.stopPropagation(); openVideoModal(\'' + escapeHtml(videoUrl) + '\');"><i class="fas fa-play"></i></button>' : '') +
                '<button type="button" class="btn-action-touch btn-wa" title="تواصل واتساب" onclick="event.preventDefault(); event.stopPropagation(); openWhatsAppFast(\'' + (window.OFFICE_DATA ? window.OFFICE_DATA.whatsapp : '0545888931') + '\', \'استفسار عن العرض رقم ' + escapeHtml(id) + ': ' + escapeHtml(title) + '\');">' +
                    '<i class="fab fa-whatsapp"></i>' +
                '</button>' +
            '</div>' +
        '</div>' +
        '<div class="card-content-body">' +
            '<div class="card-price-22">' + priceFormatted + '</div>' +
            '<h3 class="card-title-15">' + escapeHtml(title) + '</h3>' +
            '<div class="card-location-text"><i class="fas fa-map-marker-alt"></i> ' + escapeHtml(locationText) + '</div>' +
            (specChips ? '<div class="card-specs-12">' + specChips + '</div>' : '') +
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
                return '<a href="' + window.offerDetailLink(o) + '" class="most-viewed-chip"><i class="fas fa-fire"></i> ' + escapeHtml(o.title || o.name) + '</a>';
            }).join('');
        }
    } catch (e) {}
}
window.renderMostViewedBar = renderMostViewedBar;

// Lightbox
function initLightbox() {
    // Lightbox modal logic if initialized
}
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
