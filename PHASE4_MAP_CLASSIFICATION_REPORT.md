# Phase 4 — Map & Classification Enhancement Report

**التاريخ:** 2025-08-11
**الإصدار:** Stable Version (تحديثات تزايدية فقط — لا إعادة بناء)
**القيود المطبقة:** لم يتم تعديل GitHub Actions / Railway Config / Telegram Bot / Webhook / أنظمة الطلب الحالية. تم فقط إجراء تحديثات تزايدية على الخريطة ونظام التصنيف.

---

## 1. الملفات المعدّلة (Modified Files)

| الملف | نوع التغيير | الأسطر المضافة |
|---|---|---|
| `api_server/visitor_api.py` | إضافة endpoint جديد + تحديث قائمة endpoints | +62 |
| `index.html` | استبدال iframe الثابت بخريطة Leaflet تفاعلية + CSS + مكتبات | +153 |
| `js/main.js` | إضافة دوال خريطة الصفحة الرئيسية + استدعاء التهيئة | +364 |
| `list-property.html` | تحديث خيارات التصنيف (القسم / النوع / الموقع) | +30 |
| **المجموع** | | **+585 / -24** |

ملف جديد: `PHASE4_MAP_CLASSIFICATION_REPORT.md` (هذا الملف).

---

## 2. الدوال والميزات الجديدة (New Functions & Features)

### 2.1 Map API — `/api/properties/map` (api_server/visitor_api.py)

**الدالة:** `handle_properties_map(request)` (السطر 458)
**المسار:** `GET /api/properties/map` (مُسجّل في السطر 533)

**الوصف:** يقرأ ملف `offers.json` من مستودع GitHub عبر `raw.githubusercontent.com`، يفلتر العروض التي تحتوي إحداثيات صالحة (visitor_lat / visitor_lng أو lat / lng)، ويعيدها بصيغة JSON مناسبة للخريطة التفاعلية.

**الحقول المُعادة لكل عقار:**
- `id` — معرّف العقار
- `title` — العنوان
- `latitude` / `longitude` — الإحداثيات (float)
- `section` — القسم (زراعي/سكني/تجاري أو القيم القديمة)
- `property_type` — نوع العقار (مزرعة/استراحة/أرض/فيلا/مشروع)
- `type` — النوع الداخلي (farm/land/resthouse)
- `area` — المنطقة
- `price` — السعر
- `image` — أول صورة
- `operation_type` — نوع العملية (sale/rent)
- `size_sqm` — المساحة بالمتر المربع
- `map_link` — رابط الموقع

**الاستجابة:**
```json
{
  "ok": true,
  "count": 2,
  "properties": [ ... ]
}
```

**تحديث إضافي:** تمت إضافة `/api/properties/map` و `/api/visitor-images` إلى قائمة endpoints المعروضة في `handle_root` (السطر 523).

### 2.2 الخريطة التفاعلية للصفحة الرئيسية (index.html + js/main.js)

#### في index.html:
- **مكتبات Leaflet:** تمت إضافة `leaflet.css` (1.9.4) و `Control.Geocoder.css` (2.4.0) في `<head>`، و `leaflet.js` و `Control.Geocoder.js` قبل `main.js`.
- **حاوية الخريطة:** `<div id="afaq-interactive-map"></div>` (السطر 429) — ارتفاع 520px مع حواف دائرية وظل.
- **شريط الأدوات (Toolbar):**
  - مربع البحث: `<input id="home-map-search-input">` (السطر 417) — بحث عبر Nominatim/OpenStreetMap
  - زر GPS: `<button id="home-map-gps-btn">` (السطر 420) — الموقع الحالي
  - زر العقارات: `<button id="home-map-properties-btn">` (السطر 423) — إظهار/إخفاء العقارات القريبة
- **عرض الإحداثيات:** `#home-map-coords` / `#home-coords-text` — يعرض خط العرض وخط الطول
- **زر خرائط Google:** محفوظ للانتقال إلى Google Maps
- **CSS مخصص:** `.afaq-map-toolbar`, `.afaq-map-search-box`, `.afaq-map-search-results`, `.afaq-map-btn`, `.afaq-property-popup` (مع img, h4, popup-meta, popup-price, popup-contact), `.afaq-sat-toggle-home`, تنسيق leaflet-popup

