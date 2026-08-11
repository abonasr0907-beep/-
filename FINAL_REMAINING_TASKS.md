# تقرير المهام المتبقية — FINAL_REMAINING_TASKS.md
## آفاق الإنجاز العقاري — Phase 4

**التاريخ:** 2025-08-11  
**المرجع:** PHASE3_FINAL_REPORT.md + CHECKPOINT_PHASE2.md  
**المنهجية:** تحديث تدريجي (Incremental Update) — لا إعادة بناء، لا تغيير GitHub/Railway/Telegram/Webhook.  

---

## ملخص التنفيذ

تم إكمال جميع المهام الست (6) المتبقية بنجاح، مع الالتزام الكامل بالمنهجية التدريجية. تم دمج التغييرات في الفرع الرئيسي (`main`) عبر Pull Request #8، وتم التحقق من تشغيل Railway والـ Telegram Webhook.

| المهمة | الحالة | الملفات المعدلة |
|--------|--------|-----------------|
| 1. إصلاح إرسال صور طلبات الزوار | ✅ مكتملة | visitor_api.py, github_sync.py, bot.py |
| 2. تحسين نظام Request Management | ✅ مكتملة | bot.py |
| 3. التحقق قبل رسالة النجاح | ✅ مكتملة | bot.py |
| 4. تحسين الخريطة | ✅ مكتملة | list-property.html, main.js |
| 5. نظام التصنيف | ✅ مكتملة | offers.json, index.html, main.js |
| 6. نظام الإبلاغ عن الأخطاء | ✅ مكتملة | error_reporter.py (جديد), bot.py, visitor_api.py |

---

## التفاصيل التقنية لكل مهمة

### المهمة 1: إصلاح إرسال صور طلبات الزوار إلى Telegram Bot

**المشكلة الأصلية:**  
عندما يرسل زائر طلباً من الموقع، يصل الإشعار النصي إلى المسؤول بأزرار الموافقة/الرفض، لكن الصور تصل في رسالة منفصلة بدون أزرار (لأن `sendMediaGroup` لا يدعم `reply_markup`). بالإضافة إلى ذلك، يقرأ `bot.py` ملف `visitor_requests.json` محلياً ولا يتم تحديثه عند رفع الصور إلى GitHub، مما يمنع ربط الصور بالعرض المنشور.

**الحل المطبق:**

1. **إعادة كتابة `send_telegram_images()` في `visitor_api.py`:**
   - الصورة الأولى تُرسل عبر `sendPhoto` مع `caption` يحتوي على `request_id` و `reply_markup` (أزرار الموافقة/الرفض)
   - الصور المتبقية تُرسل عبر `sendMediaGroup` مع `caption` يربطها بـ `request_id`
   - المسؤول يستقبل الآن الصور مع أزرار الموافقة/الرفض مباشرة

2. **إضافة دالتين جديدتين في `github_sync.py`:**
   - `fetch_visitor_request_images(request_id)`: يبحث في `visitor_requests.json` على GitHub عن مسارات الصور المرتبطة بالطلب (في أقسام `requests`, `inquiries`, `offer_submissions`)
   - `download_visitor_image(repo_path, local_dir)`: يحمّل صورة من GitHub إلى المسار المحلي باستخدام Contents API أو `raw.githubusercontent.com` كاحتياطي

3. **إدراج كتلة جلب الصور في `_approve_visitor_request` (`bot.py`):**
   - قبل بناء كائن العرض، يحاول النظام قراءة الصور من `item.get("images", [])`
   - إذا لم تكن موجودة محلياً وGitHub مفعّل، يجلب مسارات الصور من GitHub ويحمّلها
   - الصور المحمّلة تُربط بالعرض: `"images": list(_request_images)`
   - تم إصلاح خطأ `NameError` كان سيحدث لأن `_request_images` كان مستخدماً لكنه غير معرّف

---

### المهمة 2: تحسين نظام Request Management

**المتطلبات:** عدم حذف الطلب بعد النشر، إنشاء حالات متعددة، تحديث `_approve_visitor_request`.

**الحل المطبق:**

1. **إضافة ثوابت الحالات (بعد السطر 75 في `bot.py`):**
   ```python
   REQUEST_STATUS_NEW = "NEW"
   REQUEST_STATUS_UNDER_REVIEW = "UNDER_REVIEW"
   REQUEST_STATUS_APPROVED = "APPROVED"
   REQUEST_STATUS_PUBLISHING = "PUBLISHING"
   REQUEST_STATUS_PUBLISHED = "PUBLISHED"
   REQUEST_STATUS_ARCHIVED = "ARCHIVED"
   REQUEST_STATUS_REJECTED = "REJECTED"
   ```
   - `REQUEST_STATUS_LABELS`: قاموس بالتسميات العربية
   - `normalize_request_status()`: دالة لتحويل الحالات القديمة (`approved` → `PUBLISHED`, `pending` → `UNDER_REVIEW`)

