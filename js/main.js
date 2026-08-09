/* ============================================
   مكتب آفاق الإنجاز العقاري - ملف JavaScript الرئيسي
   ============================================ */

// ===== بيانات المكتب والعروض =====
const OFFICE_DATA = {
    name: "مكتب آفاق الإنجاز العقاري",
    whatsapp: "966545888931",
    phone1: "966544699933",
    whatsapp2: "966561610748",
    email: "afaqalqary@gmail.com",
    snapchat: "https://www.snapchat.com/add/mmnf2278",
    tiktok: "https://www.tiktok.com/@whatyouarelookingforisw3",
    defaultMap: "https://maps.app.goo.gl/SQhqCtgpeLNLb56w8?g_st=aw",
    // telegramBot: مخفي عن العامة — للاستخدام الإداري فقط
};

// ===== إعدادات جسر تيليجرام (إرسال طلبات الزوار إلى البوت) =====
// يتم إرسال الطلب مباشرة إلى Telegram Bot API ليصلك إشعار فوري في البوت
const TELEGRAM_BRIDGE = {
    botToken: "8629398802:AAE2ndFy06GfV8qSQpd-cOKDccPUt_G05Os",
    adminChatId: "7746757675",
    apiBase: "https://api.telegram.org/bot",
    // رابط خادم البوت على Railway (اختياري — لتخزين الطلب في قائمة طلبات الزوار)
    // يُترك فارغاً إن لم يكن متوفراً؛ الإشعار يصل عبر Telegram Bot API مباشرة
    botApiUrl: "https://worker-production-7713.up.railway.app"
};

// ===== إرسال طلب الزائر إلى تيليجرام (إشعار فوري للمكتب) =====
// تعمل هذه الدالة بصمت في الخلفية ولا تؤثر على إرسال WhatsApp
async function notifyTelegramAdmin(requestData) {
    // الترتيب الجديد:
    // 1) إرسال الطلب إلى خادم البوت أولاً (تخزين + إشعار بالأزرار)
    // 2) إذا فشل خادم البوت: إرسال مباشر عبر Telegram Bot API (مع أزرار)

    // 1) محاولة إرسال إلى خادم البوت (يخزن + يشعر بالأزرار)
    const botApiOk = await sendToBotApi(requestData);
    if (botApiOk) {
        console.log('\u2705 تم إرسال الطلب إلى خادم البوت (تخزين + إشعار)');
        return true;
    }

    // 2) الاحتياط: إرسال مباشر عبر Telegram Bot API مع أزرار
    console.warn('\u26a0\ufe0f خادم البوت غير متوفر \u2014 إرسال مباشر عبر Telegram API');
    try {
        let html = '<b>\U0001F514 طلب عرض عقار جديد من الموقع</b>\n\n';
        html += `<b>\U0001F464 اسم العميل:</b> ${escapeHtml(requestData.name || 'غير محدد')}\n`;
        html += `<b>\U0001F4F1 رقم الهاتف:</b> ${escapeHtml(requestData.phone || 'غير محدد')}\n`;
        html += `<b>\U0001F3F7\ufe0f نوع العقار:</b> ${escapeHtml(requestData.propertyType || 'غير محدد')}\n`;
        html += `<b>\U0001F4CD الموقع:</b> ${escapeHtml(requestData.location || 'غير محدد')}\n`;
        html += `<b>\U0001F4D0 المساحة:</b> ${escapeHtml(requestData.area || 'غير محدد')} م\u00b2\n`;
        html += `<b>\U0001F4B0 السعر التقريبي:</b> ${escapeHtml(requestData.price || 'غير محدد')} ريال\n`;

        if (requestData.description && requestData.description.trim()) {
            html += `\n<b>\u2139\ufe0f الوصف:</b>\n${escapeHtml(requestData.description)}\n`;
        }

        if (requestData.latitude && requestData.longitude) {
            html += `\n<b>\U0001F5FA\ufe0f موقع العقار على الخريطة:</b>\n`;
            html += `<b>خط العرض (Latitude):</b> ${requestData.latitude}\n`;
            html += `<b>خط الطول (Longitude):</b> ${requestData.longitude}\n`;
            html += `<b>\U0001F517 رابط Google Maps:</b> ${requestData.mapsLink || 'https://www.google.com/maps?q=' + requestData.latitude + ',' + requestData.longitude}\n`;
        }

        html += `\n<b>\U0001F4F8 الصور:</b> ${requestData.imageCount || 0} صورة`;
        if ((requestData.imageCount || 0) > 0) {
            html += ' (ي\u064fرفقها العميل عبر WhatsApp)';
        }
        html += '\n';

        html += `\n<b>\U0001F4C4 رقم الطلب:</b> <code>${requestData.id}</code>\n`;
        html += `<b>\U0001F550 التاريخ:</b> ${new Date().toLocaleString('ar-SA')}\n`;
        html += `\n<b>\U0001F4A1 مكتب آفاق الإنجاز العقاري</b>\n\U0001F310 abonasr0907-beep.github.io/-`;

        const url = TELEGRAM_BRIDGE.apiBase + TELEGRAM_BRIDGE.botToken + "/sendMessage";
        const body = new URLSearchParams();
        body.append('chat_id', TELEGRAM_BRIDGE.adminChatId);
        body.append('text', html);
        body.append('parse_mode', 'HTML');
        body.append('disable_web_page_preview', 'true');

        // إضافة أزرار الموافقة والرفض مباشرة مع الرسالة
        const reqId = requestData.id || '';
        const replyMarkup = {
            inline_keyboard: [
                [{ text: "\u2705 \u0645\u0648\u0627\u0641\u0642\u0629 \u0648\u0646\u0634\u0631", callback_data: "vreq_approve_" + reqId }],
                [{ text: "\u274C \u0631\u0641\u0636", callback_data: "vreq_reject_" + reqId }]
            ]
        };
        body.append('reply_markup', JSON.stringify(replyMarkup));

        const response = await fetch(url, {
            method: 'POST',
            body: body,
        });

        if (response.ok) {
            console.log('\u2705 تم إرسال إشعار تيليجرام مباشر (احتياطي)');
            return true;
        } else {
            console.warn('\u26a0\ufe0f فشل إرسال إشعار تيليجرام:', response.status);
            return false;
        }
    } catch (err) {
        console.warn('\u26a0\ufe0f خطأ في إرسال تيليجرام:', err.message);
        return false;
    }
}

