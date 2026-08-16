# Phase Gates — بوابات المراحل وتقارير الحوادث

> **المرحلة:** Phase 2 §4
> **الهدف:** تعريف بوابات العبور بين المراحل + قالب تقرير الحوادث عند كسر قاعدة.

---

## 1. بوابة Phase 1 → Phase 2

تم العبور بنجاح:
- [x] دمج `feat/bot-manager-publish-lifecycle` إلى `main` (merge --no-ff)
- [x] وسم `phase-1-stable` + دفع الوسم
- [x] اختبارات Phase 1 الـ 12 في `docs/TESTS.md` — كلها منفذة
- [x] `bot/bot.py` + `user_manager.py` + `listing_lifecycle.py` تُترجم بـ `py_compile`
- [x] نسخة احتياطية محلية `backups/` (مُضافة لـ .gitignore)
- [x] `docs/HANDOFF_1.md` مقروء ومفهوم

---

## 2. بوابة Phase 2 → Phase 3

### متطلبات العبور:
- [x] كل أقسام Phase 2 (§1–§5) مكتملة ومُلتزمة ومُدفوعة
- [x] اختبارات Phase 2 مُضافة لـ `docs/TESTS.md` ومنفذة
- [x] `docs/HANDOFF_2.md` يحتوي: الفرع، آخر التزام، المكتمل/المتبقي، Phase 3 Locked Scope
- [x] دمج `feat/site-auction-map` إلى `main` (merge --no-ff) + دفع main
- [x] وسم `phase-2-stable` + دفع الوسم
- [x] فحص ما بعد النشر: الصفحة الرئيسية + صفحة عقار = 200، رابط `/offer/` يعمل، ≥1 صورة

### بوابات الحراسة (Guardrails):
- [x] `docs/SEO_GUARDRAILS.md` موجود ومُتبع
- [x] درجة الجودة `quality_score()` تعمل (تحذير فقط)
- [x] كشف التكرار `find_duplicates()` يعمل (تحذير فقط)
- [x] ALT تلقائي للصور يعمل
- [x] الروابط القديمة `/property/{old_id}` لا تزال تعمل
- [x] أرقام المكتب في `office-data.json` لم تتغير
- [x] لا مفاتيح API، لا تبعيات ثقيلة (الخريطة CDN فقط)

---

 قالب تقرير الحادث (Incident Report Template)

عند كسر أي قاعدة في `SEO_GUARDRAILS.md` أو أي بوابة أعلاه، أنشئ تقريرًا فوريًا:

```markdown
## Incident Report — {YYYY-MM-DD HH:MM}

**المرحلة:** Phase X §Y
**القاعدة المكسورة:** {رقم/عنوان القاعدة من SEO_GUARDRAILS.md}
**الخطورة:** منخفضة / متوسطة / عالية / حرجة
**اكتشفها:** {اسم/معرّف}
**وقت الاكتشاف:** {تاريخ}

### الوصف
{وصف موجز لما حدث}

### الأثر
{ما تأثر: روابط مُفهرَسة، SEO، بيانات، أرقام مكتب، إلخ}

### السبب الجذري
{لماذا حدث — تحليل}

### الإجراء الفوري
{ما تم فعله فورًا للحد من الضرر}

### الإجراء التصحيحي
{ما سيتم فعله لمنع التكرار — كود/عملية/مراجعة}

### الحالة
مفتوح / قيد المعالجة / مغلق

### التحقق
{كيف تأكدنا أن الإصلاح يعمل}
```

### أمثلة على حوادث تتطلب تقريرًا:
1. **رابط `/property/{id}` يعطي 404** — حرجة (يؤثر روابط مُفهرَسة)
2. **تغيير أرقام المكتب في `office-data.json`** — حرجة (بيانات اتصال رسمية)
3. **مفتاح API مُضاف للكود** — عالية (انتهاك بروتوكول الائتمان)
4. **`robots.txt` عُدِّل دون مراجعة** — عالية
5. **صورة بدون alt على صفحة منشورة** — متوسطة
6. **عرض مكرر نُشر دون فحص** — منخفضة (تنبيه فقط)

