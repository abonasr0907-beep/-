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

    // ===== .ICS Calendar File Generator =====
    function generateIcsFile(propertyTitle, appointmentDate, period) {
        var now = new Date();
        var dtstamp = now.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

        var startDate = appointmentDate || now.toISOString().split('T')[0].replace(/-/g, '');
        var startTime = '090000';
        var endTime = '110000';
        if (period === 'مسائية') {
            startTime = '160000';
            endTime = '180000';
        }

        var dtstart = startDate + 'T' + startTime;
        var dtend = startDate + 'T' + endTime;

        var icsLines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Afaq Al-Injaz//Property Appointment//AR',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            'BEGIN:VEVENT',
            'UID:apt-' + Date.now() + '@afaqalqary.com',
            'DTSTAMP:' + dtstamp,
            'DTSTART:' + dtstart,
            'DTEND:' + dtend,
            'SUMMARY:موعد معاينة عقار - ' + (propertyTitle || 'آفاق الإنجاز'),
            'DESCRIPTION:موعد معاينة عقار مع مكتب آفاق الإنجاز العقاري\\nالفترة: ' + (period || 'معاينة عقار') + '\\nتواصل: 0545888931',
            'LOCATION:مكتب آفاق الإنجاز العقاري - الخرج',
            'STATUS:CONFIRMED',
            'END:VEVENT',
            'END:VCALENDAR'
        ];

        var icsContent = icsLines.join('\r\n');
        var blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
        var link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = 'appointment-' + (propertyTitle ? propertyTitle.replace(/\s+/g, '_') : 'viewing') + '.ics';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ===== Appointment Modal & Calendar (.ics) Integration =====
    function openAppointment(id, title) {
        var existingModal = document.getElementById('appointment-modal');
        if (existingModal) existingModal.remove();

        var today = new Date().toISOString().split('T')[0];

        var modalHtml =
            '<div id="appointment-modal" style="position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.7);z-index:99999;display:flex;align-items:center;justify-content:center;padding:20px;">' +
            '  <div style="background:#FFFFFF;border-radius:16px;max-width:480px;width:100%;padding:24px;direction:rtl;text-align:right;box-shadow:0 10px 30px rgba(0,0,0,0.3);position:relative;font-family:Tajawal,sans-serif;">' +
            '    <button id="close-apt-modal" style="position:absolute;top:16px;left:16px;background:none;border:none;font-size:22px;cursor:pointer;color:#888;">✕</button>' +
            '    <h3 style="color:#1B3D3D;margin-bottom:12px;font-size:22px;">📅 حجز موعد معاينة</h3>' +
            '    <p style="color:#555;margin-bottom:16px;font-size:15px;">' + escHtml(title) + '</p>' +
            '    <div style="margin-bottom:12px;">' +
            '      <label style="display:block;margin-bottom:6px;font-weight:bold;color:#333;">تاريخ المعاينة:</label>' +
            '      <input type="date" id="apt-date" value="' + today + '" min="' + today + '" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-family:inherit;">' +
            '    </div>' +
            '    <div style="margin-bottom:20px;">' +
            '      <label style="display:block;margin-bottom:6px;font-weight:bold;color:#333;">فترة المعاينة:</label>' +
            '      <select id="apt-period" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;font-family:inherit;">' +
            '        <option value="صباحية">صباحية (9:00 ص - 11:00 ص)</option>' +
            '        <option value="مسائية">مسائية (4:00 م - 6:00 م)</option>' +
            '      </select>' +
            '    </div>' +
            '    <div style="display:flex;gap:10px;flex-wrap:wrap;">' +
            '      <button id="confirm-apt-wa" style="flex:1;background:#25D366;color:#FFF;border:none;padding:12px;border-radius:8px;font-weight:bold;cursor:pointer;font-family:inherit;">💬 تأكيد عبر واتساب</button>' +
            '      <button id="add-to-calendar-btn" style="flex:1;background:#2A5050;color:#FFF;border:none;padding:12px;border-radius:8px;font-weight:bold;cursor:pointer;font-family:inherit;">📅 أضف للتقويم (.ics)</button>' +
            '    </div>' +
            '  </div>' +
            '</div>';

        document.body.insertAdjacentHTML('beforeend', modalHtml);

        document.getElementById('close-apt-modal').onclick = function() {
            var m = document.getElementById('appointment-modal');
            if (m) m.remove();
        };

        document.getElementById('confirm-apt-wa').onclick = function() {
            var d = document.getElementById('apt-date').value;
            var p = document.getElementById('apt-period').value;
            var msg = 'أرغب في حجز موعد معاينة لعقار: ' + title + ' (معرف: ' + id + ')\nالتاريخ: ' + d + '\nالفترة: ' + p;
            var waUrl = 'https://wa.me/' + OFFICE_WHATSAPP + '?text=' + encodeURIComponent(msg);
            window.open(waUrl, '_blank');
        };

        document.getElementById('add-to-calendar-btn').onclick = function() {
            var d = document.getElementById('apt-date').value;
            var p = document.getElementById('apt-period').value;
            var cleanDate = d ? d.replace(/-/g, '') : '';
            generateIcsFile(title, cleanDate, p);
        };
    }

    // ===== PDF / Print =====
    function printProperty() {
        window.print();
    }

    // ===== Poster Canvas Generator (1080x1350) =====
    function generatePropertyPoster(prop) {
        if (!prop) return;
        var canvas = document.createElement('canvas');
        canvas.width = 1080;
        canvas.height = 1350;
        var ctx = canvas.getContext('2d');
        if (!ctx) return;

        // 1. Background linear gradient
        var grad = ctx.createLinearGradient(0, 0, 0, 1350);
        grad.addColorStop(0, '#102A2A');
        grad.addColorStop(0.5, '#1B3D3D');
        grad.addColorStop(1, '#0C1E1E');
        ctx.fillStyle = grad;
        ctx.fillRect(0, 0, 1080, 1350);

        // Gold border inner
        ctx.strokeStyle = '#C4A956';
        ctx.lineWidth = 6;
        ctx.strokeRect(30, 30, 1020, 1290);

        // 2. Header Box: Office Name & Badge
        ctx.fillStyle = '#C4A956';
        ctx.font = 'bold 44px Tajawal, Cairo, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText('مكتب آفاق الإنجاز العقاري', 1010, 95);

        // Badge: مرخص وموثق
        ctx.fillStyle = '#D4BD75';
        ctx.fillRect(70, 55, 230, 50);
        ctx.fillStyle = '#102A2A';
        ctx.font = 'bold 24px Tajawal, Cairo, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText('مرخّص وموثّق ✓', 185, 88);

        // Header Divider Line
        ctx.strokeStyle = 'rgba(196, 169, 86, 0.4)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(70, 125);
        ctx.lineTo(1010, 125);
        ctx.stroke();

        // 3. Helper to draw details after images are loaded
        var currentUrl = window.location.href;
        var qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(currentUrl);

        var firstImgUrl = (prop.images && prop.images[0]) || prop.image || '';

        var propImg = new Image();
        propImg.crossOrigin = 'anonymous';

        var qrImg = new Image();
        qrImg.crossOrigin = 'anonymous';

        var imagesLoaded = 0;
        function checkAndDraw() {
            imagesLoaded++;
            if (imagesLoaded < 2) return;

            // Draw Property Image (70, 145, 940, 560)
            try {
                if (propImg.complete && propImg.naturalWidth !== 0) {
                    ctx.drawImage(propImg, 70, 145, 940, 560);
                } else {
                    throw new Error('Image not loaded');
                }
            } catch(e) {
                // Fallback luxury placeholder box
                ctx.fillStyle = '#2A5050';
                ctx.fillRect(70, 145, 940, 560);
                ctx.fillStyle = '#D4BD75';
                ctx.font = 'bold 36px Tajawal, Cairo, sans-serif';
                ctx.textAlign = 'center';
                ctx.fillText('آفاق الإنجاز العقاري', 540, 425);
            }

            // Image Border
            ctx.strokeStyle = '#C4A956';
            ctx.lineWidth = 3;
            ctx.strokeRect(70, 145, 940, 560);

            // 4. Content Area
            var titleText = prop.title || (prop.category + ' في ' + (prop.area || ''));
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 42px Tajawal, Cairo, sans-serif';
            ctx.textAlign = 'right';
            ctx.fillText(titleText, 1010, 770);

            var priceVal = prop.price_text || (prop.price ? prop.price + ' ريال' : 'على السوم');
            ctx.fillStyle = '#D4BD75';
            ctx.font = 'bold 50px Tajawal, Cairo, sans-serif';
            ctx.fillText('السعر: ' + priceVal, 1010, 845);

            var pricePerSqm = '—';
            if (prop.price && prop.size_sqm && Number(prop.size_sqm) > 0) {
                pricePerSqm = Math.round(Number(prop.price) / Number(prop.size_sqm)) + ' ريال / م²';
            } else if (prop.price_per_sqm) {
                pricePerSqm = prop.price_per_sqm;
            }
            ctx.fillStyle = '#E8E0D0';
            ctx.font = 'bold 34px Tajawal, Cairo, sans-serif';
            ctx.fillText('سعر / م²: ' + pricePerSqm, 1010, 910);

            var infoText = 'القسم: ' + (prop.category || 'عقار') + ' | المساحة: ' + (prop.size_sqm ? prop.size_sqm + ' م²' : '—');
            ctx.font = '30px Tajawal, Cairo, sans-serif';
            ctx.fillStyle = '#B0C2C2';
            ctx.fillText(infoText, 1010, 965);

            // Divider Line
            ctx.strokeStyle = 'rgba(196, 169, 86, 0.4)';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(70, 1000);
            ctx.lineTo(1010, 1000);
            ctx.stroke();

            // 5. Bottom Section: Contacts & QR
            ctx.fillStyle = '#FFFFFF';
            ctx.fillRect(70, 1030, 200, 200);

            try {
                if (qrImg.complete && qrImg.naturalWidth !== 0) {
                    ctx.drawImage(qrImg, 80, 1040, 180, 180);
                }
            } catch(e) {}

            ctx.fillStyle = '#D4BD75';
            ctx.font = 'bold 22px Tajawal, Cairo, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText('امسح لمعاينة العرض', 170, 1260);

            ctx.textAlign = 'right';
            ctx.fillStyle = '#FFFFFF';
            ctx.font = 'bold 32px Tajawal, Cairo, sans-serif';
            ctx.fillText('📞 للتواصل والاستفسار:', 1010, 1060);

            ctx.font = 'bold 30px Tajawal, Cairo, sans-serif';
            ctx.fillStyle = '#D4BD75';
            ctx.fillText('💬 واتساب: 0545888931', 1010, 1115);
            ctx.fillText('📞 مكالمات: 0544699933', 1010, 1165);
            ctx.fillText('📲 واتساب + مكالمات: 0561610748', 1010, 1215);

            ctx.fillStyle = '#88AAAA';
            ctx.font = '22px Tajawal, Cairo, sans-serif';
            ctx.fillText('آفاق الإنجاز العقاري — الخرج والدلم', 1010, 1265);

            // 6. Download PNG
            try {
                var dataUrl = canvas.toDataURL('image/png');
                var a = document.createElement('a');
                a.download = 'poster-' + (prop.id || 'property') + '.png';
                a.href = dataUrl;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            } catch(err) {
                alert('تعذر تنزيل البوستر تلقائياً.');
            }
        }

        propImg.onload = checkAndDraw;
        propImg.onerror = checkAndDraw;
        if (firstImgUrl) {
            propImg.src = firstImgUrl;
        } else {
            checkAndDraw();
        }

        qrImg.onload = checkAndDraw;
        qrImg.onerror = checkAndDraw;
        qrImg.src = qrUrl;
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
                    '<button class="luxury-action-btn btn-pdf" id="luxury-pdf-btn" aria-label="طباعة / PDF"><i class="fas fa-print"></i> طباعة / PDF</button>' +
                    '<button class="luxury-action-btn btn-poster" id="luxury-poster-btn" aria-label="تحميل البوستر"><i class="fas fa-image"></i> 🖼 تحميل البوستر</button>';

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
                // Wire Poster
                document.getElementById('luxury-poster-btn').addEventListener('click', function() {
                    generatePropertyPoster(prop);
                });

                // Wire Video Tour if present
                if (prop.video_url || prop.video) {
                    var vUrl = prop.video_url || prop.video;
                    var vBtn = document.createElement('button');
                    vBtn.className = 'luxury-action-btn btn-video-tour';
                    vBtn.innerHTML = '<i class="fas fa-video"></i> 🎬 جولة فيديو';
                    vBtn.onclick = function() {
                        if (typeof window.openVideoModal === 'function') {
                            window.openVideoModal(vUrl, title);
                        }
                    };
                    actionBar.appendChild(vBtn);
                }
            }

            // ===== QR Code =====
            if (qrBox && !qrBox.dataset.filled) {
                qrBox.dataset.filled = '1';
                generateQR(currentUrl, qrBox);
            }

            // ===== Offer FAQ Schema =====
            if (prop.faq && Array.isArray(prop.faq) && prop.faq.length > 0) {
                var faqEntities = prop.faq.map(function(item) {
                    return {
                        "@type": "Question",
                        "name": item.question || item.q || '',
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": item.answer || item.a || ''
                        }
                    };
                });
                var faqSchema = {
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": faqEntities
                };
                var script = document.createElement('script');
                script.type = 'application/ld+json';
                script.textContent = JSON.stringify(faqSchema);
                document.head.appendChild(script);
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
        renderFullCompareTable();
        loadGuidesAndNews();

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

    // ===== المقارنة الشاملة (حتى 4 عقارات) =====
    function renderFullCompareTable() {
        var container = document.getElementById('compare-table-container');
        var emptyEl = document.getElementById('compare-empty');
        if (!container && !emptyEl) return;

        var cmp = getCompare();
        if (!cmp || cmp.length === 0) {
            if (emptyEl) emptyEl.style.display = 'block';
            if (container) container.style.display = 'none';
            return;
        }

        if (emptyEl) emptyEl.style.display = 'none';
        if (container) container.style.display = 'block';

        // ختم تحديث البوصلة
        var todayStr = new Date().toISOString().slice(0, 10);
        var lastUpdated = localStorage.getItem('afaq_bousla_last_update');
        if (lastUpdated !== todayStr) {
            localStorage.setItem('afaq_bousla_last_update', todayStr);
        }

        // جلب تفاصيل العقارات
        var allOffers = window.OFFERS || [];
        var compareOffers = cmp.map(function(c) {
            var found = allOffers.find(function(o){ return o.id === c.id; });
            return found || {
                id: c.id,
                title: c.title,
                images: [c.img || 'images/logo.jpg'],
                price: 1000000,
                price_text: '1,000,000 ريال',
                size_sqm: 1000,
                area: 'الرحمانية',
                category: 'مزرعة',
                type: 'farm'
            };
        });

        var feePct = parseFloat(window.userFeePct || 5);

        // بناء الهيدر والختم والتنويه
        var headerHtml = '<div class="compare-header-bar">' +
            '<div class="bousla-stamp-badge"><i class="fas fa-compass"></i> البوصلة محدثة: ' + todayStr + '</div>' +
            '<div style="display:flex; align-items:center; gap:10px;">' +
            '<label style="font-size:13px; font-weight:700;">رسوم الشراء القابلة للتعديل (%): </label>' +
            '<input type="number" value="' + feePct + '" min="0" max="25" step="0.5" style="width:70px; padding:6px; border:1px solid #ccc; border-radius:6px;" onchange="window.userFeePct=this.value; window.renderFullCompareTable();">' +
            '</div>' +
            '</div>' +
            '<div class="compare-disclaimer"><i class="fas fa-exclamation-triangle"></i> <strong>تنويه مهم:</strong> هذا الجدول لأغراض التقييم والاسترشاد فقط — لسنا مستشارين ماليين. يُرجى إجراء الفحص النافي للجهالة قبل اتخاذ أي قرار استثماري.</div>';

        var tableHtml = '<div class="compare-table-wrapper"><table class="compare-table"><thead><tr>' +
            '<th style="width:200px;">المعيار / العقار</th>';

        compareOffers.forEach(function(o) {
            var img = (o.images && o.images[0]) ? o.images[0] : 'images/logo.jpg';
            tableHtml += '<th class="compare-prop-header">' +
                '<img src="' + img + '" alt="' + escHtml(o.title) + '">' +
                '<span class="compare-prop-title">' + escHtml(o.title) + '</span>' +
                '<button onclick="window.afaqSilo.toggleCompare(\'' + o.id + '\'); window.renderFullCompareTable();" style="background:#e74c3c; color:#fff; border:none; border-radius:4px; padding:3px 10px; font-size:11px; cursor:pointer;">إزالة</button>' +
                '</th>';
        });
        tableHtml += '</tr></thead><tbody>';

        // قسم 1: «بالسعر المحدد»
        tableHtml += '<tr><td colspan="' + (compareOffers.length + 1) + '" class="compare-section-title"><i class="fas fa-tag"></i> أولاً: التقييم بالسعر المحدد للعقار</td></tr>';

        // السعر المحدد
        tableHtml += '<tr><td><strong>السعر المحدد</strong></td>';
        compareOffers.forEach(function(o) {
            tableHtml += '<td style="text-align:center; font-weight:700; color:#1b3d3d;">' + (o.price ? o.price.toLocaleString('en-US') + ' ريال' : o.price_text || 'على السوم') + '</td>';
        });
        tableHtml += '</tr>';

        // سعر المتر
        tableHtml += '<tr><td><strong>سعر المتر</strong></td>';
        compareOffers.forEach(function(o) {
            var pM2 = o.price && o.size_sqm ? Math.round(o.price / o.size_sqm) : '—';
            tableHtml += '<td style="text-align:center;">' + (typeof pM2 === 'number' ? pM2.toLocaleString('en-US') + ' ريال/م²' : pM2) + '</td>';
        });
        tableHtml += '</tr>';

        // انحراف % عن الفئة
        tableHtml += '<tr><td><strong>انحراف % عن متوسط الفئة</strong></td>';
        compareOffers.forEach(function(o) {
            var pM2 = o.price && o.size_sqm ? (o.price / o.size_sqm) : 0;
            var catAvg = 700;
            var dev = pM2 && catAvg ? Math.round(((pM2 - catAvg) / catAvg) * 100) : 0;
            var devClass = dev <= 0 ? 'below' : 'above';
            var devText = dev <= 0 ? dev + '% أقل من المتوسط' : '+' + dev + '% أعلى من المتوسط';
            tableHtml += '<td style="text-align:center;"><span class="compare-dev-badge ' + devClass + '">' + devText + '</span></td>';
        });
        tableHtml += '</tr>';

        // تكلفة الشراء التقديرية
        tableHtml += '<tr><td><strong>تكلفة الشراء التقديرية (السعر + ' + feePct + '% رسوم)</strong></td>';
        compareOffers.forEach(function(o) {
            var estCost = o.price ? Math.round(o.price * (1 + feePct / 100)) : 0;
            tableHtml += '<td style="text-align:center; font-weight:700;">' + (estCost ? estCost.toLocaleString('en-US') + ' ريال' : '—') + '</td>';
        });
        tableHtml += '</tr>';

        // العائد % المتوقع
        tableHtml += '<tr><td><strong>العائد السنوي % المتوقع (افتراض 7%)</strong></td>';
        compareOffers.forEach(function(o) {
            var defaultRent = o.price ? Math.round(o.price * 0.07) : 0;
            var yieldPct = '7.0';
            tableHtml += '<td style="text-align:center;">' +
                '<strong style="color:#27ae60; font-size:15px;">' + yieldPct + '%</strong><br>' +
                '<small style="color:#777;">إيجار تقديري: ' + Math.round(defaultRent).toLocaleString('en-US') + ' ريال/سنة</small>' +
                '</td>';
        });
        tableHtml += '</tr>';

        // قسم 2: «بمتوسط البوصلة»
        tableHtml += '<tr><td colspan="' + (compareOffers.length + 1) + '" class="compare-section-title"><i class="fas fa-compass"></i> ثانياً: التقييم بمتوسط البوصلة العقارية</td></tr>';

        // متوسط البوصلة
        tableHtml += '<tr><td><strong>متوسط سعر المتر (البوصلة)</strong></td>';
        compareOffers.forEach(function(o) {
            var bouslaVal = '750 ريال/م²';
            if (window.BOUSLA_PRICES && window.BOUSLA_PRICES[o.area]) {
                var bObj = window.BOUSLA_PRICES[o.area];
                bouslaVal = o.type === 'farm' ? bObj.farm : (o.type === 'resthouse' ? bObj.resthouse : bObj.land);
            }
            tableHtml += '<td style="text-align:center; font-weight:700; color:#b8860b;">' + bouslaVal + '</td>';
        });
        tableHtml += '</tr>';

        // السعر التقديري حسب البوصلة
        tableHtml += '<tr><td><strong>السعر التقديري حسب البوصلة</strong></td>';
        compareOffers.forEach(function(o) {
            var bM2 = 750;
            var totalBousla = o.size_sqm ? Math.round(bM2 * o.size_sqm) : (o.price || 0);
            tableHtml += '<td style="text-align:center;">' + totalBousla.toLocaleString('en-US') + ' ريال</td>';
        });
        tableHtml += '</tr>';

        // تكلفة الشراء التقديرية حسب البوصلة
        tableHtml += '<tr><td><strong>تكلفة الشراء التقديرية (البوصلة + ' + feePct + '%)</strong></td>';
        compareOffers.forEach(function(o) {
            var bM2 = 750;
            var totalBousla = o.size_sqm ? Math.round(bM2 * o.size_sqm) : (o.price || 0);
            var bCost = Math.round(totalBousla * (1 + feePct / 100));
            tableHtml += '<td style="text-align:center; font-weight:700;">' + bCost.toLocaleString('en-US') + ' ريال</td>';
        });
        tableHtml += '</tr>';

        // العائد المتوقع حسب البوصلة
        tableHtml += '<tr><td><strong>العائد % المتوقع حسب البوصلة</strong></td>';
        compareOffers.forEach(function(o) {
            var bM2 = 750;
            var totalBousla = o.size_sqm ? Math.round(bM2 * o.size_sqm) : (o.price || 0);
            var defaultRent = totalBousla ? Math.round(totalBousla * 0.07) : 0;
            var bYield = totalBousla && defaultRent ? ((defaultRent / totalBousla) * 100).toFixed(1) : '7.0';
            tableHtml += '<td style="text-align:center; color:#27ae60; font-weight:700;">' + bYield + '%</td>';
        });
        tableHtml += '</tr>';

        tableHtml += '</tbody></table></div>';
        container.innerHTML = headerHtml + tableHtml;
    }

    window.renderFullCompareTable = renderFullCompareTable;

    // ===== تحميل الأدلة والأخبار النسخة الاحتياطية الأصليّة =====
    async function loadGuidesAndNews() {
        var newsContainer = document.getElementById('market-news-container');
        if (!newsContainer) return;

        var newsItems = [
            {
                title: 'نمو ملحوظ في الطلب على المزارع والاستراحات بالخرج خلال 2025',
                date: '2025-02-15',
                summary: 'شهدت سوق العقارات بالخرج والرياض ارتفاعاً في حجم تداولات المزارع والاستراحات المجهزة بشبكات آبار حديثة وتقنيات ري طاقة شمسية.',
                icon: 'fa-chart-line'
            },
            {
                title: 'التوسع المخطط في المخططات السكنية والزراعية بالدلم والهياثم والرحمانية',
                date: '2025-02-10',
                summary: 'اعتماد مخططات تنظيمية جديدة تدعم التمدد العمراني والاستثمار الزراعي المستدام مع ربط المحاور الرئيسية بالخرج والرياض.',
                icon: 'fa-city'
            },
            {
                title: 'تسهيلات التوثيق الإلكتروني للصكوك ترفع معدل التداول العقاري الموثق',
                date: '2025-02-05',
                summary: 'منصة ناجز والمؤشرات العقارية للهيئة العامة للعقار تمنح الشفافية الكاملة للمشترين والمستثمرين لضمان أسرع نقل ملكية وتقييم دقيق.',
                icon: 'fa-shield-alt'
            }
        ];

        try {
            var res = await fetch('data/news.json');
            if (res.ok) {
                var data = await res.json();
                if (data && data.news && data.news.length > 0) {
                    newsItems = data.news;
                }
            }
        } catch(e) {}

        var html = '<div class="market-news-section" style="margin-top:40px;">' +
            '<h2 class="section-news-title" style="margin-bottom:20px; font-size:22px; color:#1b3d3d;"><i class="fas fa-newspaper" style="color:#C4A956;"></i> أخبار السوق العقاري بالخرج والرياض</h2>' +
            '<div class="silo-hub-grid">';

        newsItems.forEach(function(item) {
            html += '<div class="silo-hub-card market-news-card">' +
                '<div class="silo-hub-card-icon"><i class="fas ' + (item.icon || 'fa-newspaper') + '"></i></div>' +
                '<div class="silo-hub-card-body">' +
                '<div style="font-size:12px; color:#b8860b; margin-bottom:6px;"><i class="far fa-calendar-alt"></i> ' + (item.date || '2025') + '</div>' +
                '<h3>' + escHtml(item.title) + '</h3>' +
                '<p>' + escHtml(item.summary) + '</p>' +
                '</div>' +
                '</div>';
        });

        html += '</div></div>';
        newsContainer.innerHTML = html;

        // Inject NewsArticle Schema
        newsItems.forEach(function(item) {
            var newsSchema = {
                "@context": "https://schema.org",
                "@type": "NewsArticle",
                "headline": item.title,
                "datePublished": item.date || "2025-02-15",
                "description": item.summary,
                "publisher": {
                    "@type": "Organization",
                    "name": "مكتب آفاق الإنجاز العقاري",
                    "logo": {
                        "@type": "ImageObject",
                        "url": "https://abonasr0907-beep.github.io/-/images/logo.jpg"
                    }
                }
            };
            var s = document.createElement('script');
            s.type = 'application/ld+json';
            s.textContent = JSON.stringify(newsSchema);
            document.head.appendChild(s);
        });
    }

    // ===== Video Modal Helpers for Property Page =====
    window.getYouTubeEmbedUrl = function(url) {
        if (!url) return '';
        var regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|shorts\/|watch\?v=|\&v=)([^#\&\?]*).*/;
        var match = url.match(regExp);
        var id = (match && match[2].length === 11) ? match[2] : null;
        return id ? 'https://www.youtube.com/embed/' + id : url;
    };

    window.openVideoModal = function(url, title) {
        var modal = document.getElementById('video-modal');
        if (!modal) {
            var html = '<div id="video-modal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:99999;display:flex;align-items:center;justify-content:center;">' +
                '<div style="background:#111;border-radius:12px;padding:16px;max-width:600px;width:90%;position:relative;">' +
                '<button onclick="closeVideoModal()" style="position:absolute;top:10px;right:10px;background:none;border:none;color:#fff;font-size:24px;cursor:pointer;">&times;</button>' +
                '<h4 style="color:#fff;margin:0 0 12px;font-size:16px;">' + escHtml(title || 'جولة فيديو') + '</h4>' +
                '<div id="video-modal-body" style="width:100%;height:350px;"></div>' +
                '</div></div>';
            document.body.insertAdjacentHTML('beforeend', html);
            modal = document.getElementById('video-modal');
        } else {
            modal.style.display = 'flex';
        }
        var body = document.getElementById('video-modal-body');
        var uLower = (url || '').toLowerCase();
        if (uLower.includes('tiktok.com')) {
            var match = url.match(/\/video\/(\d+)/);
            var videoId = match ? match[1] : '';
            body.innerHTML = '<iframe src="https://www.tiktok.com/embed/v2/' + videoId + '" style="width:100%;height:100%;border:none;" allowfullscreen></iframe>';
        } else if (uLower.includes('instagram.com')) {
            var cleanUrl = url.split('?')[0].replace(/\/$/, '');
            body.innerHTML = '<iframe src="' + cleanUrl + '/embed" style="width:100%;height:100%;border:none;" allowfullscreen></iframe>';
        } else {
            body.innerHTML = '<iframe src="' + window.getYouTubeEmbedUrl(url) + '" style="width:100%;height:100%;border:none;" allowfullscreen></iframe>';
        }
    };

    window.closeVideoModal = function() {
        var modal = document.getElementById('video-modal');
        if (modal) modal.style.display = 'none';
        var body = document.getElementById('video-modal-body');
        if (body) body.innerHTML = '';
    };

    // Expose for property page integration
    window.afaqSilo = {
        toggleFavorite: toggleFavorite,
        toggleCompare: toggleCompare,
        getFavorites: getFavorites,
        getCompare: getCompare,
        buildOfferUrl: buildOfferUrl,
        slugify: slugify,
        renderFullCompareTable: renderFullCompareTable
    };
})();
