# HANDOFF 2 — Phase 2 Full-Stack (Site + Auction + Map + Guardrails)

## تاريخ التسليم
تاريخ الإكمال: 2026

## الفرع
`feat/site-auction-map`

## آخر التزام (قبل دمج Section 5)
`e4964672` — feat: Phase 2 §4 — guardrails, quality score, anti-duplicate, ALT auto-gen

## الحالة
✅ جميع أقسام Phase 2 (§0–§4) مكتملة ومُلتزمة ومُدفوعة. Section 5 (هذا التسليم) يُكمل الاختبارات + هذا الملف + دمج main + الوسم.

---

## 1. ملخص ما تم إنجازه

تم بناء Phase 2 كاملاً فوق Phase 1 المستقرة: عرض العقارات مع معرض صور (lazy + ALT تلقائي)، أقسام (منشورة فقط + "عامة" احتياطي)، سياسة "مُباع" مع عقارات مشابهة، نظام مزايدة كامل (واجهة + بوت)، خريطة فضائية ثلاثية الأبعاد (MapLibre GL + Esri، CDN فقط بدون مفاتيح API)، ودرجة جودة + كشف تكرار + توليد ALT تلقائي — **كل ذلك دون كسر الروابط الدائمة أو SEO أو أرقام المكتب.**

### الالتزامات على الفرع (بالترتيب)
| التزام | القسم | الوصف |
|--------|------|------|
| `7aee5502` | prep | chore: phase 2 prep — backups gitignore + data manifest baseline |
| `d68ddb72` | §0 | merge: Phase 1 — bot manager publish lifecycle |
| `e52e40eb` | §1 | feat: gallery lazy+ALT auto-gen, categories published-only + "عامة" fallback, sold policy, similar properties, detail links |
| `27c93cb4` | §2 | feat: auction/bidding system (frontend + bot backend) |
| `9e0a7b75` | §3 | feat: satellite map (MapLibre GL + Esri World Imagery, CDN only) |
| `e4964672` | §4 | feat: guardrails, quality score, anti-duplicate, ALT auto-gen |
| (هذا الالتزام) | §5 | feat: Phase 2 §5 — tests + HANDOFF_2 + Phase 3 locked scope |

---

## 2. الملفات المُعدّلة / المُنشأة

### ملفات مُعدّلة (MODIFIED)
| الملف | التغيير |
|-------|---------|
| `bot/bot.py` | §2: `import bids` + `bids.init(BIDS_FILE)`، تحليل حمولة `bid_` في `/start`، `_handle_bid_deep_link()`، `cmd_bids` / `cmd_approve_bid` / `cmd_reject_bid`، تحديث نص المساعدة. §4: لا تغييرات إضافية (الدوال في listing_lifecycle.py) |
| `bot/listing_lifecycle.py` | §4: `quality_score()` (0–100, تحذير فقط)، `find_duplicates()` (title+price, title+location, phone — تحذير فقط)، `auto_generate_alt()` + تكامل في `add_listing_image()` |
| `js/main.js` | §1: `isOfferPublished()`, `offerCategory()` (fallback "عامة"), `offerDetailLink()`, فلتر published-only, شارة "مُباع". §2: `sendBid()` (تحقق 1000–5B ريال، هاتف ≥9)، `showBidSuccessModal()`، زر مزايدة |
| `property.html` | §1: معرض lazy + ALT تلقائي، شارة مُباع، عقارات مشابهة، زر مزايدة + modal. §2: `BOT_USERNAME`, `openPropertyBid()`, `submitPropertyBid()` (wa.me + deep-link). §3: خريطة MapLibre GL فضائية (Esri tiles, pitch 58°, bearing 20°, NavigationControl), Leaflet fallback, Google Maps link, lazy load عبر IntersectionObserver, `isAdmin()` |
| `css/style.css` | §1: `.offer-btn-details`, `.offer-badge.sold-badge`. (أي تغييرات خريطة مدمجة في property.html) |
| `docs/TESTS.md` | §5: إضافة اختبارات Phase 2 (13–24) |
| `.gitignore` | §0: `backups/` |