---

## 3. بوابة Phase 2.7 → Phase 3

### متطلبات العبور:
- [x] جميع أقسام Phase 2.7 (§0–§3) مكتملة ومُلتزمة ومُدفوعة
- [x] اختبارات Phase 2.7 (41–44) مُضافة إلى `docs/TESTS.md` ومنفذة (رخیصة)
- [x] `docs/HANDOFF_2_7.md` يحتوي: الفرع، آخر التزام، المكتمل/المتبقي، فحص رابط Huawei
- [x] دمج `feat/admin-upgrade-form-map` إلى `main` (merge --no-ff) + دفع main
- [x] وسم `phase-2.7-admins` + دفع الوسم
- [x] فحص رخیص ما بعد النشر: الصفحة الرئيسية + نموذج إضافة عقار له الخريطة الجديدة + رابط عقار منشور بالتنسيق الجديد + البوت /managers يظهر الصلاحيات المرقاة

### بوابات الحارس (Guardrails) — Phase 2.7:
- [x] `full_admin` موسعة لكن الصلاحيات المحمية (delete_owner, change_token, change_webhook, change_git_settings, change_database_url) = owner only
- [x] عدد المدراء قبل = بعد (لا فقدان)
- [x] `SITE_BASE_URL` (Huawei) للروابط الظاهرة في البوت/العرض/المشاركة
- [x] canonical و sitemap تبقى على GitHub Pages (`website_url`) — لا تغيير للروابط المفهرسة
- [x] `sitemap.xml` و `robots.txt` لم يتغيرا
- [x] أرقام المكتب في `office-data.json` لم تتغير
- [x] لا مفتاح API، لا تبعيات ثقيلة (MapLibre GL + Esri CDN فقط)
- [x] روابط `/property/{old_id}` و `/offer/{external_id}/{slug}` محفوظة (نسبية على GitHub Pages)

### فحص رابط Huawei (موثق):
- الأساسي `https://urldra.cloud.huawei.com/BExUoXngu4` → 302 redirect إلى Petal Maps (POI page)
- المسارات الفرعية (مثل `/offer/test/test-slug`) → 404
- **القرار:** يُستخدم `SITE_BASE_URL` في روابط البوت/العرض/المشاركة الظاهرة للزوار؛ canonical و sitemap تبقى على GitHub Pages host.

---

## 4. سجل الحوادث

> تُسجل الحوادث هنا بتسلسل زمني. "لا حوادث" = نظافة كاملة.

| التاريخ | المرحلة | الخطورة | الحالة | الملخص |
|---------|---------|---------|--------|--------|
| — | — | — | — | لا حوادث حتى الآن في Phase 2 |
| 2025-01-15 | Phase 2.8 | منخفضة | مغلقة | visitor_requests.json حُذف في اختبار محاكاة ثم استُرجع فورًا (add-only محفوظ) |

---

## 3. بوابة Phase 2.8 — hotfix النشر والتحقق

تم العبور بنجاح:
- [x] `offer["status"] = "published"` في `_finalize_offer` + `_approve_visitor_request`
- [x] `_handle_attach_deep_link` + توجيه `attach_` في `start()` + فرع `v_awaiting_images`
- [x] `form-success` div في `list-property.html` + حقن زر `attach_` في `main.js`
- [x] `py_compile bot/bot.py` ✅ + `node --check js/main.js` ✅
- [x] `visitor_requests.json` محفوظ (add-only)
- [x] دمج `feat/publish-verification-hotfix` إلى `main` (merge --no-ff) + دفع main
- [x] وسم `phase-2.8-hotfix` + دفع الوسم
- [x] `docs/HANDOFF_2_8.md` مكتمل

---

## 5. قاعدة التوقف الآمن

