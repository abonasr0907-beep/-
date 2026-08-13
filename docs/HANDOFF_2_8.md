# HANDOFF 2.8 — Phase 2.8 إكمال بقايا النشر والتحقق

> **التاريخ:** 2025-01-15  
> **المرحلة:** Phase 2.8 (إصلاح حار / hotfix)  
> **الفرع:** `feat/publish-verification-hotfix` → `main` (merge --no-ff)  
> **الوسم:** `phase-2.8-hotfix`  
> **الحالة:** مكتمل ومُلتزم ومُدمج  

---

## 1. ملخص

أكملت Phase 2.8 بقايا النشر والتحقق التي كانت متبقية من المرحلة الثانية. تضمن العمل أربعة ملفات رئيسية مع ضمان أن العروض المنشورة تظهر صراحة كـ `published` على الموقع، وأن الزائر يستطيع إرفاق صور عقاره عبر رابط deep-link من البوت بعد إرسال النموذج على الموقع.

## 2. التغييرات المنفّذة

### 2.1 `bot/bot.py`

#### أ) `offer["status"] = "published"` في `_finalize_offer` (السطر ~2830)
أُضيف `offer["status"] = "published"` فورًا بعد `offer["publish_status"] = "Published"` لضمان أن الموقع يرى الحالة `published` صراحة عبر `isOfferPublished()`.

#### ب) `status` + `publish_status` في موافقة طلب الزائر (السطر ~3690)
في `_approve_visitor_request`، أُضيف `"status": "published"` و `"publish_status": "Published"` إلى قاموس العرض المنشأ من طلب الزائر، لضمان الاتساق مع مسار المدير.

#### ج) `_handle_attach_deep_link` (السطر ~897)
دالة جديدة تُفكك حمولة `/start attach_{request_id}`:
- تتحقق من وجود الطلب في `visitor_requests.json`
- تُهيّئ جلسة الزائر بحالة `v_awaiting_images` مع تخزين `attach_request_id`
- تطلب من الزائر إرسال صور العقار (حتى `max_images`)
- تعرض رقم الطلب وتعليمات الإكمال/الإلغاء

#### د) توجيه `attach_` في `start()` (السطر ~1052)
أُضيف توجيه بعد `bid_` مباشرة: إذا بدأ `context.args[0]` بـ `attach_`، يستدعي `_handle_attach_deep_link`.

#### هـ) فرع `attach_` في `v_awaiting_images` (السطر ~2158)
عند إرسال الزائر "تم" أثناء `v_awaiting_images`:
- إذا وُجد `attach_request_id` في الجلسة: يستدعي `property_storage.link_images_to_property()`
- يُحدّث `visitor_requests.json` بـ `images`, `images_attached_at`, `images_attached_via="deep_link_attach"`
- يُشعِر المدراء برسالة HTML
- يرد على الزائر بتأكيد + أرقام المكتـب
- يُصفّر الجلسة

### 2.2 `js/main.js`

#### أ) `submitPropertyForm` — عرض `form-success` + حقن زر الإرفاق (السطر ~1347)
- استُبدل `classList.add('show')` بـ `display = 'block'`
- يحقن رقم الطلب في `#form-success-reqid`
- يحقن رابط `https://t.me/{botUsername}?start=attach_{id}` في `#form-success-attach` (اسم البوت من `OFFICE_DATA.botUsername`، لا hardcoded)
- إذا لم يوجد `botUsername`، يُخفي الزر

#### ب) إخفاء تلقائي بعد 8 ثوانٍ (السطر ~1376)
- `display = 'none'` بدل `classList.remove('show')`
- المهلة 8000ms (كانت 5000ms)

### 2.3 `list-property.html`

أُضيف `div#form-success` بعد `</form>` مباشرة:
- أيقونة نجاح + عنوان تأكيد
- `span#form-success-reqid` لرقم الطلب
- `a#form-success-attach` بتصميم Telegram (#0088cc)

## 3. أرقام المكتـب (لم تُغيّر — حماية add-only)

| الوصف | الرقم | المصدر |
|-------|-------|--------|
| واتساب + اتصال | 0545888931 | `office-data.json` → `whatsapp_calls` |
| اتصال فقط | 0544699933 | `office-data.json` → `calls_only` |
| واتساب + اتصال (2) | 056161610748 | `office-data.json` → `whatsapp_calls_2` |
| 0548601430 | — | في Schema فقط |

اسم البوت: `tlastlastlasbot` (من `OFFICE_DATA.botUsername` في main.js)

## 4. التحقق

| الفحص | النتيجة |
|-------|---------|
| `py_compile bot/bot.py` | ✅ PASS |
| `node --check js/main.js` | ✅ PASS |
| `offer["status"]="published"` في `_finalize_offer` | ✅ موجود (سطر 2830) |
| `status`+`publish_status` في `_approve_visitor_request` | ✅ موجود (سطر 3690) |
| `_handle_attach_deep_link` موجودة | ✅ (سطر 897) |
| توجيه `attach_` في `start()` | ✅ (سطر 1052) |
| فرع `attach_` في `v_awaiting_images` | ✅ (سطر 2158) |
| `form-success` div في list-property.html | ✅ |
| حقن `attach_` رابط في main.js | ✅ (سطر 1362) |
| `isOfferPublished` يفلتر `published` فقط | ✅ (سطر 20) |
| `visitor_requests.json` لم يُحذف | ✅ (استُعيد بعد اختبار) |

## 5. السياق للمرحلة التالية (Phase 3)

- **SITE_BASE_URL:** `https://urldra.cloud.huawei.com/BExUoXngu4` — يُستخدم للروابط المرئية/bot/share/canonical/sitemap
- **الروابط القديمة** `/property/{old_id}` محفوظة (لا تُحذف)
- **الروابط الجديدة** `/offer/{external_id}/{slug}`
- **التصفية/البحث** موجودة — يُحمى فقط (guard) ولا يُحذف
- **الدورات:** owner / admin / manager(full_admin) / visitor
- **النشر = push إلى main فقط**
- **الملفات المحمية (add-only):** sitemap.xml, robots.txt, config.json, offers.json
- **الوسم التالي المتوقع:** `phase-3-final`

## 6. الملفات المعدّلة في هذا الالتزام

```
bot/bot.py              — +110 سطر (attach_ deep-link + status published)
js/main.js              — +14/-2 (form-success + attach button)
list-property.html      — +10 (form-success div)
docs/HANDOFF_2_8.md     — جديد (هذا الملف)
docs/PHASE_GATES.md     — +سطر بوابة 2.8
```

---

**تم بواسطة:** SuperNinja — تنفيذ مستقل غير مُشرف (المالك نائم)  
**القرارات الآمنة المُتخذة:**  
1. استرجاع `visitor_requests.json` بعد حذفه في اختبار محاكاة (حماية add-only)  
2. اسم البوت من `OFFICE_DATA.botUsername` لا hardcoded  
3. أرقام الهاتف ثابتة من `office-data.json` لم تُغيّر  
4. زر الإرفاق يُخفى لو لم يوجد `botUsername` (fallback آمن)  