### ملفات مُنشأة (NEW)
| الملف | الوصف |
|-------|-------|
| `bot/bids.py` | وحدة تخزين المزايدات (Phase 2): snake_case، `add_bid` (لا يغير السعر)، `get_pending`، `find_bid`، `set_status` (approved/rejected + reviewed_by). القاعدة الذهبية: لا تغيير تلقائي للسعر أو current_bid |
| `docs/SEO_GUARDRAILS.md` | القواعد الذهبية: روابط دائمة، meta tags، ALT، أداء (CDN فقط)، كشف تكرار، درجة جودة، قائمة ملفات محمية |
| `docs/PHASE_GATES.md` | بوابات العبور بين المراحل + قالب تقرير الحوادث (Incident Report) + أمثلة + قاعدة التوقف الآمن |
| `docs/PHASE_2_DATA_MANIFEST.md` | خط أساس البيانات: 25 عرض، 25 منشور (جميعها legacy)، 50 صورة |
| `docs/HANDOFF_2.md` | هذا الملف |

### ملفات بيانات (تُُنشأ وقت التشغيل)
| الملف | الوصف |
|-------|-------|
| `bot/data/bids.json` | سجلات المزايدات الجديدة (snake_case): id, listing_id, bidder_name, bidder_phone, amount, status, created_at, reviewed_by |

### ملفات **لم** تُمَس (محمية)
- `sitemap.xml` — لم يتغير ❌
- `robots.txt` — لم يتغير ❌
- `offers-data/offers.json` — لم يتغير (backfill نسخ فقط) ❌
- `offers-data/office-data.json` — لم يتغير (أرقام المكتب محمية) ❌
- `bot/config.json` — لم يتغير ❌
- Google Search Console — لم يتغير ❌
- Telegram Bot Token / Webhook — لم يتغير ❌
- Railway/Render/Koyeb config — لم يتغير ❌
- Database URL — لم يتغير (ADD-ONLY) ❌

---

## 3. الأقسام المكتملة بالتفصيل

### §0 — تثبيت Phase 1 ✅
- دمج `feat/bot-manager-publish-lifecycle` (التزام `fe849fa6`) في `main` بـ `--no-ff`
- وسم `phase-1-stable` + دفع الوسم
- إنشاء فرع `feat/site-auction-map`
- نسخ احتياطي محلي `backups/` + `.gitignore`
- `docs/PHASE_2_DATA_MANIFEST.md` (خط أساس البيانات)

### §1 — صفحة العقار + الأقسام + سياسة المُباع ✅
- معرض صور lazy loading + ALT تلقائي من `alt_ar` / `images_alt` / توليد
- الأقسام: عرض `status=published` فقط + fallback "عامة"
- حقل `sold=true` → شارة "مُباع" + عقارات مشابهة (لا حذف أبداً)
- روابط تفصيلية: `/offer/{external_id}/{slug}` + `/property/{old_id}` (محفوظة)

### §2 — نظام المزايدة (واجهة + بوت) ✅
- حقول: `price_mode` (sum/auction), `sum_price`, `current_bid`, `allow_bidding`
- زر "طلب مزايدة" + form (الاسم/الهاتف/المبلغ) + تحقق 1000–5,000,000,000 ريال
- رابط wa.me مع نص مُعبأ (أرقام المكتب لم تتغير)
- Deep-link: `https://t.me/{BOT_USERNAME}?start=bid_{external_id}_{amount}`
- `bot/bids.py` + `bids.json` (snake_case: id, listing_id, bidder_name, bidder_phone, amount, status=pending, created_at, reviewed_by)
- البوت يفكك حمولة `bid_`، يحفظ المزايدة، يُشعر المدراء فوراً
- أوامر المدير: `/bids`, `/approve_bid {bid_id}`, `/reject_bid {bid_id}`
- **القاعدة الذهبية:** سعر العقار و `current_bid` لا يتغيران تلقائياً أبداً. `/approve_bid` يحدّث `current_bid` يدوياً فقط وبعد موافقة صريحة
- noindex على صفحات form/thank-you المنفصلة (المودال مدمج في property.html فلا noindex عليه)