// ===== إرسال الطلب إلى خادم البوت على Railway (اختياري) =====
// يخزن الطلب في visitor_requests.json ليظهر في زر "طلبات الزوار"
async function sendToBotApi(requestData) {
    if (!TELEGRAM_BRIDGE.botApiUrl) return false; // غير مُكوّن — تخطي بصمت
    try {
        const apiUrl = TELEGRAM_BRIDGE.botApiUrl.replace(/\/+$/, '') + '/api/visitor-request';
        const response = await fetch(apiUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData),
        });
        if (response.ok) {
            console.log('✅ تم تخزين الطلب في خادم البوت');
            return true;
        }
        console.warn('⚠️ خادم البوت لم يستجب:', response.status);
        return false;
    } catch (err) {
        console.warn('⚠️ تعذر الوصول لخادم البوت (طبيعي إن لم يكن مُكوّناً):', err.message);
        return false;
    }
}

// ===== رفع صور طلب الزائر إلى خادم البوت =====
// ترسل الصور فعلياً عبر FormData إلى /api/visitor-images
async function uploadVisitorImages(requestId, images) {
    if (!TELEGRAM_BRIDGE.botApiUrl) return false;
    try {
        const apiUrl = TELEGRAM_BRIDGE.botApiUrl.replace(/\/+$/, '') + '/api/visitor-images';
        const fd = new FormData();
        fd.append('requestId', requestId);
        images.forEach((file, idx) => {
            fd.append('images', file, `img_${idx}_${file.name || 'photo.jpg'}`);
        });
        const response = await fetch(apiUrl, { method: 'POST', body: fd });
        if (response.ok) {
            console.log('✅ تم رفع صور طلب الزائر إلى البوت');
            return true;
        }
        console.warn('⚠️ خادم البوت لم يقبل رفع الصور:', response.status);
        return false;
    } catch (err) {
        console.warn('⚠️ تعذر رفع الصور للبوت:', err.message);
        return false;
    }
}

// ===== دالة مساعدة لتأمين النص HTML =====
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = String(text);
    return div.innerHTML;
}

// ===== أسعار البوصلة العقارية حسب المنطقة =====
const BOUSLA_PRICES = {
    "الرحمانية": { land: "850 ريال/م²", farm: "120 ريال/م²", resthouse: "350K - 1.2M ريال" },
    "الهياثم": { land: "1,100 ريال/م²", farm: "150 ريال/م²", resthouse: "400K - 1.5M ريال" },
    "الدلم": { land: "600 ريال/م²", farm: "90 ريال/م²", resthouse: "250K - 900K ريال" },
    "الضبيعة": { land: "700 ريال/م²", farm: "100 ريال/م²", resthouse: "280K - 1M ريال" },
    "العفجة": { land: "650 ريال/م²", farm: "95 ريال/م²", resthouse: "260K - 950K ريال" }
};

// ===== العروض =====
let OFFERS = [];

// ===== تحميل العروض من ملف JSON أو من localStorage =====
async function loadOffers(defaultFilter = 'all') {
    // محاولة تحميل العروض من localStorage (من بوت التلجرام)
    const storedOffers = localStorage.getItem('afaq_offers');
    if (storedOffers) {
        try {
            OFFERS = JSON.parse(storedOffers);
        } catch(e) {
            OFFERS = getDefaultOffers();
        }
    } else {
        // تحميل من ملف JSON
        try {
            const response = await fetch('offers-data/offers.json');
            const data = await response.json();
            OFFERS = data.offers;
            localStorage.setItem('afaq_offers', JSON.stringify(OFFERS));
        } catch(e) {
            OFFERS = getDefaultOffers();
        }
    }
    renderOffers(defaultFilter);
    updateStats();
}

// ===== العروض الافتراضية =====
function getDefaultOffers() {
    return [
        { id: "FRM-001", type: "farm", category: "مزرعة", title: "مزرعة زراعية كاملة بمخطط الرحمانية", area: "الرحمانية", size_sqm: 10000, price_text: "1,200,000 ريال", description: "مزرعة زراعية خصبة بمخطط الرحمانية بمساحة 10,000 م²، محاطة بأشجار النخيل، تشمل بئر مياه عام وشبكة ري بالتنقيط.", features: ["بئر مياء عام", "شبكة ري بالتنقيط", "أشجار نخيل", "على شارعين"], images: ["images/farms-bg.jpg"], map_link: OFFICE_DATA.defaultMap, featured: true },
        { id: "RST-001", type: "resthouse", category: "استراحة", title: "استراحة فاخرة بمخطط الرحمانية", area: "الرحمانية", size_sqm: 600, price_text: "850,000 ريال", description: "استراحة فاخرة بمخطط الرحمانية بمساحة 600 م²، تشمل مسبح خاص، حديقة منسقة، صالة كبيرة، غرف نوم.", features: ["مسبح خاص", "حديقة منسقة", "تشطيب فاخر"], images: ["images/resthouse-bg.jpg"], map_link: OFFICE_DATA.defaultMap, featured: true },
        { id: "LND-001", type: "land", category: "أرض سكنية", title: "أرض سكنية بمخطط الرحمانية", area: "الرحمانية", size_sqm: 500, price_text: "425,000 ريال", description: "أرض سكنية بمخطط الرحمانية بمساحة 500 م²، على شارعين، قرب من الخدمات، صك إلكتروني.", features: ["على شارعين", "صك إلكتروني", "جاهزة للبناء"], images: ["images/land-bg.jpg"], map_link: OFFICE_DATA.defaultMap, featured: true }
    ];
}

