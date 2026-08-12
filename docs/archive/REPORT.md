# تقرير شامل: إصلاح وتطوير بوت مكتب آفاق الإنجاز العقاري

**التاريخ:** 9 أغسطس 2026  
**المشروع:** مكتب آفاق الإنجاز العقاري — موقع + بوت تيليجرام  
**المستودع:** `abonasr0907-beep/-`  
**رابط الموقع للزوار:** https://abonasr0907-beep.github.io/-/

---

## 1. السبب الجذري للمشكلة (Root Cause)

### المشكلة الأساسية: فقدان حالة رفع الصور

كان بوت تيليجرام يخزن جلسات المستخدمين (`user_sessions`) في قاموس Python في الذاكرة (in-memory dict). عند استضافة البوت على منصات السحابة (Render/Railway) في وضع webhook، يحدث ما يلي:

1. **إعادة التشغيل الباردة (Cold Restart):** المنصات المجانية توقف الخدمة وتعيد تشغيلها دورياً أو عند عدم النشاط. كل إعادة تشغيل تمسح الذاكرة بالكامل.
2. **فقدان الحالة:** بعد مسح الذاكرة، يفقد البوت حالة `state = "awaiting_images"`، فيستجيب للمستخدم برسالة "استخدم زر إضافة عرض جديد أولاً" حتى لو كان في منتصف رفع الصور.
3. **عدم مزامنة الصور:** بما أن الجلسة تُفقد، الصور المرفوعة لا تُربط بالعرض المناسب ولا تصل للموقع.

### الحل المُطبَّق: الطبقة الدائمة (Persistence Layer)

تم إنشاء وحدة `persistence.py` تحفظ جميع الجلسات على القرص في ملف `sessions.json`. كل استدعاء لـ `get_session()` أو `save_session()` يمر عبر هذه الطبقة، مما يضمن بقاء الحالة حتى بعد إعادة تشغيل البوت.

---

## 2. الملفات المُنشأة حديثاً (6 وحدات جديدة)

### 2.1 `bot/persistence.py` — التخزين الدائم للجلسات والمسودات
- يحفظ/يحمّل `user_sessions` من/إلى `bot/data/sessions.json`
- آمن مع العمليات المتزامنة (`threading.Lock`)
- كتابة ذرية (atomic write) عبر ملف مؤقت ثم `replace()`
- **نظام المسودات:** يحفظ العروض غير المكتملة تلقائياً في `drafts.json`
- الدوال: `init()`, `get_session()`, `save_session()`, `reset_session()`, `save_draft()`, `get_draft()`, `has_incomplete_offer()`

### 2.2 `bot/user_manager.py` — نظام متعدد المستخدمين
- الأدوار: `admin` (مدير) و `editor` (محرر)
- الحالات: `active` (نشط) و `suspended` (موقوف)
- يستورد المديرين الحاليين من `config.json` تلقائياً
- **سجل التدقيق (Audit Log):** يسجل كل إضافة/حذف/تعديل للمستخدمين
- الدوال: `add_user()`, `remove_user()`, `is_admin()`, `is_editor()`, `is_authorized()`, `log_audit()`, `get_stats()`
- البيانات في `bot/data/users.json` و `bot/data/audit_log.json`

### 2.3 `bot/offer_id.py` — مولّد معرّفات العروض التسلسلية
- الصيغة: `AFQ-{السنة}-{التسلسل:04d}` (مثل AFQ-2026-0001)
- آمن مع العمليات المتزامنة، العداد محفوظ في `bot/data/offer_counter.json`
- `sync_with_existing_offers()`: يتفقد العروض الموجودة لمنع التكرار
- الدوال: `generate_offer_id()`, `parse_offer_id()`, `get_last_id()`

### 2.4 `bot/image_utils.py` — تحسين وضغط الصور
- تحويل تلقائي إلى **WebP** (جودة 88) أو JPEG (جودة 90)
- تحسين تلقائي: تصحيح الألوان، السطوع، التباين، إزالة الضوضاء، الحدة
- معالجة دوران EXIF عبر `ImageOps.exif_transpose()`
- **كشف التكرار:** عبر SHA256 للمحتوى (يمنع رفع نفس الصورة مرتين)
- توليد أسماء فريدة مرتبطة بمعرّف العرض: `AFQ_2026_0001_0_{timestamp}.webp`
- إنشاء صور مصغرة (thumbnails) بعرض 400px
- الحد الأقصى للعرض: 3840px

