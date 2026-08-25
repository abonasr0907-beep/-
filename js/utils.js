/* =========================================================
   Afaq Real Estate Platform - Utils Module (js/utils.js)
   ========================================================= */

window.allOffers = window.allOffers || [];
window.filteredOffers = window.filteredOffers || [];
window.currentCurrency = localStorage.getItem('afaq_currency') || 'SAR';
window.exchangeRate = 3.75; // 1 USD = 3.75 SAR

// Whitelists & Config
window.OFFICE_DATA = {
    name: "آفاق الإنجاز العقارية",
    city: "الخرج",
    license: "1100004208",
    val_number: "1100004208",
    phone: "0544699933",
    whatsapp: "0545888931",
    combo: "0561610748"
};

window.CATEGORY_WHITELIST_JS = [
    'فلل', 'فلا', 'فيلا', 'شقق', 'شقة', 'أراضي', 'اراضي', 'أرض', 'ارض',
    'عمائر', 'عمارة', 'استراحات', 'استراحة', 'مزارع', 'مزرعة', 'محلات',
    'محل', 'مستودعات', 'مستودع', 'أبراج', 'برج', 'أدوار', 'دور',
    'شاليهات', 'شاليه', 'كمباوند', 'مكاتب', 'مكتب'
];

window.AREA_WHITELIST_JS = [
    'الخرج', 'الرياض', 'الهياثم', 'الدلم', 'العفجة', 'الضبيعة', 'الرحمانية',
    'حي الريان', 'حي الخزامى', 'حي النزهة', 'حي السلام', 'حي الجوهرة',
    'حي الخالدية', 'حي الناصفة', 'حي العالية', 'حي الاندلس', 'حي الورود',
    'حي غرناطة', 'حي الزهور', 'حي الحمراء', 'حي الصفا', 'حي النهضة',
    'حي المبرز', 'حي الرفيعة', 'حي الروضة', 'حي العزيزية', 'حي الهدا',
    'حي الشرفية', 'حي المنار', 'حي اليمامة', 'حي الفيصلية', 'حي التعاون',
    'حي الصحافة', 'حي الياسمين', 'حي الملقا', 'حي النرجس', 'حي العارض'
];

window.TELEGRAM_BRIDGE = "https://afaq-ingest-bridge.up.railway.app";
window.INGEST_SECRET = "afaq_secret_ingest_2026_x89k";

// Escape HTML
function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}
window.escapeHtml = escapeHtml;
window.escapeHTML = escapeHtml;

// Normalization functions
function normalizeTextJS(text) {
    if (!text) return '';
    return String(text)
        .replace(/[أإآ]/g, 'ا')
        .replace(/ة/g, 'ه')
        .replace(/ى/g, 'ي')
        .replace(/[ً-ْ]/g, '')
        .trim();
}
window.normalizeTextJS = normalizeTextJS;

function normalizeCategoryJS(category) {
    if (!category) return 'عامة';
    var norm = normalizeTextJS(category);
    if (norm.includes('ارض') || norm.includes('قطع')) return 'أراضي';
    if (norm.includes('فل') || norm.includes('فيلا') || norm.includes('دوبلكس')) return 'فلل';
    if (norm.includes('شق')) return 'شقق';
    if (norm.includes('عمار') || norm.includes('عمائر')) return 'عمائر';
    if (norm.includes('استراح')) return 'استراحات';
    if (norm.includes('مزرع') || norm.includes('مزارع')) return 'مزارع';
    if (norm.includes('محل') || norm.includes('معرض') || norm.includes('تجاري')) return 'محلات';
    if (norm.includes('مستودع') || norm.includes('هانجر')) return 'مستودعات';
    if (norm.includes('دور') || norm.includes('ادوار')) return 'أدوار';
    return category;
}
window.normalizeCategoryJS = normalizeCategoryJS;