#### في js/main.js (دوال جديدة، السطور 1417–1803):
| الدالة | السطر | الوظيفة |
|---|---|---|
| `getMapApiUrl()` | 1417 | يعيد رابط API المناسب (Railway أو GitHub Pages fallback) |
| `initHomeMap()` | 1426 | تهيئة الخريطة التفاعلية — L.map مع fadeAnimation, zoomAnimation, inertia للأنيميشن السلس، طبقة OSM قياسية + طبقة أقمار صناعية Esri + طبقة تسميات CARTO |
| `setHomeMapPin(lat, lng)` | 1545 | وضع علامة قابلة للسحب (draggable marker) مع divIcon مخصص |
| `updateHomeMapCoords(lat, lng)` | 1561 | حفظ/عرض خط العرض وخط الطول عند تحريك العلامة (dragend event) |
| `initHomeMapSearch()` | 1569 | ربط مربع البحث بـ Nominatim API — بحث مع debounce، عرض نتائج منسدلة، النقر ينتقل للموقع |
| `toggleHomeMapProperties()` | 1636 | جلب العقارات من `/api/properties/map`، إنشاء علامات مع popup (صورة + تفاصيل + موقع + زر تواصل)، إظهار/إخفاء الطبقة |

**استدعاء التهيئة:** أُضيف داخل `DOMContentLoaded` (السطر 1802):
```javascript
if (document.getElementById('afaq-interactive-map')) {
    setTimeout(initHomeMap, 400);
}
```

### 2.3 نظام التصنيف (list-property.html)

#### القسم (Section) — D1:
خيارات جديدة: **زراعي** (مزارع / أرض زراعية)، **سكني** (أرض سكنية / فلل)، **تجاري** (أرض تجارية / مشاريع) + القيم القديمة (مزارع/أراضي/استراحات) للتوافق مع البيانات الموجودة.

#### نوع العقار (Property Type) — D2:
خيارات: **مزرعة**، **استراحة**، **أرض**، أرض زراعية، أرض سكنية، أرض تجارية، **فيلا**، فيلا / منزل، **مشروع** (جديد).

#### الموقع/المنطقة (Area) — D3:
قائمة محدّثة تشمل: مخطط الرحمانية، الهياثم، الدلم، الضبيعية، العفجة، **الشديدية** (جديد)، **حي النرجس** (جديد)، الخرج (منطقة أخرى)، الرياض.

جميع الحقول `required` + التحقق في `submitPropertyForm()` (السطر 1057) يجبر المستخدم على اختيار القسم + النوع + الموقع.

---

## 3. ربط النشر والفلترة (Publishing & Filtering Linkage) — D4/D5

### النشر (submitPropertyForm):
- يتحقق من: `data.name, data.phone, data.section, data.location, data.propertyType, data.area, data.price` (السطر 1057)
- يرسل في رسالة WhatsApp: القسم، نوع العقار، العملية، الموقع، المساحة، السعر
- يخزّن الطلب في localStorage مع جميع الحقول

### الفلترة (renderOffers) — السطر 235:
فلترة ثلاثية (3-way filtering):
1. **القسم/النوع:** `o.type === filter` (farm/land/resthouse)
2. **المنطقة:** `o.area === areaFilter`
3. **نوع العقار:** `(o.property_type || o.category) === propTypeFilter`

```javascript
function renderOffers(filter = 'all', areaFilter = 'all', propTypeFilter = 'all') {
    let filtered = OFFERS;
    if (filter !== 'all') filtered = filtered.filter(o => o.type === filter);
    if (areaFilter !== 'all') filtered = filtered.filter(o => o.area === areaFilter);
    if (propTypeFilter !== 'all') filtered = filtered.filter(o => (o.property_type || o.category) === propTypeFilter);
    // ...
}
```

### Popup عند النقر على العلامة — C2:
عند النقر على علامة عقار في الخريطة، يظهر popup يحتوي على:
- صورة العقار (مع onerror fallback)
- العنوان (h4)
- السعر (popup-price)
- المنطقة (popup-meta مع أيقونة)
- القسم (popup-meta)
- نوع العقار (popup-meta)
- المساحة (popup-meta)
- نوع العملية (للبيع/للإيجار)
- **زر التواصل** (popup-contact) — رابط WhatsApp

---

## 4. الاختبارات (Tests) — Section E

| الاختبار | النتيجة | التفاصيل |
|---|---|---|
| E1. JS Compile (`node -c js/main.js`) | ✅ نجاح | لا أخطاء صياغة |
| E2. Python Compile (`py_compile`) | ✅ نجاح | visitor_api.py سليم |
| E3. offers.json valid | ✅ نجاح | 31 عرض، بنية `{offers:[...]}` |
| E4. API endpoint test | ✅ نجاح | جلب مباشر من GitHub raw: 31 عرض، 2 بإحداثيات صالحة |
| E5. 3-way filtering | ✅ نجاح | farm=9، farm+الهياثم=1، مزرعة=10، all=31 |

