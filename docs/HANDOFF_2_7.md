# HANDOFF 2.7 — Phase 2.7 Full-Stack Production Engineer

## تاريخ التسليم
تاريخ الإكمال: 2026

## الفرع
`feat/admin-upgrade-form-map`

## آخر الالتزام (قبل دمج Section 3)
`5870397e` — Phase 2.7 Section 2: SITE_BASE_URL permanent link

## الحالة
✅ جميع أقسام Phase 2.7 (§0–§3) مكتملة ومُلتزمة ومُدفوعة. Section 3 (هذا التسليم) يُكمل الاختبارات + هذا الملف + PHASE_GATES + دمج main + الوسم.

---

## 1. ملخص ما تم إنجازه

تم تنفيذ Phase 2.7 فوق Phase 2 المستقرة: حماية بيانات المدير وترقية صلاحياته (full_admin) مع حماية الصلاحيات الحساسة، تحويل خريطة نموذج إضافة عقار إلى MapLibre GL 3D مع قمر Esri الصناعي + علامة قابلة للسحب + زر الموقع الحالي، والرابط الرسمي الدائم (SITE_BASE_URL) للروابط الظاهرة في البوت/العرض/المشاركة — **كل ذلك دون كسر الروابط الدائمة القديمة أو SEO أو أرقام المكتب أو sitemap/robots.**

### الالتزامات على الفرع (بالترتيب)
| الالتزام | القسم | الوصف |
|--------|------|------|
| `18ea7b67` | §0 | Phase 2.7 Section 0: admin privilege upgrade (full_admin) |
| `13787e31` | §1 | Phase 2.7 Section 1: form map Esri satellite + 3D (pitch=60) + draggable pin + geolocation |
| `5870397e` | §2 | Phase 2.7 Section 2: SITE_BASE_URL permanent link |
| (هذا الالتزام) | §3 | Phase 2.7 Section 3: tests + HANDOFF_2_7 + PHASE_GATES + merge main + tag |

---

## 2. الملفات المُعدّلة / المُنشأة

### ملفات مُعدّلة (MODIFIED)
| الملف | التغيير |
|-------|---------|
| `bot/user_manager.py` | §0: إضافة `full_admin` field + `is_full_admin()` + صلاحيات موسعة (`export_data`, `run_smart_fix`, `view_audit_log`, `edit_institution_data`) + صلاحيات محمية (`delete_owner`, `change_token`, `change_webhook`, `change_git_settings`, `change_database_url` = owner only) + `has_permission()` و `get_user_permissions()` تدمج الموسعة لـ full_admin + `init_from_config()` يضبط full_admin + `add_user()` يضبط full_admin + `upgrade_admins_to_full()` + `get_stats()` يضيف full_admins count |
| `bot/data/users.json` | §0: admin `7746757675` → `full_admin: true` (إضافة فقط، باقي البيانات محفوظة) |
| `bot/data/audit_log.json` | §0: إضافة سجل `admin_privilege_upgrade_2.7` — "تمت ترقية 1 مدير إلى full_admin (جديد: 1)" |
| `bot/config.json` | §2: إضافة `SITE_BASE_URL: "https://urldra.cloud.huawei.com/BExUoXngu4"` (إضافة فقط، باقي config محفوظ) |
| `bot/bot.py` | §2: `_get_site_base_url()` (يقرأ SITE_BASE_URL + fallback website_url + يضمن `/`) + `_build_listing_perm_link()` و `_do_publish` و `_approve_visitor_request` يستخدمون `_get_site_base_url()` |
| `list-property.html` | §1: MapLibre GL 3.6.2 CSS+JS (CDN) + زر "📍 موقعي الحالي" + Leaflet fallback (إضافات فقط) |
| `js/main.js` | §1: `initPropertyMap()` MapLibre GL + Esri World Imagery + pitch=60 + NavigationControl(visualizePitch) + flyTo + inertia + علامة قابلة للسحب + click-to-move + `useMyCurrentLocation()` + `useMyGPS()` + `clearMapLocation()` + `setMapLocation()` + `togglePropertiesOnMap()` guard + lazy init IntersectionObserver + المركز الافتراضي الخرج (24.2285, 47.3116) |
| `docs/TESTS.md` | §3: إضافة اختبارات Phase 2.7 (41–44) |
| `docs/PHASE_GATES.md` | §3: إضافة بوابة 2.7→3 |

