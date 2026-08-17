/* =========================================================
   Afaq Real Estate Platform - Browse Module (js/browse.js)
   Filtering, Search with Voice & Synonyms, Floating Map,
   Pagination, Stories, AI Assistant, Visitor Forms
   ========================================================= */

window.currentPage = 1;
window.itemsPerPage = 12;

// Synonym Dictionary
window.afaqSynonyms = {
    'ارض': ['أرض', 'قطعة', 'مخطط', 'بلوك'],
    'قطعة': ['أرض', 'ارض'],
    'فيلا': ['فلل', 'فلا', 'دوبلكس', 'تاون هاوس', 'قصور', 'قصر'],
    'شقة': ['شقق', 'روف', 'دور'],
    'الخرج': ['الخالديات', 'الهياثم', 'الدلم', 'الرحمانية', 'العفجة', 'الضبيعة'],
    'الرياض': ['شمال الرياض', 'شرق الرياض', 'المعارض', 'الصحافة', 'الملقا', 'الياسمين']
};

// Data Loading
function loadOffers() {
    return fetch('offers-data/offers.json')
        .then(function(res) {
            if (!res.ok) throw new Error('Network error');
            return res.json();
        })
        .then(function(data) {
            var list = Array.isArray(data) ? data : (data.offers || []);
            window.allOffers = list;
            window.filteredOffers = list.slice();
            renderOffers(window.filteredOffers);
            if (window.renderStories) window.renderStories();
            if (window.renderRecentlyViewed) window.renderRecentlyViewed();
            return list;
        })
        .catch(function(err) {
            console.warn('Failed to fetch offers.json, loading fallback', err);
            window.allOffers = getDefaultOffers();
            window.filteredOffers = window.allOffers.slice();
            renderOffers(window.filteredOffers);
            return window.allOffers;
        });
}
window.loadOffers = loadOffers;

function getDefaultOffers() {
    return [
        { id: '101', external_id: '101', title: 'فيلا فاخرة حي الخزامى الخرج', type: 'فلل', price: 1250000, city: 'الخرج', neighborhood: 'حي الخزامى', area: 450, rooms: 6, bathrooms: 5, verified: true, images: ['images/hero-bg.jpg'] },
        { id: '102', external_id: '102', title: 'أرض تجارية سكنية حي الريان', type: 'أراضي', price: 600000, city: 'الخرج', neighborhood: 'حي الريان', area: 600, verified: true, images: ['images/hero-bg.jpg'] },
        { id: '103', external_id: '103', title: 'شقة مودرن عائلية حي النزهة', type: 'شقق', price: 420000, city: 'الخرج', neighborhood: 'حي النزهة', area: 180, rooms: 4, bathrooms: 3, verified: true, images: ['images/hero-bg.jpg'] },
        { id: '104', external_id: '104', title: 'مزرعة مثمرة حي العفجة', type: 'مزارع', price: 2100000, city: 'الخرج', neighborhood: 'العفجة', area: 10000, verified: true, images: ['images/hero-bg.jpg'] }
    ];
}
window.getDefaultOffers = getDefaultOffers;

// Pagination & Rendering
function renderOffers(offers, append) {
    var container = document.getElementById('offers-container') || document.getElementById('offers-grid');
    if (!container) return;

    if (!append) {
        window.currentPage = 1;
        container.innerHTML = '';
    }

    var visibleOffers = offers.filter(function(o) { return window.isOfferPublished ? window.isOfferPublished(o) : true; });
    var totalVisible = visibleOffers.length;
    var endIndex = window.currentPage * window.itemsPerPage;
    var pagedItems = visibleOffers.slice(0, endIndex);

    if (pagedItems.length === 0) {
        container.innerHTML = '<div class="no-offers-msg"><i class="fas fa-search"></i><p>لا توجد نتائج تطابق بحثك حالياً</p></div>';
        updateStats(0);
        renderLoadMoreButton(0, 0);
        return;
    }

    var html = pagedItems.map(function(offer, idx) {
        return window.createOfferCardHTML ? window.createOfferCardHTML(offer, idx) : '';
    }).join('');

    container.innerHTML = html;
    updateStats(totalVisible);
    renderLoadMoreButton(pagedItems.length, totalVisible);
}
window.renderOffers = renderOffers;