function normalizeAreaJS(city, neighborhood) {
    var full = ((city || '') + ' ' + (neighborhood || '')).trim();
    if (!full) return 'الخرج';
    var norm = normalizeTextJS(full);
    if (norm.includes('الرياض')) return 'الرياض';
    if (norm.includes('الدلم')) return 'الدلم';
    if (norm.includes('الهياثم')) return 'الهياثم';
    if (norm.includes('العفجة')) return 'العفجة';
    if (norm.includes('الضبيعة')) return 'الضبيعة';
    if (norm.includes('الرحمانية') || norm.includes('الرحمانيه')) return 'الرحمانية';
    return city || 'الخرج';
}
window.normalizeAreaJS = normalizeAreaJS;

function isKnownCategoryJS(cat) {
    if (!cat) return false;
    var norm = normalizeTextJS(cat);
    return window.CATEGORY_WHITELIST_JS.some(function(w) {
        return normalizeTextJS(w) === norm;
    });
}
window.isKnownCategoryJS = isKnownCategoryJS;

function shouldIncludeInAllSectionsJS(cat) {
    return isKnownCategoryJS(cat);
}
window.shouldIncludeInAllSectionsJS = shouldIncludeInAllSectionsJS;

function isOfferPublished(offer) {
    if (!offer) return false;
    var st = (offer.status || '').toString().trim().toLowerCase();
    var pst = (offer.publish_status || '').toString().trim().toLowerCase();
    if (st === 'مباع' || st === 'sold') return true;
    if (st === 'draft' || st === 'مسودة' || st === 'مخفي' || st === 'hidden' || st === 'مرفوض') return false;
    if (st === 'published' || st === 'نشط' || st === 'مفتوح' || pst === 'published' || !st) return true;
    return true;
}
window.isOfferPublished = isOfferPublished;

function offerCategory(offer) {
    if (!offer) return 'عامة';
    var cat = offer.category || offer.type || offer.property_type || '';
    return normalizeCategoryJS(cat);
}
window.offerCategory = offerCategory;

function offerDetailLink(offer) {
    if (!offer) return '#';
    var extId = offer.external_id || offer.id;
    if (!extId) return '#';

    var title = offer.title || offer.name || offer.type || 'عرض عقاري';
    var slug = normalizeTextJS(title)
        .replace(/[^a-zA-Z0-9ء-ي]+/g, '-')
        .replace(/^-+|-+$/g, '') || 'offer';

    return 'offer/' + extId + '/' + slug;
}
window.offerDetailLink = offerDetailLink;

// Formatting
function formatNumber(num) {
    if (!num && num !== 0) return '0';
    return Number(num).toLocaleString('ar-SA');
}
window.formatNumber = formatNumber;

function getRawNumber(str) {
    if (!str) return 0;
    return str.toString().replace(/[^\d.]/g, '');
}
window.getRawNumber = getRawNumber;

function formatCurrency(priceSAR) {
    var val = parseFloat(priceSAR) || 0;
    if (window.currentCurrency === 'USD') {
        var usd = Math.round(val / window.exchangeRate);
        return '$' + usd.toLocaleString('en-US');
    }
    return val.toLocaleString('ar-SA') + ' ر.س';
}
window.formatCurrency = formatCurrency;

function toggleCurrency() {
    window.currentCurrency = window.currentCurrency === 'SAR' ? 'USD' : 'SAR';
    localStorage.setItem('afaq_currency', window.currentCurrency);
    var btns = document.querySelectorAll('.currency-toggle-btn');
    btns.forEach(function(b) {
        b.textContent = window.currentCurrency === 'SAR' ? 'ر.س / $' : '$ / ر.س';
    });
    if (window.renderOffers && window.allOffers) {
        window.renderOffers(window.filteredOffers || window.allOffers);
    }
}
window.toggleCurrency = toggleCurrency;

function formatPriceInput(input) {
    var val = input.value.replace(/[^\d]/g, '');
    if (val) {
        input.value = parseInt(val, 10).toLocaleString('ar-SA');
    } else {
        input.value = '';
    }
}
window.formatPriceInput = formatPriceInput;