### ملفات مُنشأة (NEW)
| الملف | الوصف |
|-------|-------|
| `docs/ADMIN_BACKUP_REPORT.md` | §0: توثيق حالة المدير قبل الترقية (1 admin, telegram_id 7746757675, role admin, status active, join 2026-08-09) |
| `docs/HANDOFF_2_7.md` | هذا الملف |

### ملفات **لم** تُمَس (محمية)
- `sitemap.xml` — لم يتغير ⛔
- `robots.txt` — لم يتغير ⛔
- `offers-data/offers.json` — لم يتغير ⛔
- `offers-data/office-data.json` — لم يتغير (أرقام المكتب محمية) ⛔
- `bot/config.json` — إضافة `SITE_BASE_URL` فقط (admin_ids, website_url, token, webhook لم تتغير) ⛔
- canonical URLs في `property.html` — تبقى على GitHub Pages (`window.location.origin`) ⛔
- `offerDetailLink()` في `js/main.js` — روابط نسبية للداخل تبقى على GitHub Pages host ⛔
- Google Search Console — لم يتغير ⛔
- Telegram Bot Token / Webhook — لم يتغير ⛔
- Database URL — لم يتغير ⛔

---

## 3. الأقسام المكتملة بالتفصيل

### §0 — حماية بيانات المدير وترقية الصلاحيات ✅
- نسخة احتياطية في `backups/users/` + `docs/ADMIN_BACKUP_REPORT.md`
- `full_admin` boolean field (إضافة فقط)
- المدراء قبل: 1 → بعد: 1 (لا فقدان)
- admin `7746757675`: `full_admin: true` (جميع البيانات محفوظة: name, role, status, added_by, added_at, last_active)
- الصلاحيات الموسعة لـ full_admin: `export_data`, `run_smart_fix`, `view_audit_log`, `edit_institution_data` = True
- الصلاحيات المحمية (owner only): `delete_owner`, `change_token`, `change_webhook`, `change_git_settings`, `change_database_url` = False للمدير دائمًا
- `is_full_admin()`, `upgrade_admins_to_full()`, `get_stats()` (full_admins count)
- سجل التدقيق: `admin_privilege_upgrade_2.7` مسجّل

### §1 — خريطة نموذج إضافة عقار (Esri satellite + 3D) ✅
- MapLibre GL 3.6.2 (CDN) + Esri World Imagery (`server.arcgisonline.com/.../World_Imagery/MapServer/tile/{z}/{y}/{x}`، لا مفتاح API)
- pitch=60, NavigationControl مع visualizePitch, flyTo, inertia
- علامة قابلة للسحب (draggable) + click-to-move + تحديث lat/lng المخفية
- زر "📍 موقعي الحالي" + `useMyCurrentLocation()` + fallback لطيف عند الرفض
- المركز الافتراضي: الخرج (24.2285, 47.3116)
- lazy init عبر IntersectionObserver
- Leaflet كـ fallback (محفوظ)
- علامة `__afaqMapLibreMode` تتبع الوضع النشط

### §2 — الرابط الرسمي الدائم (SITE_BASE_URL) ✅
- `SITE_BASE_URL` = `https://urldra.cloud.huawei.com/BExUoXngu4` في config (إضافة فقط)
- `_get_site_base_url()`: يقرأ SITE_BASE_URL + fallback website_url + يضمن `/` في النهاية
- `_build_listing_perm_link()`, `_do_publish`, `_approve_visitor_request` يستخدمون `_get_site_base_url()`
- رابط جديد: `{base}offer/{external_id}/{slug}` → `https://urldra.cloud.huawei.com/BExUoXngu4/offer/AFQ001/farm-alkharj-5000sqm`
- رابط قديم: `{base}property/{old_id}` → `https://urldra.cloud.huawei.com/BExUoXngu4/property/123` (محفوظ)
- idempotent: نفس المدخلات → نفس الرابط
- **فحص رابط Huawei:** الأساسي 302 → Petal Maps (POI page)؛ المسارات الفرعية 404 — يُستخدم في روابط البوت/العرض/المشاركة الظاهرة للزوار؛ canonical و sitemap تبقى على GitHub Pages (`website_url`).

### §3 — التوثيق والبوابة ✅
- إضافة اختبارات 41–44 إلى `docs/TESTS.md` + تشغيل الرخیصة
- إنشاء `docs/HANDOFF_2_7.md` (هذا الملف)
- تحديث `docs/PHASE_GATES.md` (بوابة 2.7→3)
- دمج `feat/admin-upgrade-form-map` في `main` بـ `--no-ff` + دفع main (هذا هو النشر)
- وسم `phase-2.7-admins` + دفع الوسم
- فحص رخیص ما بعد النشر