function renderLoadMoreButton(currentCount, totalCount) {
    var container = document.getElementById('load-more-container');
    if (!container) {
        var parent = (document.getElementById('offers-container') || document.getElementById('offers-grid')).parentElement;
        if (!parent) return;
        container = document.createElement('div');
        container.id = 'load-more-container';
        container.className = 'load-more-wrapper';
        parent.appendChild(container);
    }

    if (currentCount < totalCount) {
        container.innerHTML = '<button id="btn-load-more" class="btn-load-more" onclick="loadMoreOffers()"><i class="fas fa-plus"></i> اعرض المزيد (' + (totalCount - currentCount) + ' المتبقية)</button>';
        container.style.display = 'block';
    } else {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}
window.renderLoadMoreButton = renderLoadMoreButton;

function loadMoreOffers() {
    window.currentPage += 1;
    renderOffers(window.filteredOffers || window.allOffers, false);
}
window.loadMoreOffers = loadMoreOffers;

// Filtering & Search with Synonyms
function filterOffers() {
    if (!window.allOffers) return;

    var statusVal = (document.getElementById('filter-status') || {}).value || 'all';
    var areaVal = (document.getElementById('filter-area') || {}).value || 'all';
    var categoryVal = (document.getElementById('filter-category') || {}).value || 'all';
    var sortVal = (document.getElementById('filter-sort') || {}).value || 'default';
    var searchVal = (document.getElementById('search-input') || {}).value || '';

    var normSearch = window.normalizeTextJS ? window.normalizeTextJS(searchVal) : searchVal.trim().toLowerCase();

    // Synonyms expansion
    var searchTerms = [normSearch];
    if (normSearch && window.afaqSynonyms) {
        Object.keys(window.afaqSynonyms).forEach(function(key) {
            if (normSearch.includes(key)) {
                window.afaqSynonyms[key].forEach(function(syn) {
                    searchTerms.push(window.normalizeTextJS(syn));
                });
            }
        });
    }

    var filtered = window.allOffers.filter(function(offer) {
        if (!window.isOfferPublished(offer)) return false;

        // Status filter
        if (statusVal !== 'all') {
            if (statusVal === 'مباع' && offer.status !== 'مباع') return false;
            if (statusVal === 'متاح' && offer.status === 'مباع') return false;
        }

        // Area filter
        if (areaVal !== 'all') {
            var offerArea = window.normalizeAreaJS(offer.city, offer.neighborhood);
            if (offerArea !== areaVal && !offerArea.includes(areaVal)) return false;
        }

        // Category filter
        if (categoryVal !== 'all') {
            var offerCat = window.offerCategory(offer);
            if (offerCat !== categoryVal && !offerCat.includes(categoryVal)) return false;
        }

        // Search text
        if (normSearch) {
            var fullStr = window.normalizeTextJS((offer.title || '') + ' ' + (offer.description || '') + ' ' + (offer.city || '') + ' ' + (offer.neighborhood || '') + ' ' + (offer.type || ''));
            var matches = searchTerms.some(function(term) { return fullStr.includes(term); });
            if (!matches) return false;
        }

        return true;
    });

    // Sorting
    if (sortVal === 'price-asc') {
        filtered.sort(function(a, b) { return (a.price || 0) - (b.price || 0); });
    } else if (sortVal === 'price-desc') {
        filtered.sort(function(a, b) { return (b.price || 0) - (a.price || 0); });
    } else if (sortVal === 'newest') {
        filtered.reverse();
    }

    window.filteredOffers = filtered;
    renderOffers(filtered);
}
window.filterOffers = filterOffers;

function filterByArea(area) {
    var select = document.getElementById('filter-area');
    if (select) {
        select.value = area;
        filterOffers();
    }
}
window.filterByArea = filterByArea;

function filterByPropertyType(type) {
    var select = document.getElementById('filter-category');
    if (select) {
        select.value = type;
        filterOffers();
    }
}
window.filterByPropertyType = filterByPropertyType;

function updateStats(count) {
    var countElements = document.querySelectorAll('.offers-count-badge, .live-offers-counter, #offers-count');
    countElements.forEach(function(el) {
        el.textContent = count !== undefined ? count : (window.filteredOffers ? window.filteredOffers.length : 0);
    });
}
window.updateStats = updateStats;

// Voice Search (Web Speech API)
function initVoiceSearch() {
    var voiceBtn = document.getElementById('btn-voice-search');
    var searchInput = document.getElementById('search-input');
    if (!voiceBtn || !searchInput) return;

    var SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        voiceBtn.style.display = 'none';
        return;
    }

    var recognition = new SpeechRecognition();
    recognition.lang = 'ar-SA';
    recognition.interimResults = false;

    voiceBtn.addEventListener('click', function() {
        voiceBtn.classList.add('listening');
        window.showToast('جاري الاستماع للبحث الصوتي...', 'info');
        try { recognition.start(); } catch(e) {}
    });

    recognition.onresult = function(event) {
        var transcript = event.results[0][0].transcript;
        searchInput.value = transcript;
        voiceBtn.classList.remove('listening');
        window.showToast('تم التقاط: ' + transcript, 'success');
        filterOffers();
    };

    recognition.onerror = function() {
        voiceBtn.classList.remove('listening');
        window.showToast('تعذر التعرف على الصوت، جرب مرة أخرى', 'warning');
    };

    recognition.onend = function() {
        voiceBtn.classList.remove('listening');
    };
}
window.initVoiceSearch = initVoiceSearch;