// ===== عرض العروض =====
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
        const bousla = BOUSLA_PRICES[offer.area] || BOUSLA_PRICES["الرحمانية"];
        const bouslaPrice = offer.type === 'farm' ? bousla.farm : (offer.type === 'resthouse' ? bousla.resthouse : bousla.land);
        const featuresHtml = (offer.features || []).slice(0, 4).map(f => `<span class="offer-feature-tag">${f}</span>`).join('');
        const featuredBadge = offer.featured ? '<span class="offer-badge featured">مميز ⭐</span>' : `<span class="offer-badge">${offer.category}</span>`;
        const img = offer.images && offer.images[0] ? offer.images[0] : 'images/farms-bg.jpg';
        const mapLink = offer.map_link || OFFICE_DATA.defaultMap;
        const imgCount = (offer.images && offer.images.length) ? offer.images.length : 0;
        const morePhotosBadge = imgCount > 1 ? `<span class="offer-photos-count"><i class="fas fa-images"></i> ${imgCount} صور</span>` : '';

        return `
            <div class="offer-card" data-offer-id="${offer.id}">
                <img src="${img}" alt="${offer.title}" class="offer-card-img" loading="lazy" decoding="async" onerror="this.onerror=null; this.src='images/farms-bg.jpg';">
                ${featuredBadge}
                ${morePhotosBadge}
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
                    ${(offer.priceType === 'auction' || offer.price_type === 'auction') ? `<div class="offer-auction-info"><i class="fas fa-gavel"></i> على السوم — أعلى سوم: <strong>${(offer.highestBid || offer.highest_bid || 0).toLocaleString('en-US')} ريال</strong></div>` : ''}
                    ${(offer.priceType === 'negotiable' || offer.price_type === 'negotiable') ? `<div class="offer-price-tag"><i class="fas fa-handshake"></i> قابل للتفاوض</div>` : ''}
                    ${(offer.priceType === 'auction' || offer.price_type === 'auction') ? `<button class="offer-btn offer-btn-bid" onclick="submitBid('${offer.id}'); return false;"><i class="fas fa-gavel"></i> طلب مزايدة</button>` : ''}
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
                            <i class="fas fa-map-marked-alt"></i> الموقع على الخريطة
                        </a>
                        <a href="https://wa.me/${OFFICE_DATA.whatsapp}?text=استفسار عن ${encodeURIComponent(offer.title)}" target="_blank" class="offer-btn offer-btn-contact">
                            <i class="fas fa-comments"></i> استفسار
                        </a>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

// ===== الفلاتر =====
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

// ===== تحديث الإحصائيات =====
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

// ===== عرض البوصلة العقارية =====
function renderBousla() {
    const grid = document.getElementById('bousla-grid');
    if (!grid) return;

    grid.innerHTML = Object.entries(BOUSLA_PRICES).map(([area, prices]) => `
        <div class="bousla-card">
            <h3><i class="fas fa-map-marker-alt"></i> ${area}</h3>
            <div class="price-row"><span>الأراضي السكنية</span><span>${prices.land}</span></div>
            <div class="price-row"><span>المزارع</span><span>${prices.farm}</span></div>
            <div class="price-row"><span>الاستراحات</span><span>${prices.resthouse}</span></div>
        </div>
    `).join('');
}

// ===== النشرة الأخبارية (من الهيئة العامة للعقار) =====
async function loadNews() {
    const grid = document.getElementById('news-grid');
    if (!grid) return;

    // أخبار افتراضية (يتم تحديثها من بوت التلجرام أو من scraping)
    const defaultNews = [
        { date: "2025-08-05", title: "الهيئة العامة للعقار تستعرض التجربة السعودية في منتدى قطر العقاري 2025", desc: "شاركت الهيئة العامة للعقار في منتدى قطر العقاري 2025 لاستعراض التجربة السعودية المتميزة في تطوير القطاع العقاري.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" },
        { date: "2025-08-04", title: "تحديث مؤشرات الأسعار العقارية في مناطق المملكة", desc: "أعلنت الهيئة العامة للعقار عن تحديث المؤشرات العقارية لشهر أغسطس، مع تباين في الأسعار بين المناطق.", link: "https://rei.rega.gov.sa", source: "منصة المؤشرات العقارية" },
        { date: "2025-08-03", title: "نظام إيجار الجديد: تسهيلات إضافية للمستفيدين", desc: "أطلقت الهيئة العامة للعقار تحديثات جديدة على نظام إيجار لتسهيل المعاملات العقارية.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" },
        { date: "2025-08-02", title: "الخرج تشهد نمواً في الطلب على الأراضي الزراعية", desc: "سجلت محافظة الخرج نمواً ملحوظاً في الطلب على الأراضي الزراعية والمزارع خلال الربع الحالي.", link: "#", source: "تقارير سوقية" },
        { date: "2025-08-01", title: "بوابة العقار الجيومكانية: خدمة جديدة لعرض البيانات العقارية", desc: "أطلقت الهيئة العامة للعقار بوابة العقار الجيومكانية لعرض البيانات العقارية المكانية عبر خرائط دقيقة.", link: "https://rega.gov.sa", source: "الهيئة العامة للعقار" }
    ];

    // محاولة تحميل الأخبار من ملف news.json (محدث آلياً كل 3 أيام)
    try {
        const resp = await fetch('offers-data/news.json?_=' + Date.now());
        if (resp.ok) {
            const data = await resp.json();
            if (data && Array.isArray(data.news) && data.news.length > 0) {
                news = data.news;
            }
        }
    } catch(e) {
        console.log('تعذر تحميل news.json، استخدام الأخبار الافتراضية');
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

// ===== المساعد الذكي =====
const AI_KNOWLEDGE = {
    greeting: "أهلاً وسهلاً بك في مكتب آفاق الإنجاز العقاري! 👋 أنا مساعدك الذكي. لدي 20 سنة خبرة في السوق العقاري بالخرج والرياض. كيف يمكنني مساعدتك اليوم؟ يمكنك سؤالي عن المزارع، الاستراحات، الأراضي السكنية، أو خدماتنا.",

    farms: "🌿 لدينا مجموعة مميزة من المزارع في مخطط الرحمانية والهياثم والدلم والضبيعة والعفجة. أسعار المزارع تبدأ من 90 ريال/م² في الدلم وتصل إلى 150 ريال/م² في الهياثم. هل تريد تصفح عروض المزارع؟ <a href='farms.html'>اضغط هنا لعرض المزارع</a>",

    resthouses: "🏡 لدينا استراحات فاخرة في مختلف مناطق الخرج. الأسعار تتراوح بين 250,000 و1,500,000 ريال حسب الموقع والمساحة. <a href='resthouses.html'>اضغط هنا لعرض الاستراحات</a>",

    lands: "📍 لدينا أراضٍ سكنية في مخطط الرحمانية والهياثم والدلم والعفجة. متوسط السعر يتراوح بين 600 و1,100 ريال/م². <a href='lands.html'>اضغط هنا لعرض الأراضي السكنية</a>",

    services: "🔧 نقدم خدمات ما بعد البيع الشاملة: استخراج رخص البناء، المقاولات، التشطيب، إدارة الأملاك، حفر الآبار وتحديد مواقعها وتصويرها. <a href='services.html'>اضغط هنا لعرض الخدمات</a>",

    sell: "📈 هل تريد عرض عقارك في موقعنا؟ رائع! يمكنك تعبئة استبيان العرض عبر <a href='list-property.html'>هذه الصفحة</a> وسنتواصل معك في أقرب وقت.",

    inquiry: "🔍 لم تجد ما تبحث عنه؟ لا بأس! يمكنك تقديم طلب استفسار عبر <a href='inquiry.html'>هذه الصفحة</a> وسنقوم بمراجعته والتواصل معك.",

    contact: "📞 يمكنك التواصل معنا عبر:\n• واتساب: 0545888931\n• مكالمات: 0544699933\n• واتساب ومكالمات: 0561610748\n• البريد: afaqalqary@gmail.com",

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

    if (lower.includes('مزرعة') || lower.includes('مزارع') || lower.includes('زراعية') || lower.includes('زراع'))
        return AI_KNOWLEDGE.farms;
    if (lower.includes('استراحة') || lower.includes('استراحات') || lower.includes('استراح'))
        return AI_KNOWLEDGE.resthouses;
    if (lower.includes('أرض') || lower.includes('ارض') || lower.includes('اراضي') || lower.includes('أراضي'))
        return AI_KNOWLEDGE.lands;
    if (lower.includes('خدمة') || lower.includes('خدمات') || lower.includes('رخصة') || lower.includes('مقاولات') || lower.includes('تشطيب') || lower.includes('إدارة') || lower.includes('آبار') || lower.includes('حفر'))
        return AI_KNOWLEDGE.services;
    if (lower.includes('عرض') || lower.includes('بيع') || lower.includes('عقاري'))
        return AI_KNOWLEDGE.sell;
    if (lower.includes('استفسار') || lower.includes('طلب') || lower.includes('بحث') || lower.includes('وجدت'))
        return AI_KNOWLEDGE.inquiry;
    if (lower.includes('تواصل') || lower.includes('واتساب') || lower.includes('جوال') || lower.includes('هاتف') || lower.includes('رقم') || lower.includes('ايميل') || lower.includes('بريد'))
        return AI_KNOWLEDGE.contact;
    if (lower.includes('منطقة') || lower.includes('مناطق') || lower.includes('مكان') || lower.includes('الرحمانية') || lower.includes('الهياثم') || lower.includes('الدلم') || lower.includes('الضبيعة') || lower.includes('العفجة'))
        return AI_KNOWLEDGE.areas;
    if (lower.includes('بوصلة') || lower.includes('اسعار') || lower.includes('أسعار') || lower.includes('مؤشر'))
        return AI_KNOWLEDGE.bousla;
    if (lower.includes('خبرة') || lower.includes('سنة') || lower.includes('تاريخ'))
        return AI_KNOWLEDGE.experience;
    if (lower.includes('خريطة') || lower.includes('موقع') || lower.includes('maps'))
        return AI_KNOWLEDGE.maps;
    if (lower.includes('سلام') || lower.includes('مرحبا') || lower.includes('اهلا') || lower.includes('هاي'))
        return AI_KNOWLEDGE.greeting;

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

// ===== نماذج العرض والاستفسار =====
// ===== متغيرات الخريطة والصور =====
let propertyMap = null;
let mapMarker = null;
let selectedImages = [];
const MAX_IMAGES = 5;

// ===== تبديل حقول السعر حسب النوع (محدد/قابل للتفاوض/على السوم) =====
function togglePriceFields() {
    const sel = document.getElementById('price-type-select');
    if (!sel) return;
    const type = sel.value;
    const auctionRow = document.getElementById('auction-row');
    const priceInput = document.getElementById('price-input');
    const priceLabel = priceInput ? priceInput.closest('.form-group').querySelector('label') : null;

    if (type === 'auction') {
        if (auctionRow) auctionRow.style.display = '';
        if (priceLabel) priceLabel.innerHTML = '<i class="fas fa-gavel"></i> سعر البدء / الحد الأدنى للمزاد (ريال) *';
        if (priceInput) priceInput.placeholder = 'السعر الذي يبدأ به المزاد';
    } else {
        if (auctionRow) auctionRow.style.display = 'none';
        const hb = document.getElementById('highest-bid-input');
        if (hb) hb.value = '';
        if (priceLabel) {
            if (type === 'negotiable') {
                priceLabel.innerHTML = '<i class="fas fa-money-bill-wave"></i> السعر المطلوب (قابل للتفاوض) (ريال) *';
            } else {
                priceLabel.innerHTML = '<i class="fas fa-tag"></i> السعر المحدد (ريال) *';
            }
        }
        if (priceInput) priceInput.placeholder = 'المبلغ المطلوب';
    }
}

// ===== تهيئة الخريطة التفاعلية =====
function initPropertyMap() {
    const mapEl = document.getElementById('property-map');
    if (!mapEl || typeof L === 'undefined') return;

    // موقع افتراضي: الخرج، الرياض
    const defaultLat = 24.1554;
    const defaultLng = 47.3068;

    propertyMap = L.map('property-map', { zoomControl: true, attributionControl: true }).setView([defaultLat, defaultLng], 11);

    // طبقة الخريطة العادية
    const standardLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap',
        maxZoom: 19
    });

    // طبقة الأقمار الصناعية (Esri World Imagery)
    const satelliteLayer = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: '&copy; Esri, Maxar, Earthstar Geographics',
        maxZoom: 19
    });

    // طبقة تسميات الأماكن فوق الأقمار الصناعية
    const labelsLayer = L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager_only_labels/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; CARTO',
        maxZoom: 19,
        pane: 'shadowPane'
    });

    // الطبقة الافتراضية
    standardLayer.addTo(propertyMap);
    let isSatellite = false;
    window.__afaqSatLabels = labelsLayer;

    // زر تبديل الأقمار الصناعية
    L.control({ position: 'topright' }).addTo(propertyMap);
    const satelliteBtn = L.DomUtil.create('div', 'afaq-sat-toggle');
    satelliteBtn.innerHTML = '🛰️ أقمار صناعية';
    satelliteBtn.style.cssText = 'background:#2A5050;color:#fff;padding:6px 12px;border-radius:6px;cursor:pointer;font-size:13px;font-family:inherit;box-shadow:0 2px 6px rgba(0,0,0,0.3);z-index:1000;';
    const ctrl = L.control({ position: 'topright' });
    ctrl.onAdd = function() {
        const div = L.DomUtil.create('div');
        div.appendChild(satelliteBtn);
        L.DomEvent.disableClickPropagation(div);
        return div;
    };
    ctrl.addTo(propertyMap);

    satelliteBtn.addEventListener('click', function() {
        if (!isSatellite) {
            propertyMap.removeLayer(standardLayer);
            satelliteLayer.addTo(propertyMap);
            labelsLayer.addTo(propertyMap);
            satelliteBtn.innerHTML = '🗺️ خريطة عادية';
            isSatellite = true;
        } else {
            propertyMap.removeLayer(satelliteLayer);
            propertyMap.removeLayer(labelsLayer);
            standardLayer.addTo(propertyMap);
            satelliteBtn.innerHTML = '🛰️ أقمار صناعية';
            isSatellite = false;
        }
    });

    // النقر على الخريطة لتحديد موقع العقار
    propertyMap.on('click', function(e) {
        setMapLocation(e.latlng.lat, e.latlng.lng);
    });

    // الضغط المطول لنسخ رابط Google Maps
    let pressTimer = null;
    propertyMap.on('mousedown', function(e) {
        pressTimer = setTimeout(function() {
            const lat = e.latlng.lat.toFixed(6);
            const lng = e.latlng.lng.toFixed(6);
            const mapsUrl = 'https://www.google.com/maps?q=' + lat + ',' + lng;
            // نسخ الرابط
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(mapsUrl).then(function() {
                    showToast('تم نسخ رابط Google Maps: ' + mapsUrl, 'success');
                }).catch(function() {
                    showToast('رابط الموقع: ' + mapsUrl, '');
                });
            } else {
                showToast('رابط الموقع: ' + mapsUrl, '');
            }
        }, 800);
    });
    propertyMap.on('mouseup', function() { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
    propertyMap.on('dragstart', function() { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
    propertyMap.on('zoomstart', function() { if (pressTimer) { clearTimeout(pressTimer); pressTimer = null; } });
}

// ===== تحديد الموقع على الخريطة =====
function setMapLocation(lat, lng) {
    if (!propertyMap) return;

    // إزالة العلامة السابقة
    if (mapMarker) {
        propertyMap.removeLayer(mapMarker);
    }

    // إضافة علامة جديدة
    mapMarker = L.marker([lat, lng], {draggable: true}).addTo(propertyMap);

    // السماح بسحب العلامة
    mapMarker.on('dragend', function(e) {
        const pos = e.target.getLatLng();
        setMapLocation(pos.lat, pos.lng);
    });

    // تحديث الحقول المخفية
    document.getElementById('lat-input').value = lat.toFixed(6);
    document.getElementById('lng-input').value = lng.toFixed(6);

    // إنشاء رابط خرائط Google
    const mapsLink = `https://www.google.com/maps?q=${lat.toFixed(6)},${lng.toFixed(6)}`;
    document.getElementById('maps-link-input').value = mapsLink;

    // عرض الإحداثيات
    const display = document.getElementById('map-coords-display');
    const coordsText = document.getElementById('coords-text');
    const mapsLinkEl = document.getElementById('maps-link');
    if (display) display.style.display = 'flex';
    if (coordsText) coordsText.textContent = `خط العرض: ${lat.toFixed(6)} | خط الطول: ${lng.toFixed(6)}`;
    if (mapsLinkEl) mapsLinkEl.href = mapsLink;
}