function togglePriceFields() {
    var typeSelect = document.getElementById('type');
    var isRentGroup = document.getElementById('is-rent-group');
    if (typeSelect && isRentGroup) {
        if (typeSelect.value === 'إيجار') {
            isRentGroup.style.display = 'block';
        } else {
            isRentGroup.style.display = 'none';
        }
    }
}
window.togglePriceFields = togglePriceFields;

// Toast
function showToast(message, type) {
    type = type || 'info';
    var toast = document.createElement('div');
    toast.className = 'afaq-toast afaq-toast-' + type;
    toast.innerHTML = '<i class="fas ' + (type === 'success' ? 'fa-check-circle' : 'fa-info-circle') + '"></i> <span>' + escapeHtml(message) + '</span>';
    document.body.appendChild(toast);
    setTimeout(function() { toast.classList.add('show'); }, 10);
    setTimeout(function() {
        toast.classList.remove('show');
        setTimeout(function() { if (toast.parentNode) toast.parentNode.removeChild(toast); }, 300);
    }, 3500);
}
window.showToast = showToast;

// Menu & Header

function toggleMenu(show) {
    var navs = document.querySelectorAll('.nav-menu, .nav-links');
    var overlay = document.querySelector('.mobile-overlay');

    var isActive = show !== undefined ? show : (navs[0] ? !navs[0].classList.contains('active') : false);

    navs.forEach(function(nav) {
        nav.classList.toggle('active', isActive);
    });
    if (overlay) overlay.classList.toggle('active', isActive);
}
window.toggleMenu = toggleMenu;

function setupMobileSidebar() {
    var toggleBtn = document.querySelector('.btn-menu-toggle');
    var closeBtn = document.querySelector('.mobile-close-btn');
    var overlay = document.querySelector('.mobile-overlay');

    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'mobile-overlay';
        document.body.appendChild(overlay);
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleMenu(false);
        });
    }

    overlay.addEventListener('click', function() {
        toggleMenu(false);
    });

    document.addEventListener('click', function(e) {
        var isClickInsideNav = e.target.closest('.nav-menu') || e.target.closest('.nav-links') || e.target.closest('.btn-menu-toggle');
        if (!isClickInsideNav) {
            toggleMenu(false);
        }
    });
}
window.setupMobileSidebar = setupMobileSidebar;


function initDarkMode() {
    var savedTheme = localStorage.getItem('afaq_theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        document.body.classList.add('dark-mode');
    }
}
window.initDarkMode = initDarkMode;

// WhatsApp Channel
function initWhatsappChannel() {
    var channelBtns = document.querySelectorAll('.wa-channel-btn');
    channelBtns.forEach(function(btn) {
        btn.href = "https://whatsapp.com/channel/0029VaG931b60hBNX2E32R1q";
        btn.target = "_blank";
        btn.rel = "noopener noreferrer";
    });
}
window.initWhatsappChannel = initWhatsappChannel;

function openWhatsAppFast(phone, msg) {
    phone = phone || window.OFFICE_DATA.whatsapp;
    var cleanPhone = phone.replace(/[^\d]/g, '');
    if (cleanPhone.startsWith('0')) cleanPhone = '966' + cleanPhone.substring(1);
    var url = 'https://wa.me/' + cleanPhone + '?text=' + encodeURIComponent(msg || 'السلام عليكم، أود الاستفسار عن عروضكم العقارية');
    window.open(url, '_blank');
}
window.openWhatsAppFast = openWhatsAppFast;

// Ingest & Telegram APIs
function notifyTelegramAdmin(data) {
    return fetch(window.TELEGRAM_BRIDGE + '/ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Ingest-Secret': window.INGEST_SECRET
        },
        body: JSON.stringify(data)
    }).catch(function(err) { console.warn('Telegram Ingest error:', err); });
}
window.notifyTelegramAdmin = notifyTelegramAdmin;

function postToIngest(payload) {
    return fetch('/ingest', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Ingest-Secret': window.INGEST_SECRET
        },
        body: JSON.stringify(payload)
    }).catch(function(err) { console.warn('Ingest post error:', err); });
}
window.postToIngest = postToIngest;