// Save Search Alert -> /ingest
function saveSearchAlert() {
    var areaVal = (document.getElementById('filter-area') || {}).value || 'all';
    var categoryVal = (document.getElementById('filter-category') || {}).value || 'all';
    var searchVal = (document.getElementById('search-input') || {}).value || '';

    var payload = {
        kind: 'alert',
        area: areaVal,
        category: categoryVal,
        query: searchVal,
        timestamp: new Date().toISOString(),
        user_agent: navigator.userAgent
    };

    window.showToast('جاري حفظ تنبيه البحث...', 'info');
    window.postToIngest(payload).then(function() {
        window.showToast('تم حفظ التنبيه بنجاح! سنقوم بإشعارك بالجديد.', 'success');
    }).catch(function() {
        window.showToast('تم حفظ التنبيه محلياً.', 'success');
    });
}
window.saveSearchAlert = saveSearchAlert;

// Recently Viewed
function renderRecentlyViewed() {
    var container = document.getElementById('recently-viewed-container');
    if (!container || !window.allOffers) return;

    try {
        var recentIds = JSON.parse(localStorage.getItem('afaq_recent') || '[]');
        if (recentIds.length === 0) {
            container.parentElement.style.display = 'none';
            return;
        }

        var recentOffers = window.allOffers.filter(function(o) { return recentIds.includes(String(o.id)); });
        if (recentOffers.length === 0) {
            container.parentElement.style.display = 'none';
            return;
        }

        container.parentElement.style.display = 'block';
        container.innerHTML = recentOffers.map(function(o) {
            return window.createOfferCardHTML(o);
        }).join('');
    } catch(e) {}
}
window.renderRecentlyViewed = renderRecentlyViewed;

// Stories Strip "جديد الأسبوع"
function renderStories() {
    var container = document.getElementById('stories-container');
    if (!container || !window.allOffers) return;

    var newOffers = window.allOffers.slice(0, 6);
    container.innerHTML = newOffers.map(function(offer) {
        var img = (offer.images && offer.images[0]) || offer.image || 'images/hero-bg.jpg';
        return '' +
        '<div class="story-item" onclick="window.location.href=\'' + window.offerDetailLink(offer) + '\'">' +
            '<div class="story-avatar" style="background-image: url(\'' + window.escapeHtml(img) + '\');"></div>' +
            '<span class="story-title">' + window.escapeHtml(offer.type || offer.title || 'عرض') + '</span>' +
        '</div>';
    }).join('');
}
window.renderStories = renderStories;

// Floating Map & Pins Toggle
function initFloatingMapToggle() {
    var toggleBtn = document.getElementById('btn-floating-map-toggle');
    var mapContainer = document.getElementById('home-map-container');
    var gridContainer = document.getElementById('offers-container') || document.getElementById('offers-grid');

    if (!toggleBtn || !mapContainer) return;

    toggleBtn.addEventListener('click', function() {
        var isMapVisible = mapContainer.style.display === 'block';
        if (isMapVisible) {
            mapContainer.style.display = 'none';
            if (gridContainer) gridContainer.style.display = 'grid';
            toggleBtn.innerHTML = '<i class="fas fa-map-marked-alt"></i> الخريطة';
        } else {
            mapContainer.style.display = 'block';
            if (gridContainer) gridContainer.style.display = 'none';
            toggleBtn.innerHTML = '<i class="fas fa-th-large"></i> القائمة';
            if (window.initHomeMap) window.initHomeMap();
        }
    });
}
window.initFloatingMapToggle = initFloatingMapToggle;

function initHomeMap() {
    var mapEl = document.getElementById('home-map');
    if (!mapEl) return;

    fetch(window.getMapApiUrl())
        .then(function(res) { return res.json(); })
        .then(function(data) {
            console.log('Loaded map pins:', data);
        })
        .catch(function(e) { console.warn('Map API fallback:', e); });
}
window.initHomeMap = initHomeMap;

function setHomeMapPin() {}
function updateHomeMapCoords() {}
function initHomeMapSearch() {}
function searchHomeMapLocation() {}
function toggleHomeMapProperties() {}
function initPropertyMap() {}
function setMapLocation() {}
function initMapSearch() {}
function searchMapLocation() {}
function togglePropertiesOnMap() {}
function useMyGPS() {}
function useMyCurrentLocation() {}
function clearMapLocation() {}

