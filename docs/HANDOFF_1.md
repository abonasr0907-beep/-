# HANDOFF 1 — Bot & Listing Lifecycle (Ninja 1)

## تاريخ التسليم
تاريخ الإكمال: ٢٠٢٥

## الفرع
`feat/bot-manager-publish-lifecycle`

## الحالة
✅ جميع المهام (Phases 0-10) مكتملة. **لا تدمج في main حتى تجتاز جميع اختبارات docs/TESTS.md.**

---

## ١. ملخص ما تم إنجازه

تم تنفيذ نظام كامل لإدارة دورة حياة العقارات مع أدوار جديدة (owner/manager/visitor)، نشر مباشر للمدير، اعتماد عروض الزوار، تخزين دائم للصور، روابط دائمة، ونصوص تسويقية — **كل ذلك دون كسر الموقع أو SEO أو الروابط المفهرسة.**

---

## ٢. الملفات المُعدّلة / المُنشأة

### ملفات مُعدّلة (MODIFIED)
| الملف | التغيير |
|-------|---------|
| `bot/user_manager.py` | إضافة أدوار owner/manager/visitor، صلاحيات listing lifecycle، دوال مساعدة (is_owner, is_manager, can_*) |
| `bot/bot.py` | Phase 2: أوامر /add_manager /remove_manager /managers. Phase 4: تكامل listing_lifecycle في مسارات النشر. Phase 5/6/7: /listings /view_listing /pending، عرض العقار+الصور، روابط دائمة، تعديل النص، نص تسويقي |
| `property.html` | Phase 8: دعم /offer/{external_id}، findOfferByExternalId، isOfferVisible (إخفاء pending)، canonical URL جديد |
| `404.html` | Phase 8: توجيه /offer/{external_id} إلى property.html?offer={eid} |

### ملفات مُنشأة (NEW)
| الملف | الوصف |
|-------|-------|
| `bot/listing_lifecycle.py` | وحدة إدارة دورة حياة العقارات (707 سطر): تخزين JSON، backfill، صور، تدقيق |
| `docs/TESTS.md` | توثيق ١٢ اختبار إلزامي |
| `docs/HANDOFF_1.md` | هذا الملف |

### ملفات بيانات جديدة (تُنشأ وقت التشغيل)
| الملف | الوصف |
|-------|-------|
| `bot/data/listings.json` | سجلات العقارات (external_id, slug, status, source, ...) |
| `bot/data/listing_images.json` | صور العقارات (image_url, telegram_file_id, alt_ar, alt_en, sort_order) |

### ملفات **لم** تُمَس (محمية)
- `sitemap.xml` — لم يتغير ❌
- `robots.txt` — لم يتغير ❌
- `offers-data/offers.json` — لم يتغير (backfill ينسخ فقط) ❌
- `bot/config.json` — لم يتغير ❌
- Google Search Console — لم يتغير ❌
- Telegram Bot Token / Webhook — لم يتغير ❌
- Railway/Render/Koyeb config — لم يتغير ❌
- Database URL — لم يتغير (ADD-ONLY) ❌

---

## ٣. الأدوار والصلاحيات

| الدور | الصلاحيات |
|------|-----------|
| **owner** | كل شيء (مثل admin + إدارة المدراء) |
| **admin** | كل شيء (يفعل admin_ids في config) |
| **manager** | add/edit/publish/reject/archive listings، approve visitor+site offers، edit text، marketing text، view links، notifications. **لا يستطيع:** تغيير tokens/webhook/data/settings، إدارة المدراء، حذف العروض |
| **reviewer** | عرض الأرشيف (legacy) |
| **publisher** | نشر العروض (legacy) |
| **editor** | تعديل العروض (legacy) |
| **visitor** | تقديم عروض فقط (pending)، لا يرى العروض غير المنشورة |

### أوامر جديدة
- `/add_manager <telegram_user_id>` — owner/admin فقط
- `/remove_manager <telegram_user_id>` — owner/admin فقط
- `/managers` — عرض قائمة المدراء
- `/listings` — قائمة العقارات + روابط مباشرة
- `/view_listing <external_id>` — عرض عقار بالصور
- `/pending` — العقارات المعلقة (manager/admin) + أزرار اعتماد/رفض

---

## ٤. مسارات النشر (Publish Rules)

| المصدر | من ينشر | status | source | مرئي للزوار؟ |
|--------|---------|--------|--------|--------------|
| البوت — مدير | manager/admin | published | bot_manager | ✅ فوراً |
| البوت — زائر | visitor | pending | bot_visitor | ❌ حتى الاعتماد |
| الموقع — زائر | site visitor | pending | site_visitor | ❌ حتى الاعتماد |
| اعتماد عرض زائر بوت | manager | published | approved_site_as_bot | ✅ |
| اعتماد طلب موقع | manager | published | approved_site_as_bot | ✅ |
| عقار قديم (legacy) | backfill | published | legacy | ✅ |

---

## ٥. الروابط الدائمة (Permanent Links)

| نوع العقار | الرابط | Canonical |
|-----------|-------|-----------|
| عقار جديد | `/offer/{external_id}/{slug}` | `/offer/{external_id}/{slug}` |
| عقار قديم (legacy) | `/property/{old_id}` | `/property/{old_id}` (لم يتغير) |