### 2.5 `bot/backup.py` — النسخ الاحتياطي التلقائي
- `create_backup(reason)`: ينشئ نسخة قبل النشر أو الحذف
- ينسخ: offers.json, bot_offers.json, visitor_requests.json, office-data.json, news.json, weekly_stats.json, users.json, sessions.json, config.json
- يحتفظ بآخر 20 نسخة فقط (يحذف الأقدم تلقائياً)
- المسار: `bot/data/backups/backup_{timestamp}_{reason}/`

### 2.6 `bot/task_queue.py` — طابور المهام غير المتزامن
- مبني على `asyncio.Queue`، عامل واحد (worker) يعالج المهام بالتسلسل
- يمنع إرهاق الموارد عند العمليات الثقيلة (رفع الصور، المزامنة، تحديث الموقع)
- يتتبع حالة كل مهمة (مكتملة/فاشلة)
- يحتفظ بآخر 50 مهمة في الذاكرة للعرض في لوحة التحكم
- الدوال: `start_worker()`, `enqueue()`, `get_stats()`

---

## 3. التعديلات على الملفات الموجودة

### 3.1 `bot/bot.py` (التعديلات الرئيسية)

| التعديل | الوصف |
|---------|-------|
| **استيراد الوحدات الجديدة** | إضافة استيرادات لـ persistence, task_queue, image_utils, offer_id, backup, user_manager |
| **نظام السجلات** | `log_error()`, `get_recent_errors()`, `log_sync()`, `get_recent_syncs()` لحفظ الأخطاء وعمليات المزامنة |
| **الجلسات الدائمة** | `get_session()` → `persistence.get_session()`، `save_session()` → `persistence.save_session()` — كل التغييرات تُحفظ على القرص |
| **نظام الصلاحيات** | `is_admin()` يفحص `ADMIN_IDS` و `user_manager.is_admin()`، أضيف `is_editor()` و `is_authorized()` |
| **`add_offer_start()`** | يفحص المسودات غير المكتملة ويعرض زر "استئناف" أو "عرض جديد"، يحفظ الجلسة على القرص |
| **`handle_photo()`** | يستخدم الجلسة الدائمة، يحفظ بعد كل صورة، يستدعي `_download_and_enhance_photo()` |
| **`_download_and_enhance_photo()`** | آلية إعادة المحاولة (3 محاولات)، مهلات أطول (60s قراءة)، كشف التكرار عبر SHA256، تحويل WebP، معالجة EXIF |
| **`handle_text_during_add()`** | استُبدل `is_admin` بـ `is_authorized`، حفظ الجلسة بعد كل تغيير حالة |
| **`handle_callback()`** | استُبدل `is_admin` بـ `is_authorized`، أضيف معالجات `resume_draft` و `new_offer_discard` |
| **`_finalize_offer()`** | استُبدل UUID بـ `offer_id.generate_offer_id()`، نسخة احتياطية قبل النشر، منع نشر عرض بدون صور |
| **أوامر جديدة** | `/dashboard`, `/add_user`, `/myid`, `/users`, `/remove_user` |
| **`error_handler()`** | معالج أخطاء شامل يمنع تعطل البوت ويسجل الأخطاء |
| **`main()`** | تهيئة persistence, user_manager, offer_id, error_handler, task_queue عبر `post_init` |

### 3.2 `bot/github_sync.py` (إعادة كتابة)
- **إعادة المحاولة:** 3 محاولات مع تأخير متزايد (exponential backoff)
- **مهلات أطول:** 30s اتصال، 60s قراءة (للتعامل مع الإنترنت الضعيف)
- **سجل المزامنة:** كل عملية رفع تُسجل في `sync_log.json` (نجاح/فشل/تخطي)
- الدالة المساعدة `_retry_request()` للتغليف القياسي

### 3.3 `bot/requirements.txt`
- أضيف `aiofiles>=23.2.1` للكتابة غير المتزامنة للملفات

### 3.4 `bot/config.json`
- أضيفت إعدادات جديدة: `offer_id_prefix`, `image_format`, `image_quality`, `max_image_width`, `thumbnail_width`, `enable_drafts`, `enable_backups`, `max_backups`, `enable_audit_log`, `multi_user`

### 3.5 `render.yaml`
- أضيف **قرص دائم (Disk)** 1GB في `/app/bot/data` لمنع فقدان الجلسات والمسودات والنسخ الاحتياطية

### 3.6 `Dockerfile`
- أضيف `RUN mkdir -p /app/bot/data /app/bot/data/backups` لضمان وجود مجلد البيانات

### 3.7 `.gitignore`
- استُثني ملفات البيانات وقت التشغيل (sessions.json, drafts.json, error_log.json, sync_log.json, offer_counter.json, backups/)
- بقي تتبع users.json و audit_log.json كملفات تهيئة أولية

