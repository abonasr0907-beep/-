/**
 * Afaq Al-Injaz — Phase 3 §3: Silo Hub + Luxury Property JS
 * Add-on script (loaded after main.js, does not modify it)
 * Features:
 * - Hub page stats bar (counts from offers.json)
 * - Afaq exclusives bar (featured=true only)
 * - Visible breadcrumbs + BreadcrumbList injection
 * - Luxury property: facts grid, QR, share, ❤ favorites, ➕ compare, 📅 appointment, 🖨 PDF
 * - Favorites localStorage + counter badge
 * - Compare localStorage + drawer
 */

(function() {
    'use strict';

    // ===== Configuration =====
    var OFFICE_WHATSAPP = '966545888931';
    var BOT_USERNAME = 'tlastlastlasbot';
    var FAV_KEY = 'afaq_favorites';
    var COMPARE_KEY = 'afaq_compare';
    var COMPARE_MAX = 4;

    // ===== Utility: safe localStorage =====
    function lsGet(key) {
        try { return JSON.parse(localStorage.getItem(key) || '[]'); }
        catch(e) { return []; }
    }
    function lsSet(key, val) {
        try { localStorage.setItem(key, JSON.stringify(val)); }
        catch(e) {}
    }

    // ===== Slugify (Arabic-safe) =====
    function slugify(text) {
        if (!text) return '';
        return String(text)
            .trim()
            .replace(/[\s]+/g, '-')
            .replace(/[^\u0600-\u06FFa-zA-Z0-9\-]/g, '')
            .replace(/-+/g, '-')
            .replace(/^-|-$/g, '')
            .toLowerCase();
    }

    // ===== Build offer URL (/offer/{id}/{slug}) =====
    function buildOfferUrl(offer) {
        var id = offer.id || offer.external_id || '';
        var slug = slugify(offer.title || offer.category || '');
        if (slug) {
            return 'offer/' + encodeURIComponent(id) + '/' + encodeURIComponent(slug) + '.html';
        }
        return 'property.html?id=' + encodeURIComponent(id);
    }

    // ===== Fetch offers.json (cached) =====
    var _offersCache = null;
    function fetchOffers(cb) {
        if (_offersCache) { cb(_offersCache); return; }
        fetch('offers-data/offers.json', { cache: 'no-store' })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                var offers = (data.offers || []).filter(function(o) {
                    return o.publish_status === 'published' || o.status === 'published' || !o.publish_status;
                });
                _offersCache = offers;
                cb(offers);
            })
            .catch(function(e) {
                console.warn('silo: fetch offers failed', e);
                cb([]);
            });
    }

    // ===== Stats Bar =====
    function initStatsBar() {
        var bar = document.getElementById('silo-stats-bar');
        if (!bar) return;
        fetchOffers(function(offers) {
            var stats = {
                total: offers.length,
                farms: offers.filter(function(o){ return o.category === 'مزرعة'; }).length,
                resthouses: offers.filter(function(o){ return o.category === 'استراحة'; }).length,
                lands: offers.filter(function(o){ return o.category === 'أرض سكنية'; }).length,
                featured: offers.filter(function(o){ return o.featured; }).length,
                areas: new Set(offers.map(function(o){ return o.area; })).size
            };
            var html = '';
            if (bar.dataset.stat === 'all' || !bar.dataset.stat) {
                html +=
                    statItem(stats.total, 'عقار متاح') +
                    statItem(stats.farms, 'مزرعة') +
                    statItem(stats.resthouses, 'استراحة') +
                    statItem(stats.lands, 'أرض سكنية') +
                    statItem(stats.featured, 'عقار مميز') +
                    statItem(stats.areas, 'منطقة');
            }
            bar.innerHTML = html;
        });
    }
    function statItem(num, label) {
        return '<div class="silo-stat-item"><div class="silo-stat-number">' + num + '</div><div class="silo-stat-label">' + label + '</div></div>';
    }

    // ===== Exclusives Bar (featured=true only) =====
    function initExclusivesBar() {
        var bar = document.getElementById('silo-exclusives-scroll');
        if (!bar) return;
        fetchOffers(function(offers) {
            var featured = offers.filter(function(o){ return o.featured; });
            if (featured.length === 0) {
                var container = document.getElementById('silo-exclusives-bar');
                if (container) container.style.display = 'none';
                return;
            }
            var html = '';
            featured.forEach(function(o) {
                var img = (o.images && o.images[0]) || 'images/logo.jpg';
                html += '<a href="' + buildOfferUrl(o) + '" class="silo-exclusive-card">' +
                    '<img src="' + img + '" alt="' + escHtml(o.title || '') + ' | آفاق الإنجاز العقاري" loading="lazy">' +
                    '<div class="silo-exclusive-info">' +
                    '<span class="silo-exclusive-badge">حصري آفاق</span>' +
                    '<h3>' + escHtml(o.title || '') + '</h3>' +
                    '<div class="silo-exclusive-price">' + escHtml(o.price_text || '') + '</div>' +
                    '<div class="silo-exclusive-area"><i class="fas fa-map-marker-alt"></i> ' + escHtml(o.area || '') + '</div>' +
                    '</div></a>';
            });
            bar.innerHTML = html;
        });
    }

    // ===== Hub Cards: count per category/area =====
    function initHubCards() {
        var cards = document.querySelectorAll('[data-hub-count]');
        if (cards.length === 0) return;
        fetchOffers(function(offers) {
            cards.forEach(function(card) {
                var type = card.getAttribute('data-hub-count');
                var value = card.getAttribute('data-hub-value');
                var count = 0;
                if (type === 'category') {
                    count = offers.filter(function(o){ return o.category === value; }).length;
                } else if (type === 'area') {
                    count = offers.filter(function(o){ return o.area === value; }).length;
                }
                var countEl = card.querySelector('.silo-hub-card-count');
                if (countEl) {
                    countEl.textContent = count + ' عقار متاح';
                }
            });
        });
    }

    // ===== BreadcrumbList Schema injection =====
    function injectBreadcrumbSchema(crumbs) {
        if (!crumbs || crumbs.length === 0) return;
        var schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": crumbs.map(function(c, i) {
                return {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": c.name,
                    "item": c.url
                };
            })
        };
        var script = document.createElement('script');
        script.type = 'application/ld+json';
        script.textContent = JSON.stringify(schema);
        document.head.appendChild(script);
    }

    // ===== Favorites =====
    function getFavorites() { return lsGet(FAV_KEY); }
    function toggleFavorite(id) {
        var favs = getFavorites();
        var idx = favs.indexOf(id);
        if (idx >= 0) {
            favs.splice(idx, 1);
        } else {
            favs.push(id);
        }
        lsSet(FAV_KEY, favs);
        updateFavCounter();
        return idx < 0; // true = now favorited
    }
    function isFavorited(id) {
        return getFavorites().indexOf(id) >= 0;
    }
    function updateFavCounter() {
        var favs = getFavorites();
        var badges = document.querySelectorAll('.fav-counter-badge');
        badges.forEach(function(b) {
            if (favs.length > 0) {
                b.textContent = favs.length;
                b.classList.add('visible');
            } else {
                b.classList.remove('visible');
            }
        });
        // Update fav buttons on page
        document.querySelectorAll('[data-fav-id]').forEach(function(btn) {
            var id = btn.getAttribute('data-fav-id');
            if (isFavorited(id)) {
                btn.classList.add('active');
                btn.innerHTML = '<i class="fas fa-heart"></i> في المفضلة';
            } else {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="far fa-heart"></i> أضف للمفضلة';
            }
        });
    }

    // ===== Compare =====
    function getCompare() { return lsGet(COMPARE_KEY); }
    function toggleCompare(id, title, img) {
        var cmp = getCompare();
        var idx = cmp.findIndex(function(c){ return c.id === id; });
        if (idx >= 0) {
            cmp.splice(idx, 1);
        } else {
            if (cmp.length >= COMPARE_MAX) {
                alert('يمكن مقارنة ' + COMPARE_MAX + ' عقارات كحد أقصى');
                return false;
            }
            cmp.push({ id: id, title: title, img: img });
        }
        lsSet(COMPARE_KEY, cmp);
        updateCompareDrawer();
        return idx < 0;
    }
    function isInCompare(id) {
        return getCompare().some(function(c){ return c.id === id; });
    }
    function updateCompareDrawer() {
        var drawer = document.getElementById('luxury-compare-drawer');
        if (!drawer) return;
        var cmp = getCompare();
        if (cmp.length === 0) {
            drawer.classList.remove('active');
            return;
        }
        drawer.classList.add('active');
        var itemsHtml = '';
        cmp.forEach(function(c) {
            itemsHtml += '<div class="luxury-compare-item">' +
                '<img src="' + (c.img || 'images/logo.jpg') + '" alt="' + escHtml(c.title) + '">' +
                '<div class="luxury-compare-item-info"><h4>' + escHtml(c.title) + '</h4></div>' +
                '<button class="luxury-compare-item-remove" data-compare-remove="' + c.id + '">&times;</button>' +
                '</div>';
        });
        var itemsEl = drawer.querySelector('.luxury-compare-drawer-items');
        if (itemsEl) itemsEl.innerHTML = itemsHtml;

        // Update compare buttons on page
        document.querySelectorAll('[data-compare-id]').forEach(function(btn) {
            var id = btn.getAttribute('data-compare-id');
            if (isInCompare(id)) {
                btn.classList.add('active');
                btn.innerHTML = '<i class="fas fa-check"></i> في المقارنة';
            } else {
                btn.classList.remove('active');
                btn.innerHTML = '<i class="fas fa-plus"></i> أضف للمقارنة';
            }
        });

        // Wire remove buttons
        drawer.querySelectorAll('[data-compare-remove]').forEach(function(btn) {
            btn.addEventListener('click', function() {
                var id = this.getAttribute('data-compare-remove');
                var cmp = getCompare();
                var item = cmp.find(function(c){ return c.id === id; });
                if (item) toggleCompare(id, item.title, item.img);
            });
        });
    }

    // ===== QR Code (uses api.qrserver.com — no library) =====
    function generateQR(url, container) {
        if (!container) return;
        var qrApi = 'https://api.qrserver.com/v1/create-qr-code/?size=120x120&data=' + encodeURIComponent(url);
        container.innerHTML = '<img src="' + qrApi + '" alt="رمز QR لرابط العقار | QR code for property link" loading="lazy">';
    }

    // ===== Share =====
    function shareProperty(title, url) {
        if (navigator.share) {
            navigator.share({ title: title, url: url }).catch(function(){});
        } else {
            // Fallback: copy to clipboard
            var fullUrl = window.location.origin + window.location.pathname.replace(/[^/]*$/, '') + url;
            try {
                navigator.clipboard.writeText(fullUrl);
                alert('تم نسخ الرابط: ' + fullUrl);
            } catch(e) {
                window.prompt('انسخ الرابط:', fullUrl);
            }
        }
    }

    // ===== Appointment (deep-link to bot) =====
    function openAppointment(id, title) {
        var msg = 'أرغب في حجز موعد معاينة لعقار: ' + title + ' (معرف: ' + id + ')';
        var waUrl = 'https://wa.me/' + OFFICE_WHATSAPP + '?text=' + encodeURIComponent(msg);
        window.open(waUrl, '_blank');
    }

    // ===== PDF / Print =====
    function printProperty() {
        window.print();
    }

    // ===== HTML escape =====
    function escHtml(text) {
        if (!text) return '';
        return String(text)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }

    // ===== Luxury Property Page Init =====
    function initLuxuryProperty() {
        var factsGrid = document.getElementById('luxury-facts-grid');
        var actionBar = document.getElementById('luxury-action-bar');
        var qrBox = document.getElementById('luxury-qr-box');
        if (!factsGrid && !actionBar) return; // Not on property page

        // Wait for property data to load (main.js sets window.currentProperty)
        var checkInterval = setInterval(function() {
            var prop = window.currentProperty;
            if (!prop) return;
            clearInterval(checkInterval);

            var id = prop.id || '';
            var title = prop.title || '';
            var img = (prop.images && prop.images[0]) || 'images/logo.jpg';
            var currentUrl = window.location.href;

            // ===== Facts Grid =====
            if (factsGrid && !factsGrid.dataset.filled) {
                factsGrid.dataset.filled = '1';
                var facts = [
                    { icon: 'fa-ruler-combined', value: prop.size_sqm ? prop.size_sqm + ' م²' : '—', label: 'المساحة' },
                    { icon: 'fa-map-marker-alt', value: prop.area || '—', label: 'المنطقة' },
                    { icon: 'fa-tag', value: prop.category || '—', label: 'النوع' },
                    { icon: 'fa-layer-group', value: prop.section || prop.property_type || '—', label: 'القسم' },
                    { icon: 'fa-money-bill-wave', value: prop.price_text || '—', label: 'السعر' },
                    { icon: 'fa-calendar-alt', value: prop.date_added || '—', label: 'تاريخ الإضافة' }
                ];
                var factsHtml = '';
                facts.forEach(function(f) {
                    factsHtml += '<div class="luxury-fact-item"><div class="luxury-fact-icon"><i class="fas ' + f.icon + '"></i></div><div class="luxury-fact-value">' + escHtml(f.value) + '</div><div class="luxury-fact-label">' + f.label + '</div></div>';
                });
                factsGrid.innerHTML = factsHtml;
            }

            // ===== Action Bar =====
            if (actionBar && !actionBar.dataset.filled) {
                actionBar.dataset.filled = '1';
                var favActive = isFavorited(id) ? ' active' : '';
                var cmpActive = isInCompare(id) ? ' active' : '';
                actionBar.innerHTML =
                    '<button class="luxury-action-btn' + favActive + '" data-fav-id="' + escHtml(id) + '" aria-label="إضافة للمفضلة"><i class="far fa-heart"></i> ' + (favActive ? 'في المفضلة' : 'أضف للمفضلة') + '</button>' +
                    '<button class="luxury-action-btn' + cmpActive + '" data-compare-id="' + escHtml(id) + '" data-compare-title="' + escHtml(title) + '" data-compare-img="' + escHtml(img) + '" aria-label="إضافة للمقارنة"><i class="fas fa-plus"></i> ' + (cmpActive ? 'في المقارنة' : 'أضف للمقارنة') + '</button>' +
                    '<button class="luxury-action-btn btn-appointment" id="luxury-appointment-btn" aria-label="حجز موعد معاينة"><i class="fas fa-calendar-check"></i> حجز معاينة</button>' +
                    '<button class="luxury-action-btn" id="luxury-share-btn" aria-label="مشاركة العقار"><i class="fas fa-share-alt"></i> مشاركة</button>' +
                    '<button class="luxury-action-btn btn-pdf" id="luxury-pdf-btn" aria-label="طباعة / PDF"><i class="fas fa-print"></i> طباعة / PDF</button>';

                // Wire fav
                actionBar.querySelector('[data-fav-id]').addEventListener('click', function() {
                    toggleFavorite(id);
                });
                // Wire compare
                actionBar.querySelector('[data-compare-id]').addEventListener('click', function() {
                    toggleCompare(id, title, img);
                });
                // Wire appointment
                document.getElementById('luxury-appointment-btn').addEventListener('click', function() {
                    openAppointment(id, title);
                });
                // Wire share
                document.getElementById('luxury-share-btn').addEventListener('click', function() {
                    shareProperty(title, currentUrl);
                });
                // Wire PDF
                document.getElementById('luxury-pdf-btn').addEventListener('click', function() {
                    printProperty();
                });
            }

            // ===== QR Code =====
            if (qrBox && !qrBox.dataset.filled) {
                qrBox.dataset.filled = '1';
                generateQR(currentUrl, qrBox);
            }
        }, 500);
    }

    // ===== Init on DOM Ready =====
    function init() {
        initStatsBar();
        initExclusivesBar();
        initHubCards();
        updateFavCounter();
        updateCompareDrawer();
        initLuxuryProperty();

        // Inject breadcrumb schema if data attribute present
        var bcData = document.getElementById('breadcrumb-schema-data');
        if (bcData) {
            try {
                var crumbs = JSON.parse(bcData.textContent);
                injectBreadcrumbSchema(crumbs);
            } catch(e) {}
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for property page integration
    window.afaqSilo = {
        toggleFavorite: toggleFavorite,
        toggleCompare: toggleCompare,
        getFavorites: getFavorites,
        getCompare: getCompare,
        buildOfferUrl: buildOfferUrl,
        slugify: slugify
    };
})();