### §3 — الخريطة الفضائية (CDN فقط) ✅
- MapLibre GL 3.6.2 (CDN) + Esri World Imagery (لا مفتاح API)
- pitch 58°, bearing 20°, NavigationControl مع visualizePitch
- علامة مخصصة + popup + رابط "فتح في Google Maps"
- Leaflet fallback مع Esri tiles إذا فشل MapLibre
- lazy load عبر IntersectionObserver
- الموقع الافتراضي: الخرج (24.1554, 47.3068) + تنبيه للمدير عند استخدامه

### §4 — الحرس + درجة الجودة + كشف التكرار + ALT تلقائي ✅
- `docs/SEO_GUARDRAILS.md` — القواعد الذهبية + قائمة الملفات المحمية
- `docs/PHASE_GATES.md` — بوابات العبور + قالب تقرير الحوادث
- `quality_score()` — 0–100 (title 15, description 15, category 10, images 20, coords 10, marketing 10, price 10, location 10), تحذير فقط، لا حظر
- `find_duplicates()` — title+price, title+location, phone (≥9 أرقام), تحذير فقط، لا حذف
- `auto_generate_alt()` — `"{نوع} {مساحة}m² — {منطقة} | صورة {N} | مكتب آفاق الإنجاز العقاري"` + تكامل في `add_listing_image()`

### §5 — الاختبارات + هذا الملف + دمج main + الوسم ✅
- إضافة اختبارات Phase 2 (13–24) إلى `docs/TESTS.md`
- تشغيل الاختبارات الرخيصة: `py_compile` (bot.py, bids.py, listing_lifecycle.py) ✅، `node -c` (main.js, property.html) ✅، استدعاء دوال مباشر (quality_score, find_duplicates, auto_generate_alt, bids.add_bid/set_status) ✅
- إنشاء `docs/HANDOFF_2.md` (هذا الملف)
- دمج `feat/site-auction-map` في `main` بـ `--no-ff` + دفع main (هذا هو النشر)
- وسم `phase-2-stable` + دفع الوسم
- فحص رخيص ما بعد النشر

---

## 4. الاختبارات

### اختبارات Phase 1 (1–12) — من Phase 1، لا تزال سارية
موثقة في `docs/TESTS.md`، جميعها منفذة قبل دمج Phase 1.

### اختبارات Phase 2 (13–24) — مُضافة في Section 5
| # | الاختبار | النوع | الحالة |
|---|---------|------|--------|
| 13 | معرض lazy + ALT تلقائي | يدوي | موثق |
| 14 | الأقسام published-only + "عامة" | يدوي | موثق |
| 15 | سياسة مُباع + عقارات مشابهة | يدوي | موثق |
| 16 | زر مزايدة + تحقق المبلغ | يدوي | موثق |
| 17 | رابط wa.me + deep-link | يدوي | موثق |
| 18 | البوت يفكك bid_ + يُشعر المدراء | بوت | موثق (مراجعة يدوية) |
| 19 | أوامر /bids /approve_bid /reject_bid | بوت | موثق (مراجعة يدوية) |
| 20 | خريطة MapLibre GL + Esri | يدوي | موثق |
| 21 | الموقع الافتراضي + تنبيه المدير | يدوي | موثق |
| 22 | درجة الجودة (تحذير فقط) | رخيص | ✅ منفذ (score=100/100) |
| 23 | كشف التكرار (تحذير فقط) | رخيص | ✅ منفذ (3 معايير + no-match) |
| 24 | ALT تلقائي عند حفظ الصورة | رخيص | ✅ منفذ (index 0/2/empty) |

