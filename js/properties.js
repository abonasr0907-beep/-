/* ============================================
   مكتب آفاق الإنجاز العقاري - ملف properties.js
   يقرأ data/properties.json ويعرض العقارات ديناميكياً
   ============================================ */

let DYNAMIC_PROPERTIES = [];

async function loadDynamicProperties() {
    try {
        const response = await fetch('data/properties.json', { cache: 'no-store' });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        DYNAMIC_PROPERTIES = Array.isArray(data.properties) ? data.properties : (Array.isArray(data) ? data : []);
    } catch (error) {
        console.error('تعذر تحميل data/properties.json:', error);
        DYNAMIC_PROPERTIES = [];
    }
    renderDynamicOffers();
}

function renderDynamicOffers(typeFilter = 'all', areaFilter = 'all') {
    const grid = document.getElementById('offers-grid');
    if (!grid) return;

    let items = DYNAMIC_PROPERTIES;

    if (typeFilter !== 'all') {
        const typeMap = {
            'farm': ['مزرعة', 'farm'],
            'resthouse': ['استراحة', 'resthouse'],
            'land': ['أرض', 'أرض سكنية', 'land']
        };
        const allowedTypes = typeMap[typeFilter] || [typeFilter];
        items = items.filter(p => allowedTypes.includes(p.type));
    }

    if (areaFilter !== 'all') {
        items = items.filter(p => p.location === areaFilter || p.area === areaFilter);
    }

    if (!items || items.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 40px;">
                <i class="fas fa-search" style="font-size: 50px; color: #C4A956; margin-bottom: 15px;"></i>
                <h3 style="color: #2A5050; margin-bottom: 10px;">لا توجد عروض مطابقة</h3>
                <p style="color: #555;">لم تجد ما تبحث عنه؟ <a href="inquiry.html" style="color: #C4A956; font-weight: 700;">قدم طلب استفسار</a></p>
            </div>
        `;
        return;
    }

    grid.innerHTML = items.map(prop => {
        const typeLabel = (prop.type === 'farms' || prop.type === 'مزرعة') ? 'مزرعة' : ((prop.type === 'resthouses' || prop.type === 'استراحة') ? 'استراحة' : 'أرض سكنية');
        const title = prop.title || `${typeLabel} مميزة في ${prop.location || prop.area || 'الخرج'}`;
        const areaName = prop.location || prop.area || 'الخرج';
        const size = prop.area || prop.size_sqm || prop.size || 'غير محدد';
        const price = prop.price ? `${Number(prop.price).toLocaleString('ar-SA')} ريال` : (prop.price_text || 'عند الاتصال');
        const features = prop.features || [];
        const featuresHtml = features.slice(0, 4).map(f => `<span class="offer-feature-tag">${f}</span>`).join('');
        const img = (prop.photos && prop.photos.length > 0)
            ? prop.photos[0]
            : ((prop.images && prop.images.length > 0 && prop.images[0] && !prop.images[0].startsWith('AgAC'))
                ? prop.images[0]
                : (typeLabel === 'مزرعة' ? 'images/cat-farms.jpg' : (typeLabel === 'استراحة' ? 'images/cat-rest.jpg' : 'images/cat-lands.jpg')));

        const whatsappNumber = typeof getWhatsappNumber === 'function' ? getWhatsappNumber() : '966545888931';
        const mapLink = prop.map_link || 'https://maps.app.goo.gl/SQhqCtgpeLNLb56w8?g_st=aw';

        return `
            <div class="offer-card">
                <div class="offer-card-img-wrapper">
                    <img src="${img}" alt="${title}" loading="lazy">
                    <span class="offer-badge">${typeLabel}</span>
                </div>
                <div class="offer-card-body">
                    <h3>${title}</h3>
                    <div class="offer-location">
                        <i class="fas fa-map-marker-alt"></i> ${areaName} - الخرج
                    </div>
                    <div class="offer-details">
                        <span><i class="fas fa-ruler-combined"></i> ${typeof size === 'number' ? size.toLocaleString('ar-SA') : size} م²</span>
                        <span><i class="fas fa-road"></i> ${prop.streets ? prop.streets + ' شوارع' : 'شارع واحد'}</span>
                    </div>
                    <div class="offer-price">${price}</div>
                    <div class="offer-features">${featuresHtml}</div>
                    ${prop.description ? `<p style="font-size: 13px; color: #555; margin-bottom: 12px; line-height: 1.5;">${prop.description}</p>` : ''}
                    <div class="offer-actions">
                        <a href="${mapLink}" target="_blank" class="offer-btn offer-btn-map">
                            <i class="fas fa-map-marked-alt"></i> الخريطة
                        </a>
                        <a href="https://wa.me/${whatsappNumber}?text=${encodeURIComponent('استفسار عن عقار: ' + title)}" target="_blank" class="offer-btn offer-btn-contact">
                            <i class="fas fa-comments"></i> استفسار
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

document.addEventListener('DOMContentLoaded', function() {
    loadDynamicProperties();
});