- الروابط القديمة المفهرسة في Google **تبقى كما هي**
- لا توجد صفحات مكررة لنفس العقار
- `404.html` يعيد التوجيه من `/offer/{eid}` إلى `property.html?offer={eid}`

---

## ٦. الصور

- تُحمل من Telegram، تُحسّن، تُخزن كـ WebP في `images/bot/`
- `telegram_file_id` محفوظ في `listing_images.json`
- `alt_ar` و `alt_en` موجودان (حقول جديدة، ليست نظام SEO كامل)
- البوت: `sendMediaGroup` لأكثر من صورة، `sendPhoto` لصورة واحدة
- الموقع: الصور تظهر في معرض الصور (relative paths، ليست مؤقتة)

---

## ٧. النصوص التسويقية

- المدير يستطيع إضافة نص تسويقي: يدوي أو توليد تلقائي
- القالب التلقائي: (نوع، منطقة، مساحة، سعر، تواصل، اسم المكتب)
- **لا يتطلب ذكاء اصطناعي** — قالب بسيط
- **لا يوقف النشر** إذا فشل التوليد (try/except)

---

## ٨. التدقيق (Audit Log)

كل إجراء يُسجل عبر `user_manager.log_audit`:
- `listing_created` — إنشاء عقار
- `listing_published` — نشر عقار
- `listing_approved` — اعتماد عقار
- `listing_rejected` — رفض عقار
- `listing_text_edited` — تعديل نص
- `marketing_text_added` — إضافة نص تسويقي
- `marketing_text_generated` — توليد نص تسويقي

---

## ٩. Backfill (الترحيل الآمن)

- `listing_lifecycle.backfill_from_offers_json()` — ADD-ONLY، idempotent
- ينسخ العروض من `offers.json` إلى `listings.json` بـ `status=published`, `source=legacy`
- يحفظ `old_id` للربط بالعروض القديمة
- `export_published_to_offers_format()` يُرجع العروض مع `old_id` كـ `id` (للحفاظ على الروابط)
- **offers.json الأصلي لم يُمَس**
- تم التحقق: ٢٥ عرض مستورد، ٥٠ صورة، idempotent

---

## ١٠. الاختبارات

انظر `docs/TESTS.md` لقائمة ١٢ اختبار إلزامي.

**⚠️ لا تدمج في main حتى تجتاز جميع الاختبارات.**

---

## ١١. مشاكل خارج النطاق (Out of Scope — للمرحلة التالية)

هذه مشاكل لاحظناها لكنها **خارج نطاق Phase 1** ولا يجب معالجتها الآن:

1. **عدم وجود قاعدة بيانات حقيقية:** التخزين الحالي JSON-based. للإنتاج بمقياس كبير، يُنصح بقاعدة بيانات (PostgreSQL/SQLite). هذا تغيير كبير يتطلب مرحلة منفصلة.
2. **`sendMediaGroup` limit:** Telegram يسمح بحد أقصى ١٠ صور في media group. إذا تجاوز العقار ١٠ صور، الصور الإضافية تُرسل في رسالة منفصلة. الكود الحالي يعالج هذا لكن قد يحتاج تحسين.
3. **البحث في العقارات:** لا يوجد بحث متقدم في `/listings` (تصفية بالمنطقة/السعر/النوع). يمكن إضافته في Phase 2.
4. **تعديل الصور بعد النشر:** المدير يستطيع تعديل النص والنص التسويقي لكن لا الصور بعد النشر. يمكن إضافته.
5. **`alt_ar`/`alt_en` فارغان للعقارات القديمة:** Backfill يضع `alt_ar=title` لكن `alt_en` فارغ. يمكن ترجمته لاحقاً.
6. **إشعارات المدراء:** `_notify_managers_of_pending` يحتاج context فعلي (bot instance) لإرسال الإشعارات. حالياً يعمل في وضع polling لكن قد يحتاج اختبار في وضع webhook.
7. **تصدير listings إلى offers.json:** Phase 8 يضيف external_id/status للعروض الجديدة في offers.json، لكن العروض القديمة في offers.json لا تحتوي على هذه الحقول. الموقع يعاملها كـ published (backward compatible).
8. **Slug uniqueness across all listings:** تم التحقق من uniqueness لكن قد تحتاج إعادة فحص عند حجم كبير.

---

## ١٢. خطوات ما بعد الدمج (Post-Merge)

1. تشغيل backfill على الخادم: `python3 -c "import sys; sys.path.insert(0, 'bot'); import listing_lifecycle; listing_lifecycle.init(); print(listing_lifecycle.backfill_from_offers_json('../offers-data/offers.json'))"`
2. التأكد من إنشاء `bot/data/listings.json` و `bot/data/listing_images.json`
3. اختبار `/listings` و `/pending` في البوت
4. اختبار رابط `/offer/{external_id}` على الموقع
5. التأكد من عدم تكرار backfill (idempotent)
6. مراقبة الـ audit log للتأكد من تسجيل الإجراءات

---

## ١٣. Git Commits

| Commit | Phase | الوصف |
|--------|-------|-------|
| 370c6f99 | 1-2 | Roles & manager commands |
| be983b81 | 3 | listing_lifecycle.py |
| 9dfc93a6 | 4 | Publish rules integration |
| 9852954d | 5/6/7 | Images, permanent links, listing views, marketing text |
| 0d6d40cb | 8 | Site integration (/offer/ support, visibility, canonical) |
| (this) | 9-10 | Tests documentation & HANDOFF |
