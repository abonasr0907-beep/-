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