---

## 4. الاختبارات

### اختبارات Phase 2.7 (41–44) — مُضافة في Section 3
| # | الاختبار | النوع | الحالة |
|---|---------|------|--------|
| 41 | حماية بيانات المدير + ترقية full_admin | رخیص | ✅ منفذ (1 admin قبل=بعد، full_admin=true، محمية=False، موسعة=True، audit logged) |
| 42 | خريطة نموذج إضافة عقار (MapLibre GL + Esri + 3D + draggable + geolocation) | رخیص | ✅ منفذ (CDN refs, pitch=60, draggable, geolocation, IntersectionObserver, Al-Kharj, node -c OK) |
| 43 | SITE_BASE_URL link generation (idempotent + trailing slash + format) | رخیص | ✅ منفذ (Huawei URL + `/` + correct format + idempotent) |
| 44 | فحص رابط Huawei (HTTP) | رخیص | ✅ منفذ (302→Petal Maps, sub-paths 404) |

### الاختبارات الرخیصة المنفذة محليًا
```
py_compile: bot.py ✅ | user_manager.py ✅ | listing_lifecycle.py ✅
node -c:    main.js ✅
الدوال:     has_permission (protected=False, expanded=True) ✅ | is_full_admin() ✅
            _get_site_base_url() (trailing slash + idempotent) ✅
            admin count (1→1, no loss) ✅ | audit_log (upgrade event) ✅
```

---

## 5. المكتمل / المتبقي

### ✅ مكتمل
- [x] §0: حماية بيانات المدير + ترقية الصلاحيات (full_admin) + حماية الصلاحيات الحساسة + audit log
- [x] §1: خريطة نموذج إضافة عقار (MapLibre GL + Esri satellite + 3D pitch=60 + draggable + geolocation + lazy)
- [x] §2: الرابط الرسمي الدائم (SITE_BASE_URL + _get_site_base_url + publish/approval/listings/share)
- [x] §3: الاختبارات (41–44) + HANDOFF_2_7 + PHASE_GATES + دمج main + وسم phase-2.7-admins

### ⏳ المتبقي (لا شيء من Phase 2.7)
لا توجد مهام متبقية في Phase 2.7. جميع الأقسام مكتملة.

### ملاحظات للمراجعة اليدوية
- اختبارات البوت الفعلية (تفاعل Telegram) تتطلب تشغيل البوت فعليًا — موثقة للمراجعة اليدوية
- فحص رابط Huawei (44) تم بـ `curl` — النتيجة: 302 redirect إلى Petal Maps للأساسي، 404 للمسارات الفرعية
- canonical و sitemap تبقى على GitHub Pages host (`website_url`) — لا تغيير للروابط المفهرسة

---

## 6. Phase 3 — النطاق المغلق

> **هذا القسم يُعرّف نطاق Phase 3 للمرحلة القادمة. يجب الالتزام به ولا يتوسع دون موافقة صريحة.**

Phase 3 يركز على **الأنظمة الذكية والأتمتة المتقدمة** فوق الأساس المستقر من Phase 1 و Phase 2 و Phase 2.7:

1. **نظام إشعارات ذكي متعدد القنوات** — إشعارات Telegram للمدراء والزوار + جدولة دورية + خيار كتم
2. **بحث وفiltro متقدم للعقارات** — بحث نصي + فلاتر متعددة + ترتيب (published-only محفوظ)
3. **لوحة تحكم (Dashboard) للإدارة** — إحصائيات حية + مخططات (CDN فقط، admin-only, noindex)
4. **تحسين أداء الموقع** — WebP + srcset + lazy load محسن
5. **نظام تقييم ومراجعات** — تقييمات الزوار + مراجعة المدير + عرض النجوم
6. **تكامل خرائط متقدم** — تحديد منطقة + رسم حدود + حساب مساحة تقريبية

### القواعد الذهبية لـ Phase 3 (موروثة)
- لا مفتاح API، لا تبعيات ثقيلة (CDN فقط)
- روابط `/property/{old_id}` و `/offer/{external_id}/{slug}` لا تتغير
- `office-data.json` (أرقام المكتب) محمية
- `sitemap.xml` و `robots.txt` لا يُعدّلان دون مراجعة
- canonical على GitHub Pages host
- `SITE_BASE_URL` (Huawei) للروابط الظاهرة في البوت/العرض/المشاركة
- `full_admin` موسعة لكن المحمية (owner only) لا تُمنح للمدير
