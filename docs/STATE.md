# STATE.md — المصدر الثابت لحالة النظام

> **تنبيه حرج:** كل مهمة تقرأ `STATE.md` أولًا وتحدّثه آخرًا.

---

## 1. الوسوم المقفلة (Locked Tags)
- `phase-1-stable`
- `phase-2-stable`
- `phase-2.7-admins`
- `phase-2.8-hotfix`
- `hotfix-bot-flows`
- `phase-3-final`

---

## 2. الملفات المحمية (Protected ADD-ONLY Files)
يُحظر حذف أي بيانات من هذه الملفات — الإضافة فقط:
- `sitemap.xml`
- `robots.txt`
- `bot/config.json` (و `config.json`)
- `offers-data/offers.json` (و `offers.json`)

---

## 3. الثوابت والقواعد الأساسية
- **SITE_BASE_URL (الافتراضي عند الغياب):** `https://urldra.cloud.huawei.com/BExUoXngu4` (مع قاعدة التحويلة 302).
- **هيدر الجسر الحساس:** `X-Ingest-Secret` (لإرسال الطلبات من المواقع عبر `/ingest`).
- **عدد العروض الثابت:** `27` عرضًا.
- **اتفاقيات التسمية والروابط:**
  - الروابط القديمة `/property/{old_id}` لا تُمس وتظل تعمل.
  - الروابط الجديدة بالتنسيق: `/offer/{external_id}/{slug}`.
- **الأدوار وقواعد النشر:**
  - الأدوار: `owner`, `admin`, `manager` (`full_admin`), `visitor`.
  - المدير ينشر العروض مباشرة دون حاجة لموافقة إضافية.
  - العمليات الحساسة (حذف المالك، تغيير التوكن، إلخ) للمالك (`owner`) فقط.
- **أرقام التواصل الظاهرة للزوار:**
  - واتساب: `0545888931`
  - مكالمات: `0544699933`
  - واتساب + مكالمات: `0561610748`
  - رقم `0548601430` في الـ Schema فقط (غير معروض كزر مباشر للزائر).
- **سرّية البوت (Bot Privacy Guard):**
  - يمنع منعاً باتاً عرض اسم البوت أو رابط البوت أو أي إشارة للبوت أمام الزوار في واجهات الموقع العامة.

---

## 4. حالة المهمة M1
- **الحالة الحالية:** M1 completed ✅
- **النطاق المكتمل:** أساس الحالة + البوابة + طبقة الرواج 1
  - [x] إنشاء `docs/STATE.md` كمصدر ثابت
  - [x] تقييد `attach_` للمدراء والمالك فقط
  - [x] تأكيد `admin.html` noindex وغير مربوطة
  - [x] زر/أمر "🔄 إعادة تهيئة النظام" للمالك فقط مع تقرير خفي
  - [x] مولد بوستر Canvas 1080×1350 وتحميل PNG
  - [x] زر البوت "🐦 نص تغريدة جاهز"
  - [x] زر قناة واتساب المشروط في الفوتر والعقار
  - [x] زر "📅 أضف للتقويم" لتوليد ملف `.ics`

---

## 5. حالة المهمة M6
- **الحالة الحالية:** M6 completed ✅
- **النطاق المكتمل:** واجهات المستخدم المتقدمة، المقارنة الشاملة، SEO المحلّي والتقني
  - [x] إصلاح تراكب الشريط وتكبير الهوية ورفع الخط الأساسي لـ 17px وشبكة العروض 3-4/2
  - [x] أزرار البطاقة المصغرة المدمجة ومودال حجز المعاينة الفوري (POST /ingest + wa.me)
  - [x] المقارنة الشاملة حتى 4 عقارات، قسمان للبوصلة والسعر، ختم التحديث اليومي، وإخلاء المسؤولية
  - [x] عرض 4 أدلة وأخبار السوق العقاري بالنسخ الاحتياطية وتوحيد خط العناوين Reem Kufi
  - [x] القائمة الجانبية: إغلاق فور اللمس خارجها، رابط الأخبار، وأيقونات التواصل المشروطة
  - [x] جولات الفيديو بالتحميل الكسول ومودال إغلاق نظيف
  - [x] SEO المحلي والتقني: 3 صفحات أحياء، فتحة google-site-verification، LocalBusiness Schema موسع، canonical نظيف، NewsArticle/FAQ Schemas، WebP picture fallback، 404 الذكية، الأكثر مشاهدة هذا الأسبوع، وhreflang en

---

## 6. Deployment Path
يتم نشر محتوى الموقع تلقائيًا من فرع main إلى GitHub Pages عبر GitHub Actions workflow في `.github/workflows/static.yml` عند كل push بدون أي خطوات يدويّة مطلوبة من المالك.

## Phase Gates Log
- **M17-POLISH PHASE GATE PASSED**: Standardized unified header across all 29 HTML pages, updated comparison drawer to bottom sheet with outside-click dismiss, verified via node --check and Playwright screenshots.
- **M18-ROOT PHASE GATE PASSED**: Adopted OFFERS_PATH as single source of truth, normalized video fields to video_url, completed 10-item paginated tours, permanent manager authorization, mobile-first 2-column grid at 320px, lightweight offers-index.json with fallback UI, and 6-hour Regression Guardian system immunity.
- **M22-CORE PHASE GATE PASSED**: Single source of truth offers migration, manager preserving merge, api_admin.py backend panel with 2FA OTP owner challenge, Brain Engine arabic regex & gemini actions, Ultimate Security Shield with 30m lockout on 5 fails, rate-limiting, daily backups workflow, secret scanner, sitemap index/pages/offers generation, IndexNow pinging, and 100% py_compile & phase gate verification passed.
- **M24 PHASE GATE PASSED**: Generated sitemap-index.xml, sitemap-pages.xml, sitemap-offers.xml with canonical host https://abonasr0907-beep.github.io/-/ and single Sitemap line in robots.txt. Updated bot sync with GITHUB_CONTENT_TOKEN and queue fallback. Unified Renderer v5 in js/cards.js (?v=6) with 8-action scroll-snap-x bar starting with inspection booking. Updated Regression Guardian rules for 1-col layout at 360px. Verified via Playwright screenshots across 360px, 768px, 1280px.
- **M31 PHASE GATE PASSED**: Replaced .github/workflows/static.yml with standard deployment workflow (cancel-in-progress: false, push branches main, v4/v5 action tags), triggered deployment via README.md update, verified live deployment endpoints.