// ===== استخدام GPS لتحديد موقع المستخدم =====
function useMyGPS() {
    if (!navigator.geolocation) {
        showToast('المتصفح لا يدعم تحديد الموقع الجغرافي', 'error');
        return;
    }

    showToast('جاري تحديد موقعك...', '');

    navigator.geolocation.getCurrentPosition(
        function(position) {
            const lat = position.coords.latitude;
            const lng = position.coords.longitude;

            if (!propertyMap) initPropertyMap();

            setMapLocation(lat, lng);
            propertyMap.setView([lat, lng], 15);
            showToast('تم تحديد موقعك بنجاح', 'success');
        },
        function(error) {
            let errMsg = 'تعذر تحديد موقعك';
            if (error.code === 1) errMsg = 'تم رفض إذن الوصول للموقع';
            else if (error.code === 2) errMsg = 'الموقع غير متاح حالياً';
            else if (error.code === 3) errMsg = 'انتهت مهلة تحديد الموقع';
            showToast(errMsg, 'error');
        },
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
    );
}

// ===== مسح تحديد الموقع =====
function clearMapLocation() {
    if (mapMarker && propertyMap) {
        propertyMap.removeLayer(mapMarker);
        mapMarker = null;
    }
    document.getElementById('lat-input').value = '';
    document.getElementById('lng-input').value = '';
    document.getElementById('maps-link-input').value = '';
    const display = document.getElementById('map-coords-display');
    if (display) display.style.display = 'none';
    showToast('تم مسح تحديد الموقع', '');
}