2. **تحديث `_approve_visitor_request`:**
   - قبل خطوة النشر: `item["status"] = REQUEST_STATUS_PUBLISHING` + `publishing_started_at`
   - بعد نجاح النشر: `item["status"] = REQUEST_STATUS_PUBLISHED` + `published_at`
   - `published_offer_id` يُحفظ كمعرف العرض المنشور

3. **إزالة حذف الرسالة:**
   - تم حذف كتلة `query.message.delete()` — الطلب يُحفظ ولا يُحذف بعد النشر
   - الطلب يبقى مرئياً في السجل مع حالته الجديدة (`PUBLISHED`)

---

### المهمة 3: التحقق قبل رسالة النجاح

**المتطلبات:** التأكد من وجود العرض، القسم الصحيح، حفظ المعرف، عدم إظهار النجاح إلا بعد التحقق.

**الحل المطبق:**

1. **`verify_ok` (موجود سابقاً):** يتحقق من وجود العرض في `offers.json` بعد الحفظ
2. **`verify_section_ok` (جديد):** يتحقق من أن نوع/قسم العرض في `offers.json` يطابق النوع المتوقع
   ```python
   verify_offer = next((o for o in verify_data.get("offers", []) if o.get("id") == offer_id), None)
   verify_section_ok = True
   if verify_offer:
       _v_type = verify_offer.get("type", "").lower()
       _expected = offer.get("type", "").lower()
       if _v_type != _expected:
           verify_section_ok = False
   ```
3. **`published_offer_id`:** يُحفظ في الطلب (موجود سابقاً)
4. **رسالة النجاح:** لا تُظهر إلا بعد نجاح جميع التحققات (`not verify_ok or not verify_section_ok` → رسالة خطأ + return)
5. **الإبلاغ عن الأخطاء:** فشل التحقق يُبلغ إلى `error_reporter` بدرجة `critical`

---

### المهمة 4: تحسين الخريطة

**المتطلبات:** وضع الدبوس بالضغط، تحريك الدبوس بالسحب، حفظ Lat/Lng, مربع بحث, عرض العقارات على الخريطة.

**الموجود سابقاً (لم يُعد تغييره):**
- وضع الدبوس بالضغط (`propertyMap.on('click')`)
- تحريك الدبوس بالسحب (`{draggable: true}` + `dragend` event)
- حفظ Lat/Lng في حقول مخفية (`lat-input`, `lng-input`, `maps-link-input`)
- استخدام GPS
- تبديل الأقمار الصناعية/العادية

**المضاف حديثاً:**

1. **مربع البحث (في `list-property.html` + `main.js`):**
   - حقل إدخال `#map-search-input` فوق الخريطة
   - يستخدم Nominatim/OpenStreetMap Geocoding API (مجاني، لا يحتاج مفتاح API)
   - بحث ديناميكي مع تأخير 500ms (debounce)
   - عرض 5 نتائج مع اسم الموقع
   - النقر على نتيجة ينقل الخريطة ويضع الدبوس

2. **عرض العقارات على الخريطة (في `main.js`):**
   - زر "عرض العقارات على الخريطة" في عناصر التحكم
   - `togglePropertiesOnMap()`: يحمل `offers.json`، يعرض العقارات ذات الإحداثيات الصحيحة
   - كل عقار يُعرض كـ marker مع أيقونة حسب النوع (🌾 مزرعة، 🗺️ أرض، 🏠 فيلا، إلخ)
   - popup يعرض العنوان، المنطقة، السعر، المساحة
   - `fitBounds` لعرض جميع العقارات في إطار واحد
   - إمكانية الإخفاء/الإظهار

---

### المهمة 5: نظام التصنيف

**المتطلبات:** القسم + المنطقة + نوع العقار، استخدامها في عرض العقارات.

**الحل المطبق:**

1. **إضافة حقول التصنيف إلى `offers.json`:**
   - `section`: القسم الرئيسي (مزارع، أراضي، استراحات، فلل، شقق، محلات)
   - `property_type`: نوع العقار التفصيلي (من `category` الموجود)
   - تم تحديث جميع الـ 30 عرضاً (60 حقل جديد)
   - `operation_type`: ضمان وجود قيمة افتراضية (`sale`)

2. **فلتر نوع العقار (في `index.html`):**
   - قائمة منسدلة `#property-type-select` تحت أزرار فلتر القسم
   - خيار "كل أنواع العقارات" + أنواع ديناميكية من العروض

3. **تحديث `main.js`:**
   - `filterByPropertyType(propType)`: دالة فلترة جديدة
   - `updatePropertyTypeFilter()`: يحدّث خيارات القائمة ديناميكياً من العروض المحمّلة
   - `renderOffers(filter, areaFilter, propTypeFilter)`: قبلت معامل ثالث جديد
   - `filterOffers()` و `filterByArea()`: تم تحديثهما لتمرير فلتر نوع العقار
   - الفلترة ثلاثية الأبعاد: القسم + المنطقة + نوع العقار

