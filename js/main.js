/* ============================================
   مكتب آفاق الإنجاز العقاري - ملف JavaScript الرئيسي
   ============================================ */

const PROPERTY_TYPE_MAP = {
    'مزرعة': 'farm', 'farm': 'farm', 'farms': 'farm', 'زراعي': 'farm',
    'استراحة': 'resthouse', 'resthouse': 'resthouse', 'resthouses': 'resthouse',
    'أرض سكنية': 'land', 'land': 'land', 'lands': 'land', 'سكني': 'land'
};

const DEFAULT_IMAGES = {
    'farm': 'images/cat-farms.jpg',
    'resthouse': 'images/cat-rest.jpg',
    'land': 'images/cat-lands.jpg'
};

const TYPE_LABELS_AR = {
    'farm': 'مزرعة',
    'resthouse': 'استراحة',
    'land': 'أرض سكنية'
};

function normalizePropertyType(type) {
    const t = String(type || '').toLowerCase().trim();
    return PROPERTY_TYPE_MAP[t] || 'land';
}

function getDefaultImage(type) {
    return DEFAULT_IMAGES[normalizePropertyType(type)] || 'images/farms-bg.jpg';
}

function getPropertyCategory(type) {
    return TYPE_LABELS_AR[normalizePropertyType(type)] || 'عقار';
}

function formatPropertyPrice(price) {
    const num = Number(price) || 0;
    return num > 0 ? `${num.toLocaleString('en-US')} SAR` : 'Contact for Price';
}

function getPropertyImages(p) {
    const photos = p.photo_urls || p.photos || p.images || [];
    const validPhotos = photos.filter(url => url && (url.startsWith('http') || url.startsWith('images/')));
    return validPhotos.length > 0 ? validPhotos : [getDefaultImage(p.type)];
}

function normalizeFeatures(features) {
    if (Array.isArray(features)) return features;
    if (typeof features === 'object' && features !== null) {
        return Object.entries(features).map(([k, v]) => `${k}: ${v}`);
    }
    return [];
}

let OFFICE_DATA = null;

async function loadOfficeData() {
    OFFICE_DATA = {
        name: 'مكتب آفاق الإنجاز العقاري',
        phones: { whatsapp_calls: '0545888931' },
        google_maps: '',
        email: ''
    };
    return OFFICE_DATA;
}

function getWhatsappNumber(numKey = 'whatsapp1') {
    const number = (typeof CONTACTS !== 'undefined' && CONTACTS[numKey]) || OFFICE_DATA?.phones?.whatsapp_calls || '0545888931';
    return number.replace(/^0/, '966').replace(/\D/g, '');
}

function getDefaultMap() {
    return OFFICE_DATA?.google_maps || '';
}

function getAreaData(area) {
    const areas = OFFICE_DATA?.areas || {};
    return areas[area] || areas['الرحمانية'] || {};
}

function getBouslaPrice(area, type) {
    const prices = getAreaData(area);
    if (type === 'farm') return prices.farm_avg_price_sqm ? `${prices.farm_avg_price_sqm} ريال/م²` : 'غير متوفر';
    if (type === 'resthouse') return prices.resthouse_avg_price ? `${prices.resthouse_avg_price} ريال` : 'غير متوفر';
    return prices.land_avg_price_sqm ? `${prices.land_avg_price_sqm} ريال/م²` : 'غير متوفر';
}

let OFFERS = [];
let CURRENT_SORT = 'newest';
const API_BASE_URL = 'https://worker-production-7713.up.railway.app';

function getShortUrl(offerId) {
    if (!offerId) return 'https://abonasr0907-beep.github.io/';
    const str = String(offerId);
    if (str.startsWith('PROP-')) {
        const num = parseInt(str.replace('PROP-', ''), 10);
        return `https://abonasr0907-beep.github.io/?p=${num}`;
    }
    return `https://abonasr0907-beep.github.io/?p=${str}`;
}