// ===== معالجة اختيار الصور =====
function handleImageSelection(event) {
    const files = Array.from(event.target.files);

    for (const file of files) {
        if (selectedImages.length >= MAX_IMAGES) {
            showToast(`الحد الأقصى ${MAX_IMAGES} صور`, 'error');
            break;
        }

        if (!file.type.startsWith('image/')) {
            showToast('يرجى اختيار ملفات صور فقط', 'error');
            continue;
        }

        if (file.size > 10 * 1024 * 1024) {
            showToast(`الصورة "${file.name}" كبيرة جداً (الحد 10 ميجابايت)`, 'error');
            continue;
        }

        selectedImages.push(file);
    }

    renderImagePreviews();
    event.target.value = ''; // إعادة تعيين للسماح بإعادة اختيار نفس الصورة
}

// ===== عرض معاينة الصور =====
function renderImagePreviews() {
    const grid = document.getElementById('image-preview-grid');
    if (!grid) return;

    grid.innerHTML = '';

    selectedImages.forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'image-preview-item';

        const img = document.createElement('img');
        img.src = URL.createObjectURL(file);
        img.alt = `صورة ${idx + 1}`;

        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-img';
        removeBtn.innerHTML = '<i class="fas fa-times"></i>';
        removeBtn.type = 'button';
        removeBtn.onclick = function(e) {
            e.preventDefault();
            selectedImages.splice(idx, 1);
            renderImagePreviews();
        };

        const number = document.createElement('span');
        number.className = 'img-number';
        number.textContent = idx + 1;

        item.appendChild(img);
        item.appendChild(removeBtn);
        item.appendChild(number);
        grid.appendChild(item);
    });
}