---

### المهمة 6: نظام الإبلاغ عن الأخطاء

**المتطلبات:** أي مشكلة → `smart_repair.py` + AI Monitor مع تقرير نجاح/فشل.

**الحل المطبق:**

1. **إنشاء `bot/error_reporter.py` (وحدة جديدة):**
   - `report_error(source, error, context, severity, ...)`: يبلّغ عن خطأ إلى:
     - `smart_repair.create_repair_report()` — ينشئ تقرير إصلاح
     - `ai_monitor._save_reports()` — يحفظ في تقارير المراقبة
     - سجل محلي `error_reports.json`
   - `report_success(source, action, details)`: يتتبع العمليات الناجحة
   - `safe_operation`: سياق آمن (context manager) يلتقط الأخطاء تلقائياً
   - `get_error_stats()`: إحصائيات الأخطاء

2. **التكامل مع `bot.py`:**
   - استيراد آمن مع fallback: `try: import error_reporter except: error_reporter = None`
   - خطأ جلب الصور من GitHub → `report_error()` بدرجة `warning`
   - فشل التحقق من النشر → `report_error()` بدرجة `critical`
   - نجاح النشر → `report_success()`

3. **التكامل مع `visitor_api.py`:**
   - استيراد `error_reporter` جاهز للاستخدام في معالجة طلبات الزوار

---

## التحقق من النشر (Deployment Verification)

### GitHub
- ✅ الفرع: `phase4/remaining-tasks` → دمج في `main` عبر PR #8
- ✅ PR: https://github.com/abonasr0907-beep/-/pull/8
- ✅ Commit: `179bccd` → مدمج في `047259d` (main)
- ✅ 10 ملفات معدلة، 949 إضافة، 90 حذف

### Railway
- ✅ URL: https://worker-production-7713.up.railway.app
- ✅ HTTP Status: 200
- ✅ Health Check: `{"ok": true, "status": "running", "bot": "afaq"}`
- ✅ Response Time: 0.278s

### Telegram Webhook
- ✅ Webhook URL: https://worker-production-7713.up.railway.app/bot/...
- ✅ Pending Updates: 0
- ✅ Last Error: None

---

## الملفات المعدلة/الجديدة

| الملف | النوع | الوصف |
|------|------|------|
| `api_server/visitor_api.py` | معدّل | إعادة كتابة `send_telegram_images()` + استيراد `error_reporter` |
| `bot/bot.py` | معدّل | ثوابت الحالات، جلب الصور، التحقق من القسم، الإبلاغ عن الأخطاء |
| `bot/github_sync.py` | معدّل | `fetch_visitor_request_images()` + `download_visitor_image()` |
| `bot/error_reporter.py` | **جديد** | نظام الإبلاغ عن الأخطاء الموحد |
| `index.html` | معدّل | فلتر نوع العقار |
| `js/main.js` | معدّل | البحث على الخريطة، عرض العقارات، التصنيف |
| `list-property.html` | معدّل | مربع البحث + زر عرض العقارات |
| `offers-data/offers.json` | معدّل | حقول `section` + `property_type` |

---

## القيود الملتزم بها

- ✅ **لا تغيير GitHub settings:** لم يتم تغيير أي إعدادات في GitHub
- ✅ **لا تغيير Railway settings:** لم يتم تغيير أي إعدادات في Railway
- ✅ **لا تغيير Telegram settings:** لم يتم تغيير Bot Token أو Webhook
- ✅ **لا تغيير Webhook settings:** Webhook URL unchanged, 0 pending
- ✅ **تحديث تدريجي فقط:** تمت إضافة تحسينات فوق النظام المستقر دون إعادة بناء
- ✅ **لا إعادة اختبار الأنظمة الموجودة:** الأنظمة الـ 8 من Phase 3 تعمل كما هي

---

## الخلاصة

تم إكمال جميع المهام الست المتبقية بنجاح مع الالتزام الكامل بمنهجية التحديث التدريجي. النظام الآن يدعم:

1. **إرسال الصور بكفاءة** — الصور تصل مع أزرار الموافقة/الرفض وتُربط بالعرض المنشور
2. **إدارة الطلبات المتقدمة** — 7 حالات واضحة، لا حذف بعد النشر
3. **تحقق صارم قبل النشر** — التحقق من الوجود + القسم الصحيح
4. **خريطة تفاعلية كاملة** — بحث + عرض العقارات + ضغط/سحب + GPS
5. **تصنيف ثلاثي** — القسم + المنطقة + نوع العقار
6. **إبلاغ موحد عن الأخطاء** — `smart_repair` + `ai_monitor` + سجل محلي

النظام مستقر ومُنشَر على Railway مع التحقق الكامل من التشغيل.