### العروض ذات الإحداثيات (للخريطة):
1. **LND-142D0E** — أرض تجارية — الخرج (منطقة أخرى) | lat: 24.190182, lng: 47.155838 | قسم: أراضي | نوع: أرض تجارية
2. **FRM-3A6598** — مزرعة — حي النرجس | lat: 24.8607, lng: 46.7154 | قسم: مزارع | نوع: مزرعة

---

## 5. حالة GitHub و Railway (GitHub & Railway Status)

### GitHub:
- **المستودع:** `abonasr0907-beep/-` (فرع: main)
- **الحالة:** التعديلات جاهزة لل_commit والpush (انظر القسم 6)
- **ملاحظة:** بوت الأخبار الآلي يرفع commits كل ~1-2 دقيقة، لذا يُستخدم retry loop: `git pull --rebase && git push`
- **لم يتم تعديل:** GitHub Actions، أو أي ملفات تكوين (.github/workflows)

### Railway:
- **الرابط:** `https://worker-production-7713.up.railway.app`
- **Endpoint جديد:** `/api/properties/map` — سيكون متاحاً بعد deploy تلقائي عند push (Railway يشغّل `api_server/visitor_api.py`)
- **لم يتم تعديل:** railway.toml، Dockerfile، Procfile، أو أي إعدادات Railway
- **الاختبار المباشر:** تم التحقق من أن جلب offers.json من GitHub raw يعمل (31 عرض)

### Telegram Bot / Webhook:
- **لم يتم لمسها** — لا توجد تعديلات على `bot/` أو أي ملفات webhook

---

## 6. ملاحظات متبقية (Remaining Notes)

1. **الأنيميشن السلس (Smooth Animation):** مُفعّل عبر `fadeAnimation: true, zoomAnimation: true, inertia: true` في خيارات L.map، بالإضافة إلى `fadeAnimation` لطبقات التسميات.
2. **التحميل السريع (Fast Loading):** استخدام CDN (unpkg) لتحميل Leaflet + lazy loading للعقارات (تُجلب فقط عند الضغط على زر "العقارات القريبة").
3. **التكبير الأفضل (Better Zoom):** `maxZoom: 19` لطبقة OSM، `maxZoom: 19` للأقمار الصناعية Esri، مع `zoomControl: true`.
4. **طبقة الأقمار الصناعية:** متاحة عبر زر التبديل (satellite toggle) — Esri World Imagery + CARTO labels overlay.
5. **البحث داخل الخريطة:** عبر Nominatim API (مجاني، بدون مفتاح API) مع debounce 400ms لتفادي الطلبات الزائدة.
6. **زر GPS:** يستخدم `navigator.geolocation.getCurrentPosition` مع معالجة الأخطاء (رفض الإذن / عدم التوفر).
7. **حفظ الإحداثيات:** عند سحب العلامة أو النقر على الخريطة، تُحدّث قيم lat/lng في العناصر `#home-coords-text` ويمكن استخدامها لاحقاً.
8. **التوافق مع البيانات القديمة:** خيارات التصنيف الجديدة (زراعي/سكني/تجاري) أُضيفت بجانب القيم القديمة (مزارع/أراضي/استراحات) لضمان أن العروض الموجودة تظهر بشكل صحيح في الفلترة.
9. **العيوب القديمة الموروثة (من Phase 3):** فقط عرضان من أصل 31 لديهما إحداثيات — باقي العروض تحتاج إلى إضافة lat/lng لتظهر على الخريطة (هذا يتطلب تحديث offers-data/offers.json لاحقاً، وهو خارج نطاق Phase 4 الذي يقتصر على البنية التحتية للخريطة والتصنيف).

---

## 7. ملخص التنفيذ (Implementation Summary)

تم تنفيذ Phase 4 بنجاح كتحديثات تزايدية على النسخة المستقرة:

- **خريطة تفاعلية كاملة** في الصفحة الرئيسية (بحث + GPS + علامة قابلة للسحب + حفظ إحداثيات + أنيميشن سلس + عقارات قريبة + popup بتفاصيل العقار وزر تواصل)
- **API endpoint جديد** `/api/properties/map` يغذّي الخريطة ببيانات العقارات من GitHub
- **نظام تصنيف محسّن** يجبر المستخدم على اختيار القسم (زراعي/سكني/تجاري) + النوع (مزرعة/استراحة/أرض/فيلا/مشروع) + المنطقة، مع ربط النشر والفلترة
- **جميع الاختبارات نجحت** (JS, Python, JSON, API, فلترة)
- **لم يتم تعديل** GitHub Actions / Railway Config / Telegram Bot / Webhook / أنظمة الطلب الحالية

**الحالة:** ✅ جاهز للـ commit والـ push إلى GitHub main.