إذا اقتربت الجلسة من النفاد:
1. التزم آخر تغيير وادفعه فورًا.
2. حدّث `docs/HANDOFF_2.md` بقسم "المكتمل/المتبقي".
3. لا تترك عملًا غير مُلتزم (uncommitted).
4. سجّل الخطوة التالية بوضوح للمهندس التالي.

---

## Phase 3 §1 — التطبيع + القوائم البيضاء + حرّاس الارتداد (بُوابة تثبيت)

**التاريخ:** جلسة المرحلة الثالثة
**الفرع:** `feat/phase3-normalizer-bounce-guard`
**دمج main:** `ff001d34` (merge --no-ff)
**آخر commit على الفرع:** `c5bc64bc`

### العناصر المُنجَزة
- [x] `bot/normalizer.py` — مُطبِّع نصوص عربي idempotent (أرقام، أحرف، مسافات) + قائمة بيضاء للفئات (مزرعة/استراحة/أرض سكنية) + قائمة بيضاء للمناطق (5 مناطق) — 11/11 اختبار ذاتي ✅
- [x] `bot/bounce_guard.py` — حارس ارتداد: `_ensure_published` (idempotent)، `run_bounce_guard`، `fix_now`، `run_automatic_check`، `init_ref_count`، `verify_js_published_filter` — كل الاختبارات الذاتية ✅
- [x] `bot/bot.py` — استيراد normalizer + bounce_guard، استدعاء `normalize_offer()` في `_finalize_offer` + `_approve_visitor_request`، أمر `/fix` للإدارة، `_bounce_guard_auto_check` (كل 6 ساعات عبر JobQueue)
- [x] `js/main.js` — مرآة JS: `normalizeTextJS`، `normalizeCategoryJS`، `normalizeAreaJS`، `isKnownCategoryJS`، `shouldIncludeInAllSectionsJS` + حارس فلتر `propTypeFilter` يستخدم `normalizeCategoryJS` لمطابقة المرادفات
- [x] `offers-data/offers.json` — إضافة `status:"published"` + `publish_status:"Published"` لكل العروض (add-only، لم تُحذف بيانات)
- [x] `bot/data/bounce_guard_log.json` + `bot/data/manager_offer_refcount.json` — ملفات تتبُّع حارس الارتداد

### بُوابة التثبيت (Gate)
- [x] `py_compile bot/bot.py bot/normalizer.py bot/bounce_guard.py` ✅
- [x] `node --check js/main.js` ✅
- [x] عدد العروض: 27 (لم ينخفض — add-only) ✅
- [x] كل العروض `status=published` ✅
- [x] الفرع مُدمَج `--no-ff` إلى `main` + دفع `main` ✅
- [x] commit على الفرع موجود في remote ✅

**النتيجة:** بُوابة مَعْبُورة ✅

---

## Phase 3 §2 — SEO + Schema + Sitemap + IndexNow + Reviews (بُوابة تثبيت)

**الفرع:** `feat/phase3-seo-engine`
**دمج main:** `88d7b744` (merge --no-ff)
**آخر commit على الفرع:** `115d1afd`

### العناصر المُنجَزة
- [x] §2.1 `ai_system/seo_engine/` — محرك SEO كامل (schema_generator + meta_generator + sitemap_updater + indexnow + reviews)
- [x] §2.2 `meta_generator.py` — توليد Title/Meta/ALT/canonical/og/twitter/keywords (idempotent)
- [x] §2.3 `schema_generator.py` — Schema types: Organization + RealEstateAgent + RealEstateListing + Offer + ImageObject + BreadcrumbList + FAQPage + Article (كلها idempotent)
- [x] §2.4 `css/luxury.css` — هوية فاخرة: متغيرات داكن/ذهبي، خط عربي فاخر (Reem Kufi + Amiri)، Hero بصورة قمر صناعي + عبارة قوية + CTA واتساب، Footer NAP، بطاقات عرض فاخرة، أزرار مفضلة
- [x] §2.5 `sitemap_updater.py` — تحديث sitemap.xml (إضافة فقط): 27 رابط عرض جديد (19→46)، robots.txt: noindex على forms/thanks/filter-results
- [x] §2.6 `indexnow.py` — مفتاح IndexNow في جذر الموقع + POST لمحركات البحث عند النشر + سجل (log) — تم اختبار إرسال ناجح لـ Bing
- [x] §2.7 `reviews.py` — مراجعات شرعية فقط: pending → موافقة المدير → approved → AggregateRating من المعتمدة فقط
- [x] `bot/bot.py` — استيراد محرك SEO + تشغيل sitemap update + IndexNow فورًا بعد نشر عرض في `_finalize_offer`
- [x] noindex على list-property.html + inquiry.html + contact.html (forms/thanks)