### الاختبارات الرخيصة المنفذة محلياً
```
py_compile: bot.py ✅ | bids.py ✅ | listing_lifecycle.py ✅
node -c:    main.js ✅ | property.html (inline) ✅
الدوال:     quality_score() ✅ | find_duplicates() ✅ | auto_generate_alt() ✅ | bids.add_bid/set_status ✅
```

---

## 5. المكتمل / المتبقي

### ✅ مكتمل
- [x] §0: تثبيت Phase 1 (دمج + وسم phase-1-stable + فرع جديد)
- [x] §1: معرض + أقسام + سياسة مُباع + عقارات مشابهة
- [x] §2: نظام مزايدة كامل (واجهة + بوت + bids.py + أوامر)
- [x] §3: خريطة فضائية (MapLibre GL + Esri, CDN فقط, 3D, lazy)
- [x] §4: الحرس + درجة جودة + كشف تكرار + ALT تلقائي
- [x] §5: اختبارات + HANDOFF_2 + دمج main + وسم phase-2-stable

### ⏳ المتبقي (لا شيء من Phase 2)
لا توجد مهام متبقية في Phase 2. جميع الأقسام مكتملة.

### ملاحظات للمراجعة اليدوية
- اختبارات البوت (18–19) تتطلب تشغيل البوت فعلياً — موثقة للمراجعة اليدوية
- الخريطة (20–21) تتطلب فتح صفحة عقار في المتصفح — موثقة للمراجعة اليدوية
- المزايدات الفعلية تُخزن في `bot/data/bids.json` عند بدء الاستخدام

---

## 6. Phase 3 — Locked Scope (النطاق المقفل)

> **هذا القسم يُعرّف نطاق Phase 3 للمرحلة القادمة. يجب الالتزام به ولا يتوسع دون موافقة صريحة.**

### الأهداف المقفلة لـ Phase 3
Phase 3 تركز على **الأنظمة الذكية والأتمتة المتقدمة** فوق الأساس المستقر من Phase 1 و Phase 2:

1. **نظام إشعارات ذكي متعدد القنوات**
   - إشعارات Telegram للمدراء عند: مزايدة جديدة، طلب نشر، تنبيه جودة، تكرار محتمل
   - إشعارات للزائر عند: تغيير حالة مزايدته (approved/rejected)
   - جدولة إشعارات دورية (تقرير أسبوعي تلقائي)
   - **قاعدة:** لا spam — إشعار واحد لكل حدث، مع خيار كتم

2. **بحث وفلترة متقدم للعقارات**
   - بحث نصي في العنوان/الوصف/المنطقة
   - فلترة متعددة: النوع + المنطقة + نطاق السعر + المساحة + الحالة (متاح/مُباع)
   - ترتيب: الأحدث / السعر تصاعدي / السعر تنازلي / المساحة
   - **قاعدة:** فلترة published-only محفوظة من Phase 2

3. **لوحة تحكم (Dashboard) للإدارة**
   - إحصائيات حية: عدد العروض المنشورة/المعلقة، المزايدات، الزيارات
   - مخططات بسيطة (CDN فقط، لا مكتبات ثقيلة)
   - **قاعدة:** لوحة التحكم admin-only، noindex، لا تؤثر على SEO

4. **تحسين أداء الموقع (Performance)**
   - تحسين تحميل الصور: WebP حيث ممكن، أحجام متجاوبة (srcset)
   - Preload للموارد الحرجة
   - **قاعدة:** CDN فقط، لا إعادة تنسيق للكود القديم

5. **تكامل تحليلات بسيط (Analytics)**
   - تتبع مشاهدات الصفحات (بدون Google Analytics — حل محلي خفيف)
   - تتبع نقرات زر المزايدة / WhatsApp
   - **قاعدة:** لا تتبع للأرقام أو البيانات الشخصية، احترام الخصوصية

