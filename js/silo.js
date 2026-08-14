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

    // ===== Compass Single-Source Calculations =====
    function computeAverages(offersList) {
        var result = {};
        var categories = ['مزرعة', 'استراحة', 'أرض سكنية'];
        categories.forEach(function(cat) {
            result[cat] = { sumUnitPrice: 0, count: 0, avgUnitPrice: 0 };
        });

        if (!offersList || !offersList.length) return result;

        offersList.forEach(function(o) {
            var rawCat = o.category || o.property_type || o.type || '';
            var cat = rawCat;
            if (rawCat === 'farm') cat = 'مزرعة';
            if (rawCat === 'resthouse') cat = 'استراحة';
            if (rawCat === 'land') cat = 'أرض سكنية';

            if (!result[cat]) {
                result[cat] = { sumUnitPrice: 0, count: 0, avgUnitPrice: 0 };
            }

            var price = Number(o.price);
            var size = Number(o.size_sqm);
            if (price > 0 && size > 0) {
                result[cat].sumUnitPrice += (price / size);
                result[cat].count += 1;
            }
        });

        Object.keys(result).forEach(function(cat) {
            if (result[cat].count > 0) {
                result[cat].avgUnitPrice = Math.round(result[cat].sumUnitPrice / result[cat].count);
            }
        });

        return result;
    }
    window.computeAverages = computeAverages;

    function renderCompassWidgets() {
        fetchOffers(function(offers) {
            var avgs = computeAverages(offers);

            // 1) Update main/hub compass grid if #bousla-grid exists
            var grid = document.getElementById('bousla-grid');
            if (grid) {
                var widgetHtml = '<div style="grid-column: 1/-1; background:#ffffff; border:1px solid #e2d9c8; border-radius:12px; padding:20px; margin-bottom:20px; box-shadow:0 4px 15px rgba(0,0,0,0.05);">' +
                    '<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:2px solid #C4A956; padding-bottom:12px; margin-bottom:15px;">' +
                    '<h3 style="margin:0; color:#2A5050; font-size:1.2rem;"><i class="fas fa-compass"></i> البوصلة العقارية الموحدة (معدل سعر المتر حيًا)</h3>' +
                    '<button type="button" onclick="renderCompassWidgets(); return false;" class="btn" style="padding:6px 14px; font-size:0.85rem; background:#2A5050; color:#fff; border-radius:6px; cursor:pointer;"><i class="fas fa-sync-alt"></i> تحديث البوصلة</button>' +
                    '</div>' +
                    '<div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap:15px; text-align:center;">';

                ['مزرعة', 'استراحة', 'أرض سكنية'].forEach(function(cat) {
                    var data = avgs[cat] || { avgUnitPrice: 0, count: 0 };
                    widgetHtml += '<div style="background:#f8f6f0; padding:15px; border-radius:8px; border:1px solid #eee;">' +
                        '<div style="font-weight:bold; color:#2A5050; margin-bottom:6px;">' + cat + '</div>' +
                        '<div style="font-size:1.1rem; color:#C4A956; font-weight:bold;">متوسط سعر المتر: ' + (data.avgUnitPrice ? data.avgUnitPrice.toLocaleString('en-US') + ' ريال/م²' : 'غير متوفر') + '</div>' +
                        '<div style="font-size:0.85rem; color:#666; margin-top:4px;">(بناءً على ' + data.count + ' عقاراً)</div>' +
                        '</div>';
                });

                widgetHtml += '</div>' +
                    '<p style="margin:12px 0 0 0; font-size:0.82rem; color:#888; text-align:center; font-style:italic;"><i class="fas fa-info-circle"></i> يُستبعد أي عقار بدون مساحة أو بسعر صفر من الحسابات لموثوقية البيانات</p>' +
                    '</div>';

                grid.innerHTML = widgetHtml;
            }

            // 2) Update Compass on single offer cards / property page
            var offerCompassBlocks = document.querySelectorAll('.offer-bousla, #property-compass-widget');
            offerCompassBlocks.forEach(function(block) {
                var offerId = block.getAttribute('data-compass-offer-id');
                var offerObj = null;

                if (offerId && offers) {
                    offerObj = offers.find(function(o){ return o.id === offerId; });
                } else if (window.currentProperty) {
                    offerObj = window.currentProperty;
                }

                if (!offerObj) return;

                var rawCat = offerObj.category || offerObj.property_type || offerObj.type || '';
                var cat = rawCat;
                if (rawCat === 'farm') cat = 'مزرعة';
                if (rawCat === 'resthouse') cat = 'استراحة';
                if (rawCat === 'land') cat = 'أرض سكنية';

                var catAvgData = avgs[cat] || { avgUnitPrice: 0, count: 0 };
                var avgPrice = catAvgData.avgUnitPrice;

                var price = Number(offerObj.price);
                var size = Number(offerObj.size_sqm);
                var unitPrice = (price > 0 && size > 0) ? Math.round(price / size) : 0;

                var deviationHtml = '';
                if (unitPrice > 0 && avgPrice > 0) {
                    var diff = Math.round(((unitPrice - avgPrice) / avgPrice) * 100);
                    if (diff > 0) {
                        deviationHtml = ' <span style="color:#d63031; font-weight:bold;">(أعلى بـ ' + diff + '% عن متوسط الفئة)</span>';
                    } else if (diff < 0) {
                        deviationHtml = ' <span style="color:#27ae60; font-weight:bold;">(أقل بـ ' + Math.abs(diff) + '% عن متوسط الفئة - قيمة ممتازة)</span>';
                    } else {
                        deviationHtml = ' <span style="color:#2980b9; font-weight:bold;">(يطابق متوسط الفئة تماماً)</span>';
                    }
                }

                block.innerHTML =
                    '<div style="background:#fdfcf9; border:1px solid #e8e0d0; border-radius:10px; padding:12px 15px; margin-top:10px;">' +
                    '<div style="font-weight:bold; color:#2A5050; font-size:0.95rem; margin-bottom:5px;">' +
                    '<i class="fas fa-compass"></i> بوصلة الأسعار الحية — ' + cat +
                    '</div>' +
                    '<div style="font-size:0.88rem; color:#444; line-height:1.6;">' +
                    'متوسط سعر المتر في ' + cat + ': <strong>' + (avgPrice ? avgPrice.toLocaleString('en-US') + ' ريال/م²' : 'غير محدد') + '</strong> (بناءً على ' + catAvgData.count + ' عقاراً)<br>' +
                    (unitPrice > 0 ? 'سعر متر هذا العقار: <strong>' + unitPrice.toLocaleString('en-US') + ' ريال/م²</strong>' + deviationHtml + '<br>' : '') +
                    '<small style="color:#888;">يُستبعد أي عقار بدون مساحة | <a href="#" onclick="renderCompassWidgets(); return false;" style="color:#C4A956; text-decoration:none;"><i class="fas fa-sync-alt"></i> تحديث الحسابات</a></small>' +
                    '</div>' +
                    '</div>';
            });
        });
    }
    window.renderCompassWidgets = renderCompassWidgets;

    // ===== Exclusives Bar (featured=true only, rotated by day) =====
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

            // T3.c: Select "Offer of the Week" automatically based on current date
            var today = new Date();
            var dayOfYear = Math.floor((today - new Date(today.getFullYear(), 0, 0)) / (1000 * 60 * 60 * 24));
            var selectedIndex = dayOfYear % featured.length;

            // Sort/reorder featured so selected element is first as "عرض الأسبوع"
            var reordered = [featured[selectedIndex]].concat(featured.filter(function(_, idx){ return idx !== selectedIndex; }));

            var html = '';
            reordered.forEach(function(o, idx) {
                var img = (o.images && o.images[0]) || 'images/logo.jpg';
                var badgeText = (idx === 0) ? '🌟 عرض الأسبوع' : 'حصري آفاق';
                var badgeStyle = (idx === 0) ? 'background:#e67e22; color:#fff;' : '';

                html += '<a href="' + buildOfferUrl(o) + '" class="silo-exclusive-card">' +
                    '<img src="' + img + '" alt="' + escHtml(o.title || '') + ' | آفاق الإنجاز العقاري" loading="lazy">' +
                    '<div class="silo-exclusive-info">' +
                    '<span class="silo-exclusive-badge" style="' + badgeStyle + '">' + badgeText + '</span>' +
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

    // ===== Compare Page Generator =====
    function renderComparePage() {
        var emptyEl = document.getElementById('compare-empty');
        var tableContainer = document.getElementById('compare-table-container');
        if (!tableContainer) return;

        var cmpList = getCompare();
        if (!cmpList || cmpList.length === 0) {
            if (emptyEl) emptyEl.style.display = 'block';
            tableContainer.style.display = 'none';
            return;
        }

        fetchOffers(function(allOffers) {
            var cmpIds = cmpList.map(function(c){ return c.id; });
            var matchedOffers = allOffers.filter(function(o){ return cmpIds.indexOf(o.id) >= 0; });

            if (matchedOffers.length === 0) {
                if (emptyEl) emptyEl.style.display = 'block';
                tableContainer.style.display = 'none';
                return;
            }

            if (emptyEl) emptyEl.style.display = 'none';
            tableContainer.style.display = 'block';

            var avgs = computeAverages(allOffers);

            // Compute metrics for best value
            var offerMetrics = matchedOffers.map(function(o) {
                var price = Number(o.price) || 0;
                var size = Number(o.size_sqm) || 0;
                var unitPrice = (price > 0 && size > 0) ? Math.round(price / size) : 0;

                var rawCat = o.category || o.property_type || o.type || '';
                var cat = rawCat;
                if (rawCat === 'farm') cat = 'مزرعة';
                if (rawCat === 'resthouse') cat = 'استراحة';
                if (rawCat === 'land') cat = 'أرض سكنية';

                var catAvg = (avgs[cat] && avgs[cat].avgUnitPrice) ? avgs[cat].avgUnitPrice : 0;
                var devPct = (unitPrice > 0 && catAvg > 0) ? Math.round(((unitPrice - catAvg) / catAvg) * 100) : null;

                return {
                    offer: o,
                    cat: cat,
                    unitPrice: unitPrice,
                    catAvg: catAvg,
                    devPct: devPct
                };
            });

            // Find best value (lowest unit price or greatest negative deviation)
            var bestOffer = null;
            var validMetrics = offerMetrics.filter(function(m){ return m.unitPrice > 0; });
            if (validMetrics.length > 0) {
                validMetrics.sort(function(a, b){ return a.unitPrice - b.unitPrice; });
                bestOffer = validMetrics[0];
            }

            var html = '<div style="overflow-x:auto; background:#ffffff; border-radius:12px; border:1px solid #e2d9c8; padding:20px; box-shadow:0 4px 20px rgba(0,0,0,0.06);">' +
                '<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border-bottom:2px solid #C4A956; padding-bottom:10px;">' +
                '<h2 style="margin:0; color:#2A5050; font-size:1.3rem;"><i class="fas fa-balance-scale"></i> جدول مقارنة العقارات المحددة</h2>' +
                '<button onclick="localStorage.setItem(\'afaq_compare\',\'[]\'); location.reload();" class="btn" style="background:#e74c3c; color:#fff; border:none; padding:8px 16px; border-radius:6px; cursor:pointer;"><i class="fas fa-trash-alt"></i> مسح المقارنة</button>' +
                '</div>';

            if (bestOffer) {
                html += '<div style="background:#e8f8f5; border:1px solid #27ae60; border-radius:10px; padding:15px; margin-bottom:20px; color:#1e8449;">' +
                    '<h4 style="margin:0 0 5px 0; font-size:1.1rem;"><i class="fas fa-trophy"></i> خلاصة البوصلة: العقار الأفضل قيمةً للمتر</h4>' +
                    '<div>يعتبر <strong>' + escHtml(bestOffer.offer.title) + '</strong> هو الأفضل قيمةً للمتر بسعر <strong>' + bestOffer.unitPrice.toLocaleString('en-US') + ' ريال/م²</strong>' +
                    (bestOffer.devPct !== null ? ' (أقل بـ ' + Math.abs(bestOffer.devPct) + '% عن متوسط فئة ' + bestOffer.cat + ')' : '') +
                    '.</div>' +
                    '</div>';
            }

            html += '<table style="width:100%; border-collapse:collapse; min-width:600px; text-align:right;">' +
                '<thead><tr style="background:#2A5050; color:#fff;">' +
                '<th style="padding:12px; border:1px solid #1B3D3D; width:180px;">وجه المقارنة</th>';

            matchedOffers.forEach(function(o) {
                html += '<th style="padding:12px; border:1px solid #1B3D3D; text-align:center;">' +
                    '<div>' + escHtml(o.title) + '</div>' +
                    '<button onclick="toggleCompare(\'' + o.id + '\',\'\',\'\'); renderComparePage();" style="background:none; border:none; color:#e8c969; cursor:pointer; font-size:0.85rem; margin-top:4px;"><i class="fas fa-times-circle"></i> إزالة</button>' +
                    '</th>';
            });
            html += '</tr></thead><tbody>';

            // Rows setup
            var rows = [
                {
                    label: 'الصورة الرئيسية',
                    fn: function(m) {
                        var img = (m.offer.images && m.offer.images[0]) ? m.offer.images[0] : 'images/logo.jpg';
                        return '<img src="' + img + '" style="width:120px; height:80px; object-fit:cover; border-radius:6px;" alt="' + escHtml(m.offer.title) + '">';
                    }
                },
                {
                    label: 'الفئة والنوع',
                    fn: function(m) { return escHtml(m.cat); }
                },
                {
                    label: 'الموقع والمنطقة',
                    fn: function(m) { return escHtml(m.offer.area || 'الخرج'); }
                },
                {
                    label: 'المساحة الإجمالية',
                    fn: function(m) { return m.offer.size_sqm ? escHtml(m.offer.size_sqm) + ' م²' : 'غير محددة'; }
                },
                {
                    label: 'السعر الإجمالي',
                    fn: function(m) { return m.offer.price_text || (m.offer.price ? m.offer.price.toLocaleString('en-US') + ' ريال' : 'غير محدد'); }
                },
                {
                    label: 'سعر المتر',
                    fn: function(m) { return m.unitPrice > 0 ? '<strong>' + m.unitPrice.toLocaleString('en-US') + ' ريال/م²</strong>' : 'غير محسوب'; }
                },
                {
                    label: 'متوسط الفئة في البوصلة',
                    fn: function(m) { return m.catAvg > 0 ? m.catAvg.toLocaleString('en-US') + ' ريال/م²' : 'غير متوفر'; }
                },
                {
                    label: 'انحراف السعر عن المتوسط',
                    fn: function(m) {
                        if (m.devPct === null) return '—';
                        if (m.devPct > 0) return '<span style="color:#d63031; font-weight:bold;">أعلى بـ ' + m.devPct + '% 🔺</span>';
                        if (m.devPct < 0) return '<span style="color:#27ae60; font-weight:bold;">أقل بـ ' + Math.abs(m.devPct) + '% 🔻 (قيمة ممتازة)</span>';
                        return '<span style="color:#2980b9; font-weight:bold;">مطابق للمتوسط 🎯</span>';
                    }
                },
                {
                    label: 'التواصل والاستفسار',
                    fn: function(m) {
                        var waUrl = 'https://wa.me/' + OFFICE_WHATSAPP + '?text=' + encodeURIComponent('استفسار عن مقارنة عقار: ' + m.offer.title);
                        return '<a href="' + waUrl + '" target="_blank" class="btn" style="display:inline-block; padding:8px 14px; background:#25D366; color:#fff; border-radius:6px; text-decoration:none; font-size:0.88rem; font-weight:bold;"><i class="fab fa-whatsapp"></i> تواصل عبر واتساب</a>';
                    }
                }
            ];

            rows.forEach(function(row, idx) {
                var bg = idx % 2 === 0 ? '#fdfdfd' : '#f8f6f0';
                html += '<tr style="background:' + bg + ';">' +
                    '<td style="padding:12px; border:1px solid #eee; font-weight:bold; color:#2A5050;">' + row.label + '</td>';
                offerMetrics.forEach(function(m) {
                    html += '<td style="padding:12px; border:1px solid #eee; text-align:center;">' + row.fn(m) + '</td>';
                });
                html += '</tr>';
            });

            html += '</tbody></table></div>';
            tableContainer.innerHTML = html;
        });
    }
    window.renderComparePage = renderComparePage;

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
        renderCompassWidgets();
        updateFavCounter();
        updateCompareDrawer();
        renderComparePage();
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