async function loadOffers(defaultFilter = 'all') {
    let rawProperties = [];
    let loadFailed = false;

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);
        const response = await fetch(`${API_BASE_URL}/api/properties`, {
            cache: 'no-store',
            signal: controller.signal
        });
        clearTimeout(timeoutId);
        if (response.ok) {
            const data = await response.json();
            rawProperties = Array.isArray(data) ? data : (data.properties || []);
        } else {
            throw new Error(`HTTP ${response.status}`);
        }
    } catch (apiError) {
        console.warn('تعذر الجلب من API الحي، محاولة الجلب المحلي:', apiError);
        try {
            const res = await fetch('data/properties.json', { cache: 'no-store' });
            if (res.ok) {
                const data = await res.json();
                const propsArr = Array.isArray(data.properties) ? data.properties : (Array.isArray(data) ? data : []);
                rawProperties.push(...propsArr);
            }
        } catch (e) {
            console.warn('تعذر قراءة data/properties.json:', e);
        }

        if (rawProperties.length === 0) loadFailed = true;
    }

    if (loadFailed) {
        const grid = document.getElementById('offers-grid');
        if (grid) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 50px; color: #e74c3c; margin-bottom: 15px;"></i>
                    <h3 style="color: #2A5050; margin-bottom: 10px;">تعذر التحميل</h3>
                    <p style="color: #555;">تعذر جلب البيانات حالياً. يرجى المحاولة لاحقاً.</p>
                </div>
            `;
        }
        return;
    }

    const seen = new Set();
    OFFERS = rawProperties.map(p => {
        const typeVal = normalizePropertyType(p.type);
        const catVal = getPropertyCategory(p.type);
        const photoUrls = getPropertyImages(p);
        const feats = normalizeFeatures(p.features);

        return {
            id: p.id || `PROP-${Math.random()}`,
            type: typeVal,
            category: catVal,
            title: p.title || `${catVal} في ${p.location || p.area || 'الخرج'}`,
            area: p.location || p.area || 'الخرج',
            size_sqm: Number(p.size_sqm || p.size || p.area || 0),
            price: Number(p.price || 0),
            price_text: formatPropertyPrice(p.price),
            description: p.description || '',
            features: feats,
            images: photoUrls,
            map_link: p.map_link,
            date_added: p.date || p.date_added || p.created_at || '',
            featured: p.is_vip || p.featured || false
        };
    }).filter(o => {
        if (!o.id || seen.has(o.id)) return false;
        seen.add(o.id);
        return true;
    });

    renderOffers(defaultFilter);
    updateStats();

    if (typeof propertyRecommender !== 'undefined') {
        propertyRecommender.setProperties(OFFERS);
    }
}

async function handlePropertyQueryParam() {
    const urlParams = new URLSearchParams(window.location.search);
    let propParam = urlParams.get('p') || urlParams.get('property');
    if (!propParam) return;

    let targetId = propParam;
    if (!isNaN(propParam) && !propParam.startsWith('PROP-')) {
        targetId = `PROP-${String(propParam).padStart(10, '0')}`;
    }

    let targetOffer = OFFERS.find(o => o.id === targetId || o.id === propParam);

    if (!targetOffer) {
        try {
            const res = await fetch(`${API_BASE_URL}/api/properties/${targetId}`);
            if (res.ok) {
                const p = await res.json();
                console.log('Fetched single property API response for', targetId, p);
                const typeVal = (p.type === 'مزرعة' || p.type === 'farm' || p.type === 'farms') ? 'farm' : ((p.type === 'استراحة' || p.type === 'resthouse' || p.type === 'resthouses') ? 'resthouse' : 'land');
                const catVal = typeVal === 'farm' ? 'مزرعة' : (typeVal === 'resthouse' ? 'استراحة' : 'أرض سكنية');
                const photoUrl = (p.photo_urls && p.photo_urls.length > 0) ? p.photo_urls[0] : (typeVal === 'farm' ? 'images/cat-farms.jpg' : (typeVal === 'resthouse' ? 'images/cat-rest.jpg' : 'images/cat-lands.jpg'));

                let feats = [];
                if (Array.isArray(p.features)) {
                    feats = p.features;
                } else if (typeof p.features === 'object' && p.features !== null) {
                    feats = Object.entries(p.features).map(([k, v]) => `${k}: ${v}`);
                }

                targetOffer = {
                    id: p.id,
                    type: typeVal,
                    category: catVal,
                    title: p.title || `${catVal} في ${p.location || p.area || 'الخرج'}`,
                    area: p.location || p.area || 'الخرج',
                    size_sqm: Number(p.size_sqm || p.size || p.area || 0),
                    price: Number(p.price || 0),
                    price_text: p.price ? `${Number(p.price).toLocaleString('en-US')} SAR` : (p.price_text || 'Contact for Price'),
                    description: p.description || '',
                    features: feats,
                    images: [photoUrl],
                    map_link: p.map_link,
                    featured: p.is_vip || false
                };
            }
        } catch (e) {}
    }

    const grid = document.getElementById('offers-grid');
    if (!grid) return;

    if (targetOffer) {
        if (typeof setChatContext === 'function') {
            setChatContext(targetOffer);
        }

        const bouslaPrice = getBouslaPrice(targetOffer.area, targetOffer.type);
        const featuresHtml = (targetOffer.features || []).map(f => `<span class="offer-feature-tag">${f}</span>`).join('');
        const mapLink = targetOffer.map_link || getDefaultMap();
        const shortUrl = getShortUrl(targetOffer.id);
        const waText = encodeURIComponent(`أرغب بالاستفسار عن: ${targetOffer.title} ${shortUrl}`);

        grid.innerHTML = `
            <div class="offer-card single-property-view" style="grid-column: 1/-1; max-width: 800px; margin: 0 auto;">
                <div class="offer-card-img-wrapper" id="single-gallery" style="height: 350px;">
                    <span class="offer-badge">${targetOffer.category}</span>
                    ${targetOffer.featured ? '<span class="offer-badge-featured">⭐ عرض مميز</span>' : ''}
                </div>
                <div class="offer-card-body" style="padding: 24px;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h2>${targetOffer.title}</h2>
                        <span style="background:#C4A956; color:#fff; padding:4px 12px; border-radius:12px; font-weight:bold;">${targetOffer.id}</span>
                    </div>
                    <div class="offer-location" style="font-size: 1.1rem; margin: 10px 0;">
                        <i class="fas fa-map-marker-alt"></i> ${targetOffer.area} - الخرج
                    </div>
                    <div class="offer-details" style="font-size: 1.1rem; margin-bottom: 15px;">
                        <span><i class="fas fa-ruler-combined"></i> ${targetOffer.size_sqm} م²</span>
                        <span><i class="fas fa-tag"></i> ${targetOffer.category}</span>
                    </div>
                    <div class="offer-price" style="font-size: 1.5rem;">${targetOffer.price_text}</div>
                    ${targetOffer.description ? `<p style="margin: 15px 0; line-height: 1.6; color: rgba(255,255,255,0.9);">${targetOffer.description}</p>` : ''}
                    <div class="offer-features" style="margin: 15px 0;">${featuresHtml}</div>
                    <div class="offer-bousla">
                        <div class="offer-bousla-title">
                            <i class="fas fa-compass"></i> البوصلة العقارية - ${targetOffer.area}
                        </div>
                        <div class="offer-bousla-data">
                            متوسط سعر المتر: <strong>${bouslaPrice}</strong><br>
                            <small>المصدر: منصة المؤشرات العقارية - الهيئة العامة للعقار</small>
                        </div>
                    </div>
                    <div class="offer-actions" style="margin-top: 20px;">
                        <a href="${mapLink}" target="_blank" class="offer-btn offer-btn-map">
                            <i class="fas fa-map-marked-alt"></i> الخريطة
                        </a>
                        <a href="https://wa.me/${getWhatsappNumber()}?text=${waText}" target="_blank" class="offer-btn offer-btn-contact">
                            <i class="fab fa-whatsapp"></i> تواصل عبر الواتساب
                        </a>
                        <button onclick="if(typeof propertyComparison !== 'undefined') propertyComparison.addToCompare(OFFERS.find(o=>o.id==='${targetOffer.id}')||targetOffer)" class="offer-btn offer-btn-map">
                            <i class="fas fa-balance-scale"></i> مقارنة
                        </button>
                        <button onclick="shareOffer('${targetOffer.title}', '${shortUrl}')" class="offer-btn offer-btn-share">
                            <i class="fas fa-share-alt"></i> 📤 مشاركة العرض
                        </button>
                    </div>
                    <div style="margin-top:15px; display:flex; gap:10px; flex-wrap:wrap;">
                        <button class="btn btn-sm btn-outline" onclick="if(typeof inquirySystem !== 'undefined') inquirySystem.showInquiryModal('${targetOffer.id}')">
                            <i class="fas fa-question-circle"></i> طلب معلومات
                        </button>
                    </div>
                </div>
            </div>
        `;
        // Inject RealEstateListing JSON-LD Schema
        try {
            const existingSchema = document.getElementById('real-estate-listing-schema');
            if (existingSchema) existingSchema.remove();

            const schemaScript = document.createElement('script');
            schemaScript.id = 'real-estate-listing-schema';
            schemaScript.type = 'application/ld+json';
            schemaScript.text = JSON.stringify({
                "@context": "https://schema.org",
                "@type": "RealEstateListing",
                "name": targetOffer.title,
                "description": targetOffer.description || targetOffer.title,
                "url": window.location.href,
                "image": targetOffer.images && targetOffer.images[0] ? targetOffer.images[0] : "",
                "offers": {
                    "@type": "Offer",
                    "price": targetOffer.price || 0,
                    "priceCurrency": "SAR"
                },
                "floorSize": {
                    "@type": "QuantitativeValue",
                    "value": targetOffer.size_sqm || 0,
                    "unitCode": "MTK"
                },
                "containedInPlace": {
                    "@type": "Place",
                    "name": `${targetOffer.area} - الخرج`
                }
            });
            document.head.appendChild(schemaScript);
        } catch (e) {}

        setTimeout(() => {
            const galleryContainer = document.getElementById('single-gallery');
            if (galleryContainer && targetOffer) {
                renderImageGallery(galleryContainer, targetOffer.images, targetOffer.title);
            }
        }, 100);

        const offersSection = document.getElementById('offers');
        if (offersSection) {
            offersSection.scrollIntoView({ behavior: 'smooth' });
        }
    }
}

function shareOffer(title, url) {
    if (navigator.share) {
        navigator.share({ title: title, url: url }).catch(() => {});
    } else {
        navigator.clipboard.writeText(url).then(() => {
            showToast('تم نسخ رابط العرض بنجاح! 📋');
        }).catch(() => {
            showToast('الرابط: ' + url);
        });
    }
}

function setSort(sortType) {
    CURRENT_SORT = sortType;
    document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.sort-btn[data-sort="${sortType}"]`);
    if (btn) btn.classList.add('active');

    const activeType = document.querySelector('.filter-btn.active');
    const typeFilter = activeType ? activeType.dataset.filter : 'all';
    const activeArea = document.querySelector('.area-filter-btn.active');
    const areaFilter = activeArea ? activeArea.dataset.area : 'all';
    renderOffers(typeFilter, areaFilter);
}