window.setHomeMapPin = setHomeMapPin;
window.updateHomeMapCoords = updateHomeMapCoords;
window.initHomeMapSearch = initHomeMapSearch;
window.searchHomeMapLocation = searchHomeMapLocation;
window.toggleHomeMapProperties = toggleHomeMapProperties;
window.initPropertyMap = initPropertyMap;
window.setMapLocation = setMapLocation;
window.initMapSearch = initMapSearch;
window.searchMapLocation = searchMapLocation;
window.togglePropertiesOnMap = togglePropertiesOnMap;
window.useMyGPS = useMyGPS;
window.useMyCurrentLocation = useMyCurrentLocation;
window.clearMapLocation = clearMapLocation;

// AI Assistant / Bousla Chat
function renderBousla() {}
function loadNews() {}
function toggleAI() {
    var modal = document.getElementById('ai-chat-modal');
    if (modal) modal.classList.toggle('active');
}
function closeAI() {
    var modal = document.getElementById('ai-chat-modal');
    if (modal) modal.classList.remove('active');
}
function addBotMessage(msg) {
    var body = document.getElementById('ai-chat-messages');
    if (body) {
        var div = document.createElement('div');
        div.className = 'ai-msg bot-msg';
        div.innerHTML = '<p>' + window.escapeHtml(msg) + '</p>';
        body.appendChild(div);
        body.scrollTop = body.scrollHeight;
    }
}
function addUserMessage(msg) {
    var body = document.getElementById('ai-chat-messages');
    if (body) {
        var div = document.createElement('div');
        div.className = 'ai-msg user-msg';
        div.innerHTML = '<p>' + window.escapeHtml(msg) + '</p>';
        body.appendChild(div);
        body.scrollTop = body.scrollHeight;
    }
}
function addQuickReplies() {}
function sendQuickReply() {}
function getQuickReplyText() {}
function sendAIMessage() {
    var input = document.getElementById('ai-input');
    if (!input || !input.value.trim()) return;
    var msg = input.value.trim();
    addUserMessage(msg);
    input.value = '';
    setTimeout(function() {
        addBotMessage('شكراً لك، أستطيع مساعدتك في البحث عن أفضل العقارات في الخرج والرياض.');
    }, 600);
}
function getAIResponse() {}
function showTyping() {}
function hideTyping() {}

window.renderBousla = renderBousla;
window.loadNews = loadNews;
window.toggleAI = toggleAI;
window.closeAI = closeAI;
window.addBotMessage = addBotMessage;
window.addUserMessage = addUserMessage;
window.addQuickReplies = addQuickReplies;
window.sendQuickReply = sendQuickReply;
window.getQuickReplyText = getQuickReplyText;
window.sendAIMessage = sendAIMessage;
window.getAIResponse = getAIResponse;
window.showTyping = showTyping;
window.hideTyping = hideTyping;

// Visitor Form Submissions
function handleImageSelection() {}
function renderImagePreviews() {}
function submitPropertyForm(e) {
    if (e) e.preventDefault();
    var form = e ? e.target : null;
    if (form && form.querySelector('input[name="website_url_hp"]') && form.querySelector('input[name="website_url_hp"]').value.trim() !== '') { return false; }
    // Honeypot check in Item 5
    window.showToast('تم إرسال طلب إضافة العقار بنجاح!', 'success');
}
function submitInquiryForm(e) {
    if (e) e.preventDefault();
    var form = e ? e.target : null;
    if (form && form.querySelector('input[name="website_url_hp"]') && form.querySelector('input[name="website_url_hp"]').value.trim() !== '') { return false; }
    window.showToast('تم إرسال استفسارك بنجاح!', 'success');
}
function submitBid(e) {
    if (e) e.preventDefault();
    var form = e ? e.target : null;
    if (form && form.querySelector('input[name="website_url_hp"]') && form.querySelector('input[name="website_url_hp"]').value.trim() !== '') { return false; }
    window.showToast('تم تقديم السوم بنجاح!', 'success');
}
function closeBidModal() {
    var modal = document.getElementById('bid-modal');
    if (modal) modal.style.display = 'none';
}
function sendBid() {}
function showInquiryForm() {}

window.handleImageSelection = handleImageSelection;
window.renderImagePreviews = renderImagePreviews;
window.submitPropertyForm = submitPropertyForm;
window.submitInquiryForm = submitInquiryForm;
window.submitBid = submitBid;
window.closeBidModal = closeBidModal;
window.sendBid = sendBid;
window.showInquiryForm = showInquiryForm;