// ===== إرسال نموذج عرض العقار =====
function submitPropertyForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

    // التحقق من الحقول المطلوبة
    if (!data.name || !data.phone || !data.location || !data.propertyType || !data.area || !data.price) {
        showToast('يرجى تعبئة جميع الحقول المطلوبة', 'error');
        return false;
    }
    if (!data.priceType) {
        showToast('يرجى اختيار نوع السعر', 'error');
        return false;
    }
    // التحقق من أعلى سوم عند اختيار "على السوم"
    if (data.priceType === 'auction') {
        const hb = document.getElementById('highest-bid-input');
        if (hb && (!hb.value || hb.value === '')) {
            showToast('يرجى إدخال أعلى سوم حالي', 'error');
            hb.focus();
            return false;
        }
        const hbVal = parseFloat(hb.value);
        if (isNaN(hbVal) || hbVal < 0 || hbVal > 50000000) {
            showToast('أعلى سوم يجب أن يكون بين 0 و 50,000,000 ريال', 'error');
            hb.focus();
            return false;
        }
        data.highestBid = hbVal;
    }

    // حفظ الطلب في localStorage (للاستمرارية)
    const requests = JSON.parse(localStorage.getItem('afaq_property_requests') || '[]');
    data.id = 'REQ-' + Date.now();
    data.date = new Date().toISOString();
    data.status = 'pending';
    data.imageCount = selectedImages.length;
    if (data.latitude && data.longitude) {
        data.hasLocation = true;
        data.mapsLink = data.mapsLink || '';
    }
    requests.push(data);
    localStorage.setItem('afaq_property_requests', JSON.stringify(requests));

    // تسمية نوع السعر بالعربية للعرض
    const priceTypeLabels = { fixed: 'سعر محدد', negotiable: 'قابل للتفاوض', auction: 'على السوم' };
    const priceTypeLabel = priceTypeLabels[data.priceType] || 'سعر محدد';

    // بناء رسالة واتساب الاحترافية
    let msg = `*\u{1F3E0} طلب عرض عقار جديد*\n\n`;
    msg += `*\u{1F464} الاسم:* ${data.name}\n`;
    msg += `*\u{1F4DE} الجوال:* ${data.phone}\n`;
    msg += `*\u{1F3F7}\u{FE0F} نوع العقار:* ${data.propertyType || 'غير محدد'}\n`;
    msg += `*\u{1F4CD} الموقع:* ${data.location || 'غير محدد'}\n`;
    msg += `*\u{1F4D0} المساحة:* ${data.area || 'غير محدد'} م\u{00B2}\n`;
    msg += `*\u{1F4B0} السعر:* ${data.price || 'غير محدد'} ريال (${priceTypeLabel})\n`;
    if (data.priceType === 'auction' && data.highestBid) {
        msg += `*\u{1FA99} أعلى سوم حالي:* ${data.highestBid} ريال\n`;
    }

    // إضافة الوصف إن وجد
    if (data.description && data.description.trim()) {
        msg += `*\u{2139}\u{FE0F} الوصف:* ${data.description}\n`;
    }

    // إضافة الموقع الجغرافي إن تم تحديده
    if (data.latitude && data.longitude) {
        msg += `\n*\u{1F5FA}\u{FE0F} موقع العقار على الخريطة:*\n`;
        msg += `*خط العرض:* ${parseFloat(data.latitude).toFixed(6)}\n`;
        msg += `*خط الطول:* ${parseFloat(data.longitude).toFixed(6)}\n`;
        msg += `*رابط خرائط Google:* ${data.mapsLink}\n`;
    }

    // إضافة عدد الصور
    if (selectedImages.length > 0) {
        msg += `\n*\u{1F4F8} عدد الصور المرفقة:* ${selectedImages.length}\n`;
        msg += `_ملاحظة: يرجى إرفاق الصور يدوياً في واتساب بعد فتح المحادثة_\n`;
    }

    msg += `\n*\u{1F4C4} رقم الطلب:* ${data.id}\n`;
    msg += `*\u{1F550} التاريخ:* ${new Date().toLocaleString('ar-SA')}\n`;
    msg += `\n*\u{1F4A1} مكتب آفاق الإنجاز العقاري*\n`;
    msg += `\u{1F310} abonasr0907-beep.github.io/-`;

    // فتح واتساب بالرسالة
    const whatsappUrl = `https://wa.me/${OFFICE_DATA.whatsapp}?text=${encodeURIComponent(msg)}`;
    window.open(whatsappUrl, '_blank');

    // ── إرسال نسخة إلى بوت تيليجرام (إشعار فوري للمكتب) ──
    // يتم الإرسال بصمت في الخلفية ولا يؤثر على WhatsApp
    notifyTelegramAdmin({
        id: data.id,
        name: data.name,
        phone: data.phone,
        propertyType: data.propertyType,
        location: data.location,
        area: data.area,
        price: data.price,
        priceType: data.priceType,
        highestBid: data.highestBid || '',
        description: data.description,
        latitude: data.latitude,
        longitude: data.longitude,
        mapsLink: data.mapsLink,
        imageCount: selectedImages.length,
    }).catch(() => {}); // تجاهل الأخطاء بصمت

    // ── رفع الصور فعلياً إلى خادم البوت (اختياري — بصمت) ──
    if (selectedImages.length > 0) {
        uploadVisitorImages(data.id, selectedImages).catch(() => {});
    }

    // عرض رسالة النجاح
    const fs = document.getElementById('form-success');
    if (fs) fs.classList.add('show');
    event.target.reset();

    // مسح الصور والخريطة
    selectedImages = [];
    renderImagePreviews();
    clearMapLocation();

    showToast('تم إرسال طلبك بنجاح! سنتواصل معك قريباً', 'success');

    setTimeout(() => {
        const fsR = document.getElementById('form-success');
        if (fsR) fsR.classList.remove('show');
    }, 5000);

    return false;
}