function renderOffers(filter = 'all', areaFilter = 'all') {
    const grid = document.getElementById('offers-grid');
    if (!grid) return;

    let filtered = OFFERS;
    if (filter !== 'all') {
        filtered = filtered.filter(o => o.type === filter);
    }
    if (areaFilter !== 'all') {
        filtered = filtered.filter(o => o.area === areaFilter);
    }

    // Sort VIP first always
    filtered = [...filtered].sort((a, b) => {
        if (a.featured !== b.featured) {
            return a.featured ? -1 : 1;
        }
        if (CURRENT_SORT === 'price_asc') {
            return a.price - b.price;
        } else if (CURRENT_SORT === 'price_desc') {
            return b.price - a.price;
        } else if (CURRENT_SORT === 'area_asc') {
            return a.size_sqm - b.size_sqm;
        } else if (CURRENT_SORT === 'area_desc') {
            return b.size_sqm - a.size_sqm;
        }
        return (b.id || '').localeCompare(a.id || '');
    });

    if (filtered.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                <i class="fas fa-search" style="font-size: 50px; color: #C4A956; margin-bottom: 15px;"></i>
                <h3 style="color: #2A5050; margin-bottom: 10px;">لا توجد عروض مطابقة</h3>
                <p style="color: #555;">لم تجد ما تبحث عنه؟ <a href="#" onclick="showInquiryForm(); return false;" style="color: #C4A956; font-weight: 700;">قدم طلب استفسار</a></p>
            </div>
        `;
        return;
    }

    grid.innerHTML = filtered.map(offer => {
        const bouslaPrice = getBouslaPrice(offer.area, offer.type);
        const translateKeyMap = {
            'trees_count': 'عدد الأشجار',
            'greenhouses_count': 'عدد البيوت المحمية',
            'fenced': 'مسوّر',
            'facade': 'الواجهة',
            'land_kind': 'نوع الأرض',
            'electricity': 'الكهرباء',
            'well': 'بئر',
            'pool': 'مسبح'
        };
        const featuresHtml = (offer.features || []).slice(0, 4).map(f => {
            let label = f;
            if (f.includes(':')) {
                const parts = f.split(':');
                const k = parts[0].trim().toLowerCase();
                const v = parts.slice(1).join(':').trim();
                const translatedK = translateKeyMap[k] || parts[0].trim();
                label = `${translatedK}: ${v}`;
            } else {
                label = translateKeyMap[f.trim().toLowerCase()] || f;
            }
            return `<span class="offer-feature-tag">${label}</span>`;
        }).join('');
        const featuredBadge = offer.featured ? '<span class="offer-badge-featured">⭐ عرض مميز</span>' : '';
        const categoryBadge = `<span class="offer-badge">${offer.category}</span>`;
        const mapLink = offer.map_link || getDefaultMap();
        const shortUrl = getShortUrl(offer.id);
        const waText = encodeURIComponent(`أرغب بالاستفسار عن: ${offer.title} ${shortUrl}`);

        return `
            <div class="offer-card">
                <div class="offer-card-img-wrapper" id="gallery-${offer.id}">
                    ${categoryBadge}
                    ${featuredBadge}
                </div>
                <div class="offer-card-body">
                    <h3>${offer.title}</h3>
                    <div class="offer-location">
                        <i class="fas fa-map-marker-alt"></i> ${offer.area} - الخرج
                    </div>
                    <div class="offer-details">
                        <span><i class="fas fa-ruler-combined"></i> ${offer.size_sqm} م²</span>
                        <span><i class="fas fa-tag"></i> ${offer.category}</span>
                    </div>
                    <div class="offer-price">${offer.price_text}</div>
                    <div class="offer-features">${featuresHtml}</div>
                    <div class="offer-bousla">
                        <div class="offer-bousla-title">
                            <i class="fas fa-compass"></i> البوصلة العقارية - ${offer.area}
                        </div>
                        <div class="offer-bousla-data">
                            متوسط سعر المتر: <strong>${bouslaPrice}</strong><br>
                            <small>المصدر: منصة المؤشرات العقارية - الهيئة العامة للعقار</small>
                        </div>
                    </div>
                    <div class="offer-actions">
                        <a href="${mapLink}" target="_blank" class="offer-btn offer-btn-map">
                            <i class="fas fa-map-marked-alt"></i> الخريطة
                        </a>
                        <a href="https://wa.me/${getWhatsappNumber()}?text=${waText}" target="_blank" class="offer-btn offer-btn-contact">
                            <i class="fab fa-whatsapp"></i> واتساب
                        </a>
                        <button onclick="if(typeof propertyComparison !== 'undefined') propertyComparison.addToCompare(OFFERS.find(o=>o.id==='${offer.id}'))" class="offer-btn offer-btn-map">
                            <i class="fas fa-balance-scale"></i> مقارنة
                        </button>
                        <button onclick="shareOffer('${offer.title}', '${shortUrl}')" class="offer-btn offer-btn-share">
                            <i class="fas fa-share-alt"></i> 📤 مشاركة
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    setTimeout(() => {
        filtered.forEach(offer => {
            const galleryContainer = document.getElementById(`gallery-${offer.id}`);
            if (galleryContainer) {
                renderImageGallery(galleryContainer, offer.images, offer.title);
            }
        });

        const cards = grid.querySelectorAll('.offer-card');
        cards.forEach((el, i) => {
            el.style.opacity = '0';
            el.style.transform = 'translateY(24px)';
            el.style.transition = `opacity 0.6s ease ${i * 0.08}s, transform 0.6s ease ${i * 0.08}s`;
            setTimeout(() => {
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 50);
        });
    }, 100);
}

function filterOffers(type) {
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    const btn = document.querySelector(`.filter-btn[data-filter="${type}"]`);
    if (btn) btn.classList.add('active');

    const activeArea = document.querySelector('.area-filter-btn.active');
    const areaFilter = activeArea ? activeArea.dataset.area : 'all';
    renderOffers(type, areaFilter);
}

function filterByArea(area) {
    document.querySelectorAll('.area-filter-btn').forEach(b => b.classList.remove('active'));
    if (area !== 'all') {
        const btn = document.querySelector(`.area-filter-btn[data-area="${area}"]`);
        if (btn) btn.classList.add('active');
    }
    const activeType = document.querySelector('.filter-btn.active');
    const typeFilter = activeType ? activeType.dataset.filter : 'all';
    renderOffers(typeFilter, area);
}

function updateStats() {
    const farms = OFFERS.filter(o => o.type === 'farm').length;
    const resthouses = OFFERS.filter(o => o.type === 'resthouse').length;
    const lands = OFFERS.filter(o => o.type === 'land').length;

    const farmEl = document.getElementById('stat-farms');
    const restEl = document.getElementById('stat-resthouses');
    const landEl = document.getElementById('stat-lands');
    const totalEl = document.getElementById('stat-total');

    if (farmEl) farmEl.textContent = farms;
    if (restEl) restEl.textContent = resthouses;
    if (landEl) landEl.textContent = lands;
    if (totalEl) totalEl.textContent = OFFERS.length;
}

async function renderBousla() {
    const grid = document.getElementById('bousla-grid');
    if (!grid) return;

    let compassData = null;
    try {
        const response = await fetch(`${API_BASE_URL}/api/compass`, { cache: 'no-store' });
        if (response.ok) {
            compassData = await response.json();
        }
    } catch (e) {}

    if (compassData && Object.keys(compassData).length > 0) {
        grid.innerHTML = Object.entries(compassData).map(([area, info]) => {
            const avgPrice = info.avg_sqm_price ? `${Number(info.avg_sqm_price).toLocaleString('ar-SA')} ريال/م²` : 'غير متوفر';
            return `
                <div class="bousla-card">
                    <h3><i class="fas fa-map-marker-alt"></i> ${area}</h3>
                    <div class="price-row"><span>متوسط سعر المتر</span><span>${avgPrice}</span></div>
                    <div class="price-row"><span>عدد العروض</span><span>${info.count || 0}</span></div>
                </div>
            `;
        }).join('');
    } else {
        const areas = OFFICE_DATA?.areas || {};
        grid.innerHTML = Object.entries(areas).map(([area, prices]) => `
            <div class="bousla-card">
                <h3><i class="fas fa-map-marker-alt"></i> ${area}</h3>
                <div class="price-row"><span>الأراضي السكنية</span><span>${prices.land_avg_price_sqm || 'غير متوفر'} ريال/م²</span></div>
                <div class="price-row"><span>المزارع</span><span>${prices.farm_avg_price_sqm || 'غير متوفر'} ريال/م²</span></div>
                <div class="price-row"><span>الاستراحات</span><span>${prices.resthouse_avg_price || 'غير متوفر'} ريال</span></div>
            </div>
        `).join('');
    }
}

async function loadNews() {
    const grid = document.getElementById('news-grid');
    if (!grid) return;

    const defaultNews = [
        { date: "2025-08-05", title: "الهيئة العامة للعقار تستعرض التجربة السعودية في منتدى قطر العقاري 2025", desc: "شاركت الهيئة العامة للعقار في منتدى قطر العقاري 2025 لاستعراض التجربة السعودية المتميزة في تطوير القطاع العقاري.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" },
        { date: "2025-08-04", title: "تحديث مؤشرات الأسعار العقارية في مناطق المملكة", desc: "أعلنت الهيئة العامة للعقار عن تحديث المؤشرات العقارية لشهر أغسطس، مع تباين في الأسعار بين المناطق.", link: "https://rei.rega.gov.sa", source: "منصة المؤشرات العقارية" },
        { date: "2025-08-03", title: "نظام إيجار الجديد: تسهيلات إضافية للمستفيدين", desc: "أطلقت الهيئة العامة للعقار تحديثات جديدة على نظام إيجار لتسهيل المعاملات العقارية.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" },
        { date: "2025-08-02", title: "الخرج تشهد نمواً في الطلب على الأراضي الزراعية", desc: "سجلت محافظة الخرج نمواً ملحوظاً في الطلب على الأراضي الزراعية والمزارع خلال الربع الحالي.", link: "#", source: "تقارير سوقية" },
        { date: "2025-08-01", title: "بوابة العقار الجيومكانية: خدمة جديدة لعرض البيانات العقارية", desc: "أطلقت الهيئة العامة للعقار بوابة العقار الجيومكانية لعرض البيانات العقارية المكانية عبر خرائط دقيقة.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" }
    ];

    const storedNews = localStorage.getItem('afaq_news');
    let news = defaultNews;
    if (storedNews) {
        try { news = JSON.parse(storedNews); } catch(e) { news = defaultNews; }
    }

    grid.innerHTML = news.map(item => `
        <div class="news-card">
            <div class="news-date"><i class="far fa-calendar-alt"></i> ${item.date}</div>
            <h3>${item.title}</h3>
            <p>${item.desc}</p>
            ${item.link && item.link !== '#' ? `<a href="${item.link}" target="_blank">اقرأ المزيد <i class="fas fa-chevron-left"></i></a>` : ''}
            <div class="news-source"><i class="fas fa-landmark"></i> ${item.source}</div>
        </div>
    `).join('');
}

const AI_KNOWLEDGE = {
    greeting: "أهلاً وسهلاً بك في مكتب آفاق الإنجاز العقاري! 👋 أنا مساعدك الذكي. لدي 20 سنة خبرة في السوق العقاري بالخرج والرياض. كيف يمكنني مساعدتك اليوم؟ يمكنك سؤالي عن المزارع، الاستراحات، الأراضي السكنية، أو خدماتنا.",
    farms: "🌿 لدينا مجموعة مميزة من المزارع في مخطط الرحمانية والهياثم والدلم والضبيعة والعفجة. أسعار المزارع تبدأ من 90 ريال/م² في الدلم وتصل إلى 150 ريال/م² في الهياثم. هل تريد تصفح عروض المزارع؟ <a href='farms.html'>اضغط هنا لعرض المزارع</a>",
    resthouses: "🏡 لدينا استراحات فاخرة في مختلف مناطق الخرج. الأسعار تتراوح بين 250,000 و1,500,000 ريال حسب الموقع والمساحة. <a href='resthouses.html'>اضغط هنا لعرض الاستراحات</a>",
    lands: "📍 لدينا أراضٍ سكنية في مخطط الرحمانية والهياثم والدلم والعفجة. متوسط السعر يتراوح بين 600 و1,100 ريال/م². <a href='lands.html'>اضغط هنا لعرض الأراضي السكنية</a>",
    services: "🔧 نقدم خدمات ما بعد البيع الشاملة: استخراج رخص البناء، المقاولات، التشطيب، إدارة الأملاك، حفر الآبار وتحديد مواقعها وتصويرها. <a href='services.html'>اضغط هنا لعرض الخدمات</a>",
    sell: "📈 هل تريد عرض عقارك في موقعنا؟ رائع! يمكنك تعبئة استبيان العرض عبر <a href='list-property.html'>هذه الصفحة</a> وسنتواصل معك في أقرب وقت.",
    inquiry: "🔍 لم تجد ما تبحث عنه؟ لا بأس! يمكنك تقديم طلب استفسار عبر <a href='inquiry.html'>هذه الصفحة</a> وسنقوم بمراجعته والتواصل معك.",
    get contact() {
        const c = typeof CONTACTS !== 'undefined' ? CONTACTS : { whatsapp1: '0545888931', call1: '0544699933', whatsapp2: '0561610748', email: 'afaqalqary@gmail.com' };
        return `📞 يمكنك التواصل معنا عبر:\n• واتساب: ${c.whatsapp1}\n• مكالمات: ${c.call1}\n• واتساب ومكالمات: ${c.whatsapp2}\n• البريد: ${c.email}`;
    },
    areas: "🗺️ نغطي بشكل رئيسي مخطط الرحمانية والمناطق المحيطة: الهياثم، الدلم، الضبيعة، العفجة. 90% من عروضنا في هذه المناطق.",
    bousla: "🧭 نعرض أسعار البوصلة العقارية (منصة المؤشرات العقارية للهيئة العامة للعقار) تحت كل عرض حسب موقعه الجغرافي. يمكنك أيضاً رؤية الأسعار في <a href='index.html#bousla'>قسم البوصلة العقارية</a>.",
    experience: "⭐ لمكتب آفاق الإنجاز العقاري 20 سنة خبرة في المجال العقاري بالخرج والرياض، ونحن نوفر لك أفضل العروض والخدمات.",
    maps: "🗺️ كل عرض لدينا مرتبط بخريطة Google Maps. يمكنك الضغط على زر 'الموقع على الخريطة' تحت أي عرض لرؤية الموقع بدقة.",
    default: "أنا هنا لمساعدتك في كل ما يخص العقار في الخرج والرياض. يمكنك سؤالي عن:\n• المزارع 🌿\n• الاستراحات 🏡\n• الأراضي السكنية 📍\n• خدمات ما بعد البيع 🔧\n• كيفية عرض عقارك 📈\n• التواصل معنا 📞\n\nماذا تريد أن تعرف؟"
};

function toggleAI() {
    const chatBox = document.getElementById('ai-chat-box');
    chatBox.classList.toggle('show');

    if (chatBox.classList.contains('show') && !chatBox.dataset.initialized) {
        addBotMessage(AI_KNOWLEDGE.greeting);
        addQuickReplies();
        chatBox.dataset.initialized = 'true';
    }
}

function closeAI() {
    document.getElementById('ai-chat-box').classList.remove('show');
}

function addBotMessage(text) {
    const messages = document.getElementById('ai-messages');
    const msg = document.createElement('div');
    msg.className = 'ai-message bot';
    msg.innerHTML = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

function addUserMessage(text) {
    const messages = document.getElementById('ai-messages');
    const msg = document.createElement('div');
    msg.className = 'ai-message user';
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
}

function addQuickReplies() {
    const container = document.getElementById('ai-quick-replies');
    if (!container) return;
    const replies = [
        { text: "🌿 المزارع", keyword: "farms" },
        { text: "🏡 الاستراحات", keyword: "resthouses" },
        { text: "📍 الأراضي السكنية", keyword: "lands" },
        { text: "🔧 الخدمات", keyword: "services" },
        { text: "📈 عرض عقاري", keyword: "sell" },
        { text: "📞 التواصل", keyword: "contact" }
    ];
    container.innerHTML = replies.map(r => `<button class="ai-quick-reply" onclick="sendQuickReply('${r.keyword}')">${r.text}</button>`).join('');
}

function sendQuickReply(keyword) {
    addUserMessage(getQuickReplyText(keyword));
    showTyping();
    setTimeout(() => {
        hideTyping();
        addBotMessage(AI_KNOWLEDGE[keyword] || AI_KNOWLEDGE.default);
    }, 800);
}

function getQuickReplyText(keyword) {
    const map = {
        farms: "أريد رؤية المزارع",
        resthouses: "أريد رؤية الاستراحات",
        lands: "أريد رؤية الأراضي السكنية",
        services: "ما هي خدماتكم؟",
        sell: "أريد عرض عقاري",
        contact: "كيف أتواصل معكم؟"
    };
    return map[keyword] || keyword;
}

function sendAIMessage() {
    const input = document.getElementById('ai-input');
    const text = input.value.trim();
    if (!text) return;

    addUserMessage(text);
    input.value = '';

    showTyping();
    setTimeout(() => {
        hideTyping();
        const response = getAIResponse(text);
        addBotMessage(response);
    }, 1000);
}

function getAIResponse(text) {
    const lower = text.toLowerCase();
    if (lower.includes('مزرعة') || lower.includes('مزارع') || lower.includes('زراعية')) return AI_KNOWLEDGE.farms;
    if (lower.includes('استراحة') || lower.includes('استراحات')) return AI_KNOWLEDGE.resthouses;
    if (lower.includes('أرض') || lower.includes('ارض') || lower.includes('اراضي')) return AI_KNOWLEDGE.lands;
    if (lower.includes('خدمة') || lower.includes('خدمات') || lower.includes('رخصة')) return AI_KNOWLEDGE.services;
    if (lower.includes('عرض') || lower.includes('بيع') || lower.includes('عقاري')) return AI_KNOWLEDGE.sell;
    if (lower.includes('استفسار') || lower.includes('طلب')) return AI_KNOWLEDGE.inquiry;
    if (lower.includes('تواصل') || lower.includes('واتساب') || lower.includes('جوال')) return AI_KNOWLEDGE.contact;
    if (lower.includes('منطقة') || lower.includes('مناطق') || lower.includes('الرحمانية')) return AI_KNOWLEDGE.areas;
    if (lower.includes('بوصلة') || lower.includes('اسعار')) return AI_KNOWLEDGE.bousla;
    if (lower.includes('خبرة') || lower.includes('سنة')) return AI_KNOWLEDGE.experience;
    if (lower.includes('خريطة') || lower.includes('موقع')) return AI_KNOWLEDGE.maps;
    if (lower.includes('سلام') || lower.includes('مرحبا') || lower.includes('اهلا')) return AI_KNOWLEDGE.greeting;

    return AI_KNOWLEDGE.default;
}

function showTyping() {
    const messages = document.getElementById('ai-messages');
    const typing = document.createElement('div');
    typing.className = 'ai-message bot';
    typing.id = 'typing-indicator';
    typing.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;
}

function hideTyping() {
    const typing = document.getElementById('typing-indicator');
    if (typing) typing.remove();
}

async function submitPropertyForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    try {
        await fetch(`${API_BASE_URL}/api/visitors`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'property_submission', ...data })
        });
    } catch (e) {}

    const requests = JSON.parse(localStorage.getItem('afaq_property_requests') || '[]');
    data.id = 'REQ-' + Date.now();
    data.date = new Date().toISOString();
    data.status = 'pending';
    requests.push(data);
    localStorage.setItem('afaq_property_requests', JSON.stringify(requests));

    const msg = `*طلب عرض عقار جديد* 📈\n\n` +
        `*الاسم:* ${data.name}\n` +
        `*نوع العقار:* ${data.propertyType || data.property_type || 'غير محدد'}\n` +
        `*الموقع:* ${data.location || 'غير محدد'}\n` +
        `*المساحة:* ${data.area || data.size || 'غير محدد'} م²\n` +
        `*السعر التقريبي:* ${data.price || 'غير محدد'} ريال\n` +
        `*رقم الجوال:* ${data.phone}\n` +
        (data.description ? `*الوصف:* ${data.description}\n` : '');

    window.open(`https://wa.me/${getWhatsappNumber()}?text=${encodeURIComponent(msg)}`, '_blank');

    const fs = document.getElementById('form-success');
    if (fs) fs.classList.add('show');
    event.target.reset();
    showToast('تم إرسال طلبك بنجاح! سنتواصل معك قريباً', 'success');

    setTimeout(() => {
        const fsR = document.getElementById('form-success');
        if (fsR) fsR.classList.remove('show');
    }, 5000);

    return false;
}