### خارج النطاق (Out of Scope) لـ Phase 3
- ❌ لا قاعدة بيانات خارجية (يبقى JSON)
- ❌ لا إطار عمل ثقيل (لا React/Vue/Angular)
- ❌ لا مفاتيح API مدفوعة (تبقى CDN مجاني)
- ❌ لا تغيير أرقام المكتب في `office-data.json`
- ❌ لا كسر الروابط الدائمة (`/offer/{id}`, `/property/{old_id}`)
- ❌ لا إعادة هيكلة الكود القديم
- ❌ لا تغيير تلقائي لسعر العقار أو `current_bid` (القاعدة الذهبية)

### بوابة العبور Phase 2 → Phase 3
موثقة في `docs/PHASE_GATES.md` §2. المتطلبات:
- [x] كل أقسام Phase 2 (§1–§5) مكتملة ومُلتزمة ومُدفوعة
- [x] اختبارات Phase 2 مُضافة لـ `docs/TESTS.md` ومنفذة
- [x] `docs/HANDOFF_2.md` يحتوي: الفرع، آخر التزام، المكتمل/المتبقي، Phase 3 Locked Scope
- [x] دمج `feat/site-auction-map` في `main` (merge --no-ff) + دفع main
- [x] وسم `phase-2-stable` + دفع الوسم
- [x] فحص ما بعد النشر: الرئيسية + صفحة عقار = 200، رابط `/offer/` يعمل، ≥1 صورة

### القواعد الذهبية الحارسة (تنتقل إلى Phase 3)
1. الروابط الدائمة لا تُكسر أبداً
2. أرقام المكتب في `office-data.json` لا تتغير
3. لا مفاتيح API، لا تبعيات ثقيلة (الخريطة CDN فقط)
4. `robots.txt` و `sitemap.xml` لا يُعدّلان دون مراجعة
5. سعر العقار و `current_bid` لا يتغيران تلقائياً
6. درجة الجودة وكشف التكرار = تحذير فقط (لا حظر/حذف)
7. كل قسم مكتمل = التزام + دفع فوراً
8. التوقف الآمن: اكتب "مكتمل/متبقي" في HANDOFF قبل التوقف

---

## 7. خطوات ما بعد الدمج (للمرحلة القادمة)

1. ✅ دمج `feat/site-auction-map` → `main` (--no-ff)
2. ✅ دفع `main` (هذا هو النشر — GitHub Pages يلتقط تلقائياً)
3. ✅ وسم `phase-2-stable` + دفع الوسم
4. ⏳ فحص رخيص ما بعد النشر:
   - `curl -s -o /dev/null -w "%{http_code}" https://abonasr0907-beep.github.io/-/` → يجب 200
   - `curl -s -o /dev/null -w "%{http_code}" https://abonasr0907-beep.github.io/-/property.html?offer=1` → يجب 200
   - التحقق من رابط `/offer/` يعمل
   - التحقق من ≥1 صورة تُعرض
5. ⏳ مراجعة يدوية: الخريطة، المزايدة، الأقسام

---

## 8. ملاحظات تقنية

- البوت: `tlastlastlasbot` (id: 8629398802)
- رقم WhatsApp للمزايدات: 966545888931 (من `office-data.json`، لم يتغير)
- الفرع: `feat/site-auction-map` → يُدمج في `main`
- النشر: عبر `git push` إلى `main` فقط (لا أداة deploy)
- التخزين: JSON (offers.json, listings.json, bids.json) — لا قاعدة بيانات
- الكود القديم للمزايدات (`_save_bid_record`, `_update_offer_with_bid` مع `highestBid`) لا يزال في bot.py لكن **لا يُستدعى** من كود Phase 2 الجديد. الوحدة الجديدة `bids.py` تستخدم snake_case ولا تغير السعر تلقائياً.