function submitInquiryForm(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const data = Object.fromEntries(formData);

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

    window.open(`https://wa.me/${OFFICE_DATA.whatsapp}?text=${encodeURIComponent(msg)}`, '_blank');

    // ── إرسال نسخة استفسار إلى بوت تيليجرام ──
    notifyTelegramAdmin({
        id: data.id,
        name: data.name,
        phone: data.phone,
        propertyType: data.propertyType || data.property_type || '',
        location: data.location || data.area || '',
        area: data.area || data.size || '',
        price: data.budget || '',
        description: data.details || '',
    }).catch(() => {});

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

// ===== طلب مزايدة على عرض (يصل للإدارة) =====
function submitBid(offerId) {
    const offer = OFFERS.find(o => String(o.id) === String(offerId));
    if (!offer) return;
    const currentBid = offer.highestBid || offer.highest_bid || offer.price || 0;

    // بناء نموذج مزايدة بسيط
    const bidHtml = `
        <div id="bid-modal" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.6);z-index:99998;display:flex;align-items:center;justify-content:center;">
            <div style="background:#fff;border-radius:12px;padding:28px;max-width:420px;width:90%;box-shadow:0 10px 40px rgba(0,0,0,0.3);font-family:inherit;">
                <h3 style="color:#2A5050;margin:0 0 8px;"><i class="fas fa-gavel"></i> طلب مزايدة</h3>
                <p style="color:#666;font-size:14px;margin:0 0 16px;">${offer.title}</p>
                <p style="background:#f5f5f5;padding:10px;border-radius:8px;font-size:14px;margin:0 0 16px;">أعلى سوم حالي: <strong>${Number(currentBid).toLocaleString('en-US')} ريال</strong></p>
                <label style="display:block;font-size:14px;color:#333;margin-bottom:6px;">مبلغ المزايدة (ريال) *</label>
                <input type="number" id="bid-amount" placeholder="أدخل مبلغ المزايدة" min="${currentBid}" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;margin-bottom:12px;font-family:inherit;" />
                <label style="display:block;font-size:14px;color:#333;margin-bottom:6px;">الاسم *</label>
                <input type="text" id="bid-name" placeholder="اسمك الكامل" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;margin-bottom:12px;font-family:inherit;" />
                <label style="display:block;font-size:14px;color:#333;margin-bottom:6px;">رقم الجوال *</label>
                <input type="text" id="bid-phone" placeholder="05xxxxxxxx" style="width:100%;padding:10px;border:1px solid #ccc;border-radius:8px;margin-bottom:18px;font-family:inherit;" />
                <div style="display:flex;gap:10px;">
                    <button onclick="closeBidModal()" style="flex:1;padding:10px;border:1px solid #ccc;border-radius:8px;background:#fff;cursor:pointer;font-family:inherit;">إلغاء</button>
                    <button onclick="sendBid('${offerId}')" style="flex:1;padding:10px;border:none;border-radius:8px;background:#2A5050;color:#fff;cursor:pointer;font-family:inherit;">إرسال المزايدة</button>
                </div>
            </div>
        </div>
    `;
    const existing = document.getElementById('bid-modal');
    if (existing) existing.remove();
    document.body.insertAdjacentHTML('beforeend', bidHtml);
}

function closeBidModal() {
    const m = document.getElementById('bid-modal');
    if (m) m.remove();
}

async function sendBid(offerId) {
    const amount = document.getElementById('bid-amount').value;
    const name = document.getElementById('bid-name').value.trim();
    const phone = document.getElementById('bid-phone').value.trim();
    if (!amount || !name || !phone) {
        showToast('يرجى تعبئة جميع الحقول', 'error');
        return;
    }
    const offer = OFFERS.find(o => String(o.id) === String(offerId));
    const currentBid = offer ? (offer.highestBid || offer.highest_bid || offer.price || 0) : 0;
    if (parseFloat(amount) <= parseFloat(currentBid)) {
        showToast('مبلغ المزايدة يجب أن يكون أعلى من السوم الحالي', 'error');
        return;
    }

    // إرسال المزايدة للإدارة عبر تيليجرام
    const bidData = {
        id: 'BID-' + Date.now(),
        offerId: offerId,
        offerTitle: offer ? offer.title : '',
        bidAmount: amount,
        name: name,
        phone: phone,
        type: 'bid',
    };
    notifyTelegramAdmin({
        id: bidData.id,
        name: name,
        phone: phone,
        propertyType: 'طلب مزايدة على ' + (offer ? offer.title : offerId),
        location: offer ? offer.area : '',
        area: '',
        price: amount,
        priceType: 'auction',
        description: 'طلب مزايدة على العرض ' + offerId + ' — المبلغ: ' + amount + ' ريال',
    }).catch(() => {});

    closeBidModal();
    showToast('تم إرسال طلب المزايدة بنجاح! سنتواصل معك قريباً.', 'success');
}

function showInquiryForm() {
    window.location.href = 'inquiry.html';
}

// ===== رسائل التوست =====
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

// ===== القائمة المتنقلة =====
function toggleMenu() {
    document.getElementById('nav-menu').classList.toggle('show');
}

// ===== تهيئة الصفحة =====
document.addEventListener('DOMContentLoaded', function() {
    // اكتشاف نوع الصفحة لتحديد الفلتر الافتراضي
    const pagePath = window.location.pathname.toLowerCase();
    let defaultFilter = 'all';
    if (pagePath.includes('farms')) defaultFilter = 'farm';
    else if (pagePath.includes('resthouses') || pagePath.includes('resthouse')) defaultFilter = 'resthouse';
    else if (pagePath.includes('lands') || pagePath.includes('land')) defaultFilter = 'land';

    loadOffers(defaultFilter);
    renderBousla();
    loadNews();

    // الترحيب
    if (window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/')) {
        setTimeout(() => {
            showToast('مرحباً بك في مكتب آفاق الإنجاز العقاري! 👋');
        }, 1500);
    }

    // إدخال المساعد بالـ Enter
    const aiInput = document.getElementById('ai-input');
    if (aiInput) {
        aiInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendAIMessage();
            }
        });
    }

    // ===== معرض الصور (Lightbox) لعرض صور العرض بدقة عالية =====
    initLightbox();

    // ===== تهيئة الخريطة التفاعلية (إن وجدت في الصفحة) =====
    if (document.getElementById('property-map')) {
        // تأخير بسيط للتأكد من تحميل Leaflet
        setTimeout(initPropertyMap, 300);
    }
});