async function submitInquiryForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    try {
        await fetch(`${API_BASE_URL}/api/visitors`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ type: 'inquiry', ...data })
        });
    } catch (e) {}

    const inquiries = JSON.parse(localStorage.getItem('afaq_inquiries') || '[]');
    data.id = 'INQ-' + Date.now();
    data.date = new Date().toISOString();
    data.status = 'pending';
    inquiries.push(data);
    localStorage.setItem('afaq_inquiries', JSON.stringify(inquiries));

    const msg = `*طلب استفسار جديد* 🔍\n\n` +
        `*الاسم:* ${data.name}\n` +
        `*نوع العقار المطلوب:* ${data.propertyType || data.property_type || 'غير محدد'}\n` +
        `*المنطقة المفضلة:* ${data.location || data.area || 'غير محدد'}\n` +
        `*الميزانية:* ${data.budget ? data.budget + ' ريال' : 'غير محدد'}\n` +
        `*المساحة المطلوبة:* ${data.area || data.size || 'غير محدد'} م²\n` +
        `*رقم الجوال:* ${data.phone}\n` +
        (data.details ? `*التفاصيل:* ${data.details}\n` : '');

    window.open(`https://wa.me/${getWhatsappNumber()}?text=${encodeURIComponent(msg)}`, '_blank');

    const fs2 = document.getElementById('form-success');
    if (fs2) fs2.classList.add('show');
    event.target.reset();
    showToast('تم إرسال استفسارك بنجاح! سنقوم بمراجعته والتواصل معك', 'success');

    setTimeout(() => {
        const fsR = document.getElementById('form-success');
        if (fsR) fsR.classList.remove('show');
    }, 5000);

    return false;
}