function sendToBotApi(endpoint, data) {
    return fetch('/api/' + endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}
window.sendToBotApi = sendToBotApi;

function uploadVisitorImages(files) {
    var formData = new FormData();
    for (var i = 0; i < files.length; i++) {
        formData.append('images', files[i]);
    }
    return fetch('/api/upload', {
        method: 'POST',
        body: formData
    }).then(function(res) { return res.json(); });
}
window.uploadVisitorImages = uploadVisitorImages;

function compressImage(file, maxWidth, quality) {
    maxWidth = maxWidth || 1200;
    quality = quality || 0.8;
    return new Promise(function(resolve, reject) {
        var reader = new FileReader();
        reader.readAsDataURL(file);
        reader.onload = function(e) {
            var img = new Image();
            img.src = e.target.result;
            img.onload = function() {
                var canvas = document.createElement('canvas');
                var w = img.width;
                var h = img.height;
                if (w > maxWidth) {
                    h = Math.round((h * maxWidth) / w);
                    w = maxWidth;
                }
                canvas.width = w;
                canvas.height = h;
                var ctx = canvas.getContext('2d');
                ctx.drawImage(img, 0, 0, w, h);
                canvas.toBlob(function(blob) {
                    resolve(new File([blob], file.name, { type: 'image/jpeg' }));
                }, 'image/jpeg', quality);
            };
            img.onerror = reject;
        };
        reader.onerror = reject;
    });
}
window.compressImage = compressImage;

function compressImages(files) {
    var promises = Array.from(files).map(function(f) { return compressImage(f); });
    return Promise.all(promises);
}
window.compressImages = compressImages;

function applyLangEnTranslation() {
    if (document.documentElement.lang === 'en') {
        // Simple translation hooks if needed
    }
}
window.applyLangEnTranslation = applyLangEnTranslation;

function cleanCanonicalUrl() {
    var canonical = document.querySelector('link[rel="canonical"]');
    if (canonical) {
        var href = canonical.getAttribute('href');
        if (href && href.includes('index.html')) {
            canonical.setAttribute('href', href.replace('/index.html', '/'));
        }
    }
}
window.cleanCanonicalUrl = cleanCanonicalUrl;

function initGoogleSiteVerification() {
    // Site verification initialization
}
window.initGoogleSiteVerification = initGoogleSiteVerification;

function getMapApiUrl() {
    return '/api/properties/map';
}
window.getMapApiUrl = getMapApiUrl;

// ===== Glass Sidebar Social Links Injection =====
function injectSidebarSocialLinks() {
    var navs = document.querySelectorAll('.nav-menu, .nav-links');
    navs.forEach(function(nav) {
        if (nav.querySelector('.sidebar-social-section')) return;
        var socialSection = document.createElement('div');
        socialSection.className = 'sidebar-social-section';
        socialSection.innerHTML =
            '<div class="sidebar-social-title">تابعنا على</div>' +
            '<div class="sidebar-social-links">' +
                '<a href="https://www.instagram.com/afaqalanqaz" target="_blank" rel="noopener noreferrer" class="social-insta" title="إنستقرام"><i class="fab fa-instagram"></i></a>' +
                '<a href="https://www.tiktok.com/@whatyouarelookingforisw3" target="_blank" rel="noopener noreferrer" class="social-tiktok" title="تيك توك"><i class="fab fa-tiktok"></i></a>' +
                '<a href="https://www.snapchat.com/add/mmnf2278" target="_blank" rel="noopener noreferrer" class="social-snap" title="سناب شات"><i class="fab fa-snapchat"></i></a>' +
                '<a href="https://whatsapp.com/channel/0029VaG931b60hBNX2E32R1q" target="_blank" rel="noopener noreferrer" class="social-wa" title="قناة واتساب"><i class="fab fa-whatsapp"></i></a>' +
                '<a href="https://x.com/afaqalanqaz" target="_blank" rel="noopener noreferrer" class="social-x" title="X تويتر"><i class="fab fa-x-twitter"></i></a>' +
            '</div>';
        nav.appendChild(socialSection);
    });
}
window.injectSidebarSocialLinks = injectSidebarSocialLinks;