### بُوابة التثبيت (Gate)
- [x] `py_compile` (bot/bot.py + 6 ملفات seo_engine) ✅
- [x] `node --check js/main.js` ✅
- [x] عدد العروض: 27 (لم ينخفض — add-only) ✅
- [x] sitemap.xml: 46 رابط (من 19 — إضافة فقط) ✅
- [x] robots.txt: 28 Allow + 6 Disallow (إضافة فقط) ✅
- [x] 3 صفحات forms بـ noindex ✅
- [x] مفتاح IndexNow موجود في جذر الموقع ✅
- [x] الفرع مُدمَج `--no-ff` إلى `main` + دفع `main` ✅

**النتيجة:** بُوابة مَعْبُورة ✅

---

## Phase 3 §3 — Hierarchical Silo + Luxury Property ✅ GATE PASSED
- **Commit:** 19342b44 (feat/phase3-silo-hubs) → merged --no-ff → main af9f6874
- **6 hub pages:** categories.html, areas.html, guides.html, why-us.html, faq.html, compare.html — all with SEO meta + OG/Twitter + canonical + BreadcrumbList Schema (via breadcrumb-schema-data + silo.js injectBreadcrumbSchema)
- **Nav hierarchy:** updated in all 9 existing pages + property.html (main-nav) — added الأقسام/المناطق/أدلة عقارية/لماذا نحن/الأسئلة الشائعة/مقارنة العقارات (add-only, no links removed)
- **Stats bar + Trust bar + Afaq exclusives bar** (featured=true only) on hub pages via silo.js
- **Luxury property page:** facts grid, QR code (api.qrserver.com), share (navigator.share/clipboard), ❤ favorites (localStorage), ➕ compare (localStorage + drawer), 📅 appointment (wa.me deep-link), 🖨 PDF (window.print) — window.currentProperty = offer added (1 line)
- **Intra-silo links** section on all hub pages
- **Gate checks:** py_compile ✅ | node --check main.js+silo.js ✅ | 27 offers unchanged ✅

---

## بوابة الجزء 0 — إنعاش البوت (hotfix: worker crash)
- **التاريخ:** $(date -u +%Y-%m-%dT%H:%M:%SZ)
- **السبب:** `logger` استُخدم في كتل except للاستيرادات (سطور 60/76/83/98/101) قبل تعريفه عند السطر 193 → NameError مزدوج → Crash في Railway worker.
- **الإصلاح الجراحي:** نقل `logging.basicConfig` + `logger = logging.getLogger("afaq_bot")` لأعلى الملف بعد الاستيرادات مباشرة (السطر 39-43)، واستبدال `logger.warning` بـ `print` في except الخاص بمحرك SEO احتياطًا، وإزالة التهيئة المكررة القديمة.
- **التحقق:** `py_compile bot/bot.py` ✅ نظيف | `git log origin/main -1` = `3e0e924d hotfix: define logger before SEO import (worker crash)` ✅
- **النشر:** push إلى main فقط — Railway سيقلع وحده تلقائيًا.

---