function showInquiryForm() {
    window.location.href = 'inquiry.html';
}

function showToast(message, type = '') {
    const toast = document.createElement('div');
    toast.className = 'toast ' + type;
    toast.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function toggleMenu() {
    const menu = document.querySelector('#nav-menu, .nav-menu, .sidebar, .side-nav, .navigation-menu, .nav-links');
    if (!menu) return;
    let overlay = document.querySelector('#drawer-overlay, .drawer-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'drawer-overlay';
        overlay.className = 'drawer-overlay';
        overlay.onclick = toggleMenu;
        document.body.appendChild(overlay);
    }
    const isShowing = menu.classList.contains('show') || menu.classList.contains('active') || menu.classList.contains('open');
    if (isShowing) {
        menu.classList.remove('show', 'active', 'open');
        overlay.classList.remove('show', 'active', 'open');
    } else {
        menu.classList.add('show', 'active', 'open');
        overlay.classList.add('show', 'active', 'open');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const toggleBtn = document.querySelector('.sidebar-toggle, .menu-toggle, .nav-toggler, .btn-menu-toggle');
    const sidebar = document.querySelector('.sidebar, .side-nav, .navigation-menu, .nav-links, #nav-menu, .nav-menu');
    let overlay = document.querySelector('#drawer-overlay, .drawer-overlay');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
        document.addEventListener('click', function(e) {
            const currentOverlay = document.querySelector('#drawer-overlay, .drawer-overlay');
            if (sidebar && !sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('active', 'open', 'show');
                if (currentOverlay) {
                    currentOverlay.classList.remove('active', 'open', 'show');
                }
            }
        });
    }
});