// ============================================================
//  نظام معرض الصور (Lightbox) — يدعم صور WebP و JPEG
// ============================================================
function initLightbox() {
    if (document.getElementById('afaq-lightbox')) return;

    const lightbox = document.createElement('div');
    lightbox.id = 'afaq-lightbox';
    lightbox.style.cssText = 'display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:99999;justify-content:center;align-items:center;flex-direction:column;';
    lightbox.innerHTML = `
        <span id="afaq-lb-close" style="position:absolute;top:20px;right:30px;color:#fff;font-size:36px;cursor:pointer;z-index:100001;">&times;</span>
        <span id="afaq-lb-prev" style="position:absolute;left:20px;top:50%;transform:translateY(-50%);color:#fff;font-size:48px;cursor:pointer;z-index:100001;">&#10094;</span>
        <span id="afaq-lb-next" style="position:absolute;right:20px;top:50%;transform:translateY(-50%);color:#fff;font-size:48px;cursor:pointer;z-index:100001;">&#10095;</span>
        <img id="afaq-lb-img" style="max-width:90%;max-height:85%;object-fit:contain;border-radius:8px;" alt="">
        <div id="afaq-lb-caption" style="color:#fff;margin-top:12px;font-size:15px;text-align:center;max-width:80%;"></div>
    `;
    document.body.appendChild(lightbox);

    let currentImages = [];
    let currentIdx = 0;

    function showLightbox(images, idx, caption) {
        currentImages = images;
        currentIdx = idx;
        updateLightbox(caption);
        lightbox.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function updateLightbox(caption) {
        const imgEl = document.getElementById('afaq-lb-img');
        const capEl = document.getElementById('afaq-lb-caption');
        imgEl.src = currentImages[currentIdx];
        imgEl.alt = caption || '';
        capEl.textContent = caption ? caption + ' (' + (currentIdx + 1) + '/' + currentImages.length + ')' : (currentIdx + 1) + '/' + currentImages.length;
        document.getElementById('afaq-lb-prev').style.display = currentImages.length > 1 ? 'block' : 'none';
        document.getElementById('afaq-lb-next').style.display = currentImages.length > 1 ? 'block' : 'none';
    }

    function closeLightbox() {
        lightbox.style.display = 'none';
        document.body.style.overflow = '';
    }

    function nextImg() {
        currentIdx = (currentIdx + 1) % currentImages.length;
        updateLightbox(document.getElementById('afaq-lb-img').alt);
    }

    function prevImg() {
        currentIdx = (currentIdx - 1 + currentImages.length) % currentImages.length;
        updateLightbox(document.getElementById('afaq-lb-img').alt);
    }

    document.getElementById('afaq-lb-close').addEventListener('click', closeLightbox);
    document.getElementById('afaq-lb-next').addEventListener('click', nextImg);
    document.getElementById('afaq-lb-prev').addEventListener('click', prevImg);
    lightbox.addEventListener('click', function(e) {
        if (e.target === lightbox) closeLightbox();
    });
    document.addEventListener('keydown', function(e) {
        if (lightbox.style.display === 'flex') {
            if (e.key === 'Escape') closeLightbox();
            if (e.key === 'ArrowRight') nextImg();
            if (e.key === 'ArrowLeft') prevImg();
        }
    });

    document.addEventListener('click', function(e) {
        const cardImg = e.target.closest('.offer-card-img');
        if (cardImg) {
            const card = cardImg.closest('.offer-card');
            if (!card) return;
            const offerId = card.getAttribute('data-offer-id');
            const title = card.querySelector('h3') ? card.querySelector('h3').textContent.trim() : '';
            const offer = offerId ? OFFERS.find(o => String(o.id) === String(offerId)) : null;
            if (offer && offer.images && offer.images.length > 0) {
                showLightbox(offer.images, 0, offer.title);
            } else {
                showLightbox([cardImg.src], 0, title);
            }
        }
    });
}