### 3.8 `sitemap.xml`
- تحديث جميع تواريخ `lastmod` إلى 2026-08-09

### 3.9 `js/main.js`
- دعم صور WebP (المتصفحات الحديثة تدعمها تلقائياً)
- **معرض الصور (Lightbox):** النقر على صورة عرض يفتح المعرض بدقة عالية مع التنقل بالأسهم
- شارة عدد الصور لكل عرض
- `onerror` fallback إلى صورة افتراضية عند فشل تحميل صورة
- `decoding="async"` لتحسين الأداء

### 3.10 `css/style.css`
- أنماط لشارة عدد الصور `.offer-photos-count`
- تأثير تكبير الصورة عند التحويم (hover zoom)

---

## 4. الأوامر الجديدة في البوت

| الأمر | الوصف | الصلاحية |
|-------|-------|----------|
| `/dashboard` | لوحة تحكم: عدد العروض، آخر عرض، طلبات الزوار، حالة البوت، الأخطاء، عمليات المزامنة | مدير |
| `/add_user` | إضافة مستخدم جديد (محرر) — `/add_user USER_ID الاسم editor` | مدير |
| `/myid` | عرض معرّف تيليجرام الخاص بالمستخدم | الكل |
| `/users` | قائمة جميع المستخدمين المصرّح لهم | مدير |
| `/remove_user` | حذف مستخدم — `/remove_user USER_ID` | مدير |

---

## 5. الاختبارات المنجزة

### 5.1 فحص البنية (Syntax Check)
- ✅ جميع ملفات Python الـ 8 تجتاز `py_compile`
- ✅ `js/main.js` يجتاز فحص الصيغة (`node --check`)
- ✅ `sitemap.xml` XML صالح (8 روابط)
- ✅ `render.yaml` YAML صالح
- ✅ `index.html` JSON-LD صالح (schema.org RealEstateAgent)

### 5.2 اختبارات الاستيراد
- ✅ جميع الوحدات الـ 7 (persistence, task_queue, image_utils, offer_id, backup, user_manager, github_sync) تُستورد بنجاح
- ✅ `bot.py` يُستورد بنجاح مع توفر جميع الدوال الـ 19 الأساسية

### 5.3 اختبارات التكامل الوظيفي
- ✅ **persistence:** حفظ/تحميل الجلسة، نظام المسودات، إعادة التعيين
- ✅ **offer_id:** توليد معرّفات تسلسلية فريدة (AFQ-2026-0001, 0002, ...)
- ✅ **user_manager:** التعرّف على المدير من config، إضافة محرر، سجل التدقيق
- ✅ **backup:** إنشاء نسخة احتياطية بنجاح
- ✅ **image_utils:** حساب hash للمحتوى، توليد أسماء فريدة
- ✅ **task_queue:** معالجة المهام غير المتزامنة
- ✅ **github_sync:** تسجيل عمليات المزامنة

---

## 6. القيود المُحترَمة

- ✅ **لم يُغيَّر** توكن البوت (BOT_TOKEN)
- ✅ **لم تُغيَّر** إعدادات GitHub
- ✅ **لم تُغيَّر** إعدادات Railway/Render الأساسية (فقط أضيف قرص دائم)
- ✅ **لم يُعاد بناء** المشروع من الصفر — جميع التعديلات على الكود الموجود
- ✅ **البوت ليس عاماً** — لا يوجد رابط دعوة، الوصول عبر `ADMIN_IDS` و `user_manager` فقط

---

## 7. رابط الموقع للزوار

**https://abonasr0907-beep.github.io/-/**

الموقع يحتوي على:
- الصفحة الرئيسية مع العروض المميزة
- صفحات: المزارع، الاستراحات، الأراضي السكنية، الخدمات
- صفحة التواصل والاستفسارات
- بيانات منظمة schema.org (RealEstateAgent)
- sitemap.xml و robots.txt للفهرسة في Google
- معرض صور تفاعلي (Lightbox)
- دعم صور WebP المحسّنة

---

## 8. خطوات ما بعد النشر

1. **على Render:** بعد النشر، أضف `WEBHOOK_URL` كمتغير بيئة بقيمة رابط الخدمة
2. **قرص البيانات:** تأكد أن قرص 1GB مُفعّل في `/app/bot/data`
3. **Google Search Console:** أرسل `https://abonasr0907-beep.github.io/-/sitemap.xml` لفهرسة أسرع
4. **اختبار البوت:** أرسل `/add` وجرّب رفع صور متعددة، ثم أعد تشغيل البوت وتحقق من استمرار الجلسة
5. **إضافة محرر:** استخدم `/add_user <USER_ID> <الاسم> editor` لإضافة أعضاء جدد