function initStatsCounter() {
    const statNumbers = document.querySelectorAll('.stat-num[data-target]');
    if (!statNumbers.length) return;
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target);
                const duration = 2000;
                const start = performance.now();
                const prefix = el.textContent.includes('+') ? '+' : '';
                function update(currentTime) {
                    const elapsed = currentTime - start;
                    const progress = Math.min(elapsed / duration, 1);
                    const easeOut = 1 - Math.pow(1 - progress, 3);
                    const current = Math.floor(easeOut * target);
                    el.textContent = prefix + current.toLocaleString('ar-SA');
                    if (progress < 1) requestAnimationFrame(update);
                    else el.textContent = prefix + target.toLocaleString('ar-SA');
                }
                requestAnimationFrame(update);
                observer.unobserve(el);
            }
        });
    }, { threshold: 0.5 });
    statNumbers.forEach(el => observer.observe(el));
}

function applyHeroFilters() {
    const type = document.getElementById('filter-type')?.value || 'all';
    const location = document.getElementById('filter-location')?.value || 'all';
    const category = document.getElementById('filter-category')?.value || 'all';
    const params = new URLSearchParams();
    if (type !== 'all') params.set('type', type);
    if (location !== 'all') params.set('area', location);
    if (category !== 'all') params.set('category', category);
    const url = 'offers.html' + (params.toString() ? '?' + params.toString() : '');
    window.location.href = url;
}