## بوابة الجزء 1 — حارس شامل + إحياء الأوامر والأزرار
- **الحارس الشامل:** `error_handler` مسجل عبر `app.add_error_handler` (PTB v20 يلتقط كل استثناءات الـ handlers تلقائيًا). حُدّث قسم الأخطاء غير المتوقعة ليرسل تنبيهًا نصيًا فوريًا للمالك/المدراء (get_staff_for_notifications + ADMIN_IDS) بدل صمت البوت — يتضمن النوع والرسالة والمستخدم وآخر سطر من الـ traceback.
- **إحياء الأوامر والأزرار:** الكسر الجذري كان الـ worker crash (الجزء 0) الذي أسقط كل شيء. بعد الإنعاش: `add_offer_start` (إضافة عرض) ✅، `handle_callback` (أزرار الكيبورد) ✅، `cmd_listings` (/listings) ✅، `cmd_pending_listings` (/pending) ✅، معالجات الموافقات (vreq_approve_/vreq_reject_) ✅ — كلها سليمة بنيويًا ولم تُعَد كتابتها (تعديل جراحي فقط).
- **التحقق:** `py_compile bot/bot.py` ✅ | فحص AST: كل المعالجات الحرجة موجودة (162 دالة) ✅

## وسم hotfix-bot-flows — إحياء البوت + حارس + استقبال صامت
- **التحقق من الثلاثة آثار:** (أ) logger معرّف قبل استيراد SEO ✅ | (ب) `_handle_ingest_api` + تسجيل مسار `/ingest` بهيدر `X-Ingest-Secret` (أُضيف جراحيًا في كلا خادمَي aiohttp) ✅ | (ج) `error_handler` يرسل تنبيهًا نصيًا للمالك/المدراء ✅
- **الوسم:** `hotfix-bot-flows` أُنشئ على رأس main الحالي ودُفع إلى origin.
- **التحقق:** `py_compile bot/bot.py` ✅

## جزء 0.2 — جسر الإرسال /ingest + تطهير تيليجرام من واجهات الزوار
- **compressImage:** canvas بأقصى بُعد 1280px وجودة 0.8 (JPEG) + compressImages + postToIngest بهيدر `X-Ingest-Secret` (يطابق `ingest_secret` في bot/config.json) في js/main.js.
- **submitPropertyForm:** ضغط الصور قبل الإرسال؛ نموذج المزايدة: إرسال عبر `/ingest` بدل notifyTelegramAdmin.
- **التطهير:** إزالة زر إرفاق البوت من list-property.html + رسالة النجاح، حذف showBidSuccessModal وكل deep-link t.me من main.js و property.html — الظاهر للزائر واتساب/هاتف فقط.
- **التحقق:** `node --check js/main.js` ✅ | grep: لا form-success-attach/showBidSuccessModal/t.me في واجهات الزوار ✅

---

## Phase 3 Final — بوابة الإغلاق النهائية M4 ✅ GATE PASSED
- **الوسم النهائي:** `phase-3-final`
- **حالة العروض:** 27 عرضاً ثابتاً في `offers.json`.
- **التحقق البنيوي والذاتي:** `py_compile` لجميع ملفات البوت والـ Guardian ✅ | `node --check` لجميع ملفات JS ✅ | فحص grep لسرية البوت نظيف 100% ✅.

---

## بوابة المهمة M1 — أساس الحالة + البوابة + طبقة الرواج 1
- **الفرع:** `mission/m1-foundation`
- **الحالة:** مكتملة واجتازت كافة الاختبارات ✅
- **التحقق البنيوي والعملي:**
  - [x] `py_compile bot/bot.py` ✅
  - [x] `node --check js/main.js` و `node --check js/silo.js` ✅
  - [x] عدد العروض في `offers.json` = 27 ✅
  - [x] إنشاء `docs/STATE.md` كمصدر ثابت وتحديث حالة M1 ✅

---

## بوابة المهمة M6 — تحسين الواجهات وUI الفاخر وحسابات البوصلة
- **الفرع:** `mission/m6-ui`
- **الحالة:** مكتملة واجتازت كافة الفحوصات البنيوية والتقنية ✅
- **العناصر المنفذة:**
  - [x] إصلاح تراكب الشريط الهيدر وتكبير الشعار والهوية ورفع الخط الأساسي إلى 17px وضبط شبكة العروض 3-4/2.
  - [x] أزرار البطاقة المصغرة المدمجة ومودال حجز المعاينة الفوري (POST /ingest + wa.me).
  - [x] المقارنة الشاملة حتى 4 عقارات، قسمان بمتوسط البوصلة وبالسعر المحدد، ختم التحديث اليومي، وإخلاء المسؤولية المالية.
  - [x] عرض 4 أدلة وأخبار السوق مع النسخ الاحتياطية وتوحيد خط العناوين (Reem Kufi).
  - [x] القائمة الجانبية: إغلاق فور اللمس خارجها، رابط الأخبار، والأيقونات المشروطة (X، تيك توك، قناة واتساب).
  - [x] جولات الفيديو: زر جولة فيديو بالتحميل الكسول لـ iframe يوتيوب ومودال إغلاق نظيف.
  - [x] SEO المحلي والتقني: 3 صفحات أحياء، google-site-verification، توسيع LocalBusiness schema، تنظيف canonical، NewsArticle/FAQ schemas، WebP picture fallback، 404 الذكية، الأكثر مشاهدة هذا الأسبوع، وhreflang en.
- **التحقق البنيوي:**
  - [x] `node --check js/main.js` و `node --check js/silo.js` ✅
  - [x] فحص العروض بـ offers.json ✅

---

## بوابة المهمة M7 — إغلاق قنوات النشر والصلاحيات ذاتيًا
- **الفرع:** `mission/m7-publish`
- **الحالة:** مكتملة واجتازت كافة الفحوصات البنيوية والتقنية ✅
- **العناصر المنفذة:**
  - [x] زرع OWNER_ID (7746757675) في `data/managers.json` و `office-data.json` و `config.json` و `users.json` بدور `owner` دائم.
  - [x] إضافة القاعدة الاحتياطية المباشرة بالكود لمعاملة OWNER_ID كمالك كامل الصلاحيات تحت كل الظروف.
  - [x] إضافة زر "🎬 استوديو التسويق" والقائمة الفرعية (إدارة الجولات وروابط يوتيوب، سكريبت ريلز، تجديد الأخبار، رابط التقييم، ونص النشرة).
  - [x] إضافة مسار GET `/api/properties/map` لإعادة بيانات العروض دون أسرار حلًا لـ 404.
  - [x] توثيق مسار النشر التلقائي عبر GitHub Pages في `docs/STATE.md`.
- **التحقق البنيوي:**
  - [x] `py_compile bot/bot.py bot/user_manager.py api_server/visitor_api.py` ✅
  - [x] `node --check js/main.js` و `node --check js/silo.js` ✅

---

## بوابة المهمة M15 — النمو والفهرسة والإعلانات الخجولة والتنظيف (M15 Growth)
- **الفرع:** `mission/m15-growth`
- **وسم المرحلة:** `m15-growth`
- **الحالة:** مكتملة واجتازت كافة الفحوصات البنيوية والتقنية ✅
- **العناصر المنفذة:**
  - [x] جرد وتنظيف المستودع وسجلات وحذف الفروع المدموجة القديمة بأمان.
  - [x] نظام الإعلانات الخجولة (data/ads.json schema, js/ads.js, css/ads.css, #ad-home, #ad-detail, معالج البوت للمالك "📢 إدارة الإعلانات").
  - [x] الفهرسة والهوية: favicon.ico + PNG 192/512 + apple-touch، canonical و og:url مطلقة على GitHub Pages،Schemas (Organization, WebSite, LocalBusiness)، إعادة توليد sitemap.xml بـ 56 رابطاً، وتحديث robots.txt مع فتحة google-site-verification.
- **التحقق البنيوي:**
  - [x] `py_compile bot/bot.py` ✅
  - [x] `node --check js/ads.js` و `node --check js/main.js` و `node --check js/silo.js` ✅
  - [x] فحص XML لسلاسل sitemap.xml ✅
  - [x] فحص grep لغياب أي Huawei canonical قديم وجودة favicons وسرية البوت ✅