function initScrollAnimations() {
    if (window._scrollObserver) {
        window._scrollObserver.disconnect();
    }
    const animatedElements = document.querySelectorAll('.feature-item, .cat-card, .why-item, .service-card, .why-card');
    window._scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                window._scrollObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -30px 0px' });

    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        window._scrollObserver.observe(el);
    });
}

function initHeaderScroll() {
    const header = document.querySelector('.main-header');
    if (!header) return;
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        if (currentScroll > 80) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    }, { passive: true });
}

// ==========================================================================
// معرض الصور المتعدد (Image Gallery)
// ==========================================================================

function renderImageGallery(container, images, title) {
    if (!images || images.length === 0) {
        images = ['images/farms-bg.jpg'];
    }

    let currentIndex = 0;

    const galleryHtml = `
        <div class="image-gallery" data-gallery-id="${Date.now()}">
            <div class="gallery-main">
                <img src="${images[0]}" alt="${title || ''}" class="gallery-main-img" loading="lazy">
                ${images.length > 1 ? `
                    <button class="gallery-nav gallery-prev" aria-label="السابق">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                    <button class="gallery-nav gallery-next" aria-label="التالي">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <div class="gallery-counter">
                        <span class="gallery-current">1</span> / <span class="gallery-total">${images.length}</span>
                    </div>
                ` : ''}
            </div>
            ${images.length > 1 ? `
                <div class="gallery-thumbs">
                    ${images.map((img, i) => `
                        <div class="gallery-thumb ${i === 0 ? 'active' : ''}" data-index="${i}">
                            <img src="${img}" alt="${title || ''} - ${i + 1}" loading="lazy">
                        </div>
                    `).join('')}
                </div>
                <div class="gallery-dots">
                    ${images.map((_, i) => `
                        <span class="gallery-dot ${i === 0 ? 'active' : ''}" data-index="${i}"></span>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;

    container.innerHTML += galleryHtml;

    if (images.length <= 1) {
        const mainImgOnly = container.querySelector('.gallery-main-img');
        if (mainImgOnly) {
            mainImgOnly.addEventListener('click', (e) => {
                e.stopPropagation();
                openLightbox(images, 0, title);
            });
        }
        return;
    }

    // عناصر المعرض
    const gallery = container.querySelector('.image-gallery');
    const mainImg = gallery.querySelector('.gallery-main-img');
    const prevBtn = gallery.querySelector('.gallery-prev');
    const nextBtn = gallery.querySelector('.gallery-next');
    const currentSpan = gallery.querySelector('.gallery-current');
    const thumbs = gallery.querySelectorAll('.gallery-thumb');
    const dots = gallery.querySelectorAll('.gallery-dot');

    // دالة تحديث الصورة
    function updateImage(index) {
        currentIndex = index;
        mainImg.src = images[index];
        if (currentSpan) currentSpan.textContent = index + 1;

        thumbs.forEach((t, i) => t.classList.toggle('active', i === index));
        dots.forEach((d, i) => d.classList.toggle('active', i === index));
    }

    // أزرار التنقل
    if (prevBtn) {
        prevBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const newIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
            updateImage(newIndex);
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const newIndex = currentIndex === images.length - 1 ? 0 : currentIndex + 1;
            updateImage(newIndex);
        });
    }

    // Thumbs
    thumbs.forEach(thumb => {
        thumb.addEventListener('click', (e) => {
            e.stopPropagation();
            updateImage(parseInt(thumb.dataset.index));
        });
    });

    // Dots
    dots.forEach(dot => {
        dot.addEventListener('click', (e) => {
            e.stopPropagation();
            updateImage(parseInt(dot.dataset.index));
        });
    });

    // Swipe على الموبايل
    let touchStartX = 0;
    let touchEndX = 0;

    const mainDiv = gallery.querySelector('.gallery-main');
    if (mainDiv) {
        mainDiv.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        }, { passive: true });

        mainDiv.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            handleSwipe();
        }, { passive: true });
    }

    function handleSwipe() {
        const diff = touchStartX - touchEndX;
        if (Math.abs(diff) > 50) {
            if (diff > 0) {
                const newIndex = currentIndex === images.length - 1 ? 0 : currentIndex + 1;
                updateImage(newIndex);
            } else {
                const newIndex = currentIndex === 0 ? images.length - 1 : currentIndex - 1;
                updateImage(newIndex);
            }
        }
    }

    // Zoom on click
    if (mainImg) {
        mainImg.addEventListener('click', (e) => {
            e.stopPropagation();
            openLightbox(images, currentIndex, title);
        });
    }
}

// Lightbox
function openLightbox(images, startIndex, title) {
    const lightbox = document.createElement('div');
    lightbox.className = 'lightbox-overlay';
    lightbox.innerHTML = `
        <div class="lightbox-content">
            <button class="lightbox-close" aria-label="إغلاق"><i class="fas fa-times"></i></button>
            <button class="lightbox-nav lightbox-prev" aria-label="السابق"><i class="fas fa-chevron-right"></i></button>
            <img src="${images[startIndex]}" alt="${title || ''}" class="lightbox-img">
            <button class="lightbox-nav lightbox-next" aria-label="التالي"><i class="fas fa-chevron-left"></i></button>
            <div class="lightbox-counter">${startIndex + 1} / ${images.length}</div>
        </div>
    `;

    document.body.appendChild(lightbox);
    document.body.style.overflow = 'hidden';

    let currentIdx = startIndex;
    const img = lightbox.querySelector('.lightbox-img');
    const counter = lightbox.querySelector('.lightbox-counter');

    function updateLightbox(idx) {
        currentIdx = idx;
        img.src = images[idx];
        counter.textContent = `${idx + 1} / ${images.length}`;
    }

    lightbox.querySelector('.lightbox-prev').addEventListener('click', () => {
        updateLightbox(currentIdx === 0 ? images.length - 1 : currentIdx - 1);
    });

    lightbox.querySelector('.lightbox-next').addEventListener('click', () => {
        updateLightbox(currentIdx === images.length - 1 ? 0 : currentIdx + 1);
    });

    lightbox.querySelector('.lightbox-close').addEventListener('click', () => {
        lightbox.remove();
        document.body.style.overflow = '';
    });

    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            lightbox.remove();
            document.body.style.overflow = '';
        }
    });

    // Keyboard navigation
    document.addEventListener('keydown', function handleKey(e) {
        if (e.key === 'Escape') {
            lightbox.remove();
            document.body.style.overflow = '';
            document.removeEventListener('keydown', handleKey);
        } else if (e.key === 'ArrowRight') {
            updateLightbox(currentIdx === 0 ? images.length - 1 : currentIdx - 1);
        } else if (e.key === 'ArrowLeft') {
            updateLightbox(currentIdx === images.length - 1 ? 0 : currentIdx + 1);
        }
    });
}

document.addEventListener('DOMContentLoaded', async function() {
    initStatsCounter();
    initScrollAnimations();
    initHeaderScroll();

    const pagePath = window.location.pathname.toLowerCase();
    let defaultFilter = 'all';
    if (pagePath.includes('farms')) defaultFilter = 'farm';
    else if (pagePath.includes('resthouses') || pagePath.includes('resthouse')) defaultFilter = 'resthouse';
    else if (pagePath.includes('lands') || pagePath.includes('land')) defaultFilter = 'land';

    await loadOfficeData();
    await loadOffers(defaultFilter);
    await handlePropertyQueryParam();
    renderBousla();
    loadNews();

    if (document.getElementById('faq-container') && typeof renderFAQ === 'function') {
        renderFAQ();
    }
    if (document.getElementById('mortgage-calculator-container') && typeof mortgageCalculator !== 'undefined') {
        mortgageCalculator.renderCalculator('mortgage-calculator-container');
    }
    if (document.getElementById('recommendations-container') && typeof propertyRecommender !== 'undefined') {
        propertyRecommender.renderRecommendationForm('recommendations-container');
    }
    if (document.getElementById('booking-container') && typeof bookingSystem !== 'undefined') {
        bookingSystem.renderBookingForm('booking-container');
    }

    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/')) {
        setTimeout(() => {
            showToast('مرحباً بك في مكتب آفاق الإنجاز العقاري! 👋');
        }, 1500);
    }

    const aiInput = document.getElementById('ai-input');
    if (aiInput) {
        aiInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') sendAIMessage();
        });
    }
});
