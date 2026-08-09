# دليل فهرسة الموقع في محركات البحث (SEO)

## رابط الموقع للزوار
**https://abonasr0907-beep.github.io/-/**

---

## ✅ ما تم إنجازه (جاهز للفهرسة)

### 1. ملفات SEO الأساسية (جميعها منشورة وتعمل)
- **robots.txt** — يسمح لجميع محركات البحث بالفهرسة، يمنع /bot/ و /admin.html
- **sitemap.xml** — 8 صفحات مع تواريخ محدّثة (2026-08-09)
- **schema.org** — بيانات منظمة RealEstateAgent (اسم، هاتف، عنوان، إحداثيات، روابط اجتماعية)
- **meta tags** — description، keywords، Open Graph، Twitter Cards
- **canonical link** — يمنع تكرار المحتوى
- **site.webmanifest** — PWA manifest

### 2. التحقق من النشر
- ✅ الصفحة الرئيسية: HTTP 200
- ✅ جميع الصفحات (farms, resthouses, lands, services, contact): HTTP 200
- ✅ sitemap.xml: HTTP 200
- ✅ robots.txt: HTTP 200
- ✅ js/main.js + css/style.css: HTTP 200

---

## 🔍 خطوات الفهرسة في Google (مطلوب منك)

Google أوقفت خدمة ping التلقائية. الفهرسة الآن تتم عبر **Google Search Console**:

### الطريقة الأولى: Google Search Console (موصى بها)

1. اذهب إلى: **https://search.google.com/search-console**
2. أضف موقع جديد بنوع **بادئة عنوان URL**
3. أدخل: `https://abonasr0907-beep.github.io/-/`
4. **التحقق من الملكية** — اختر طريقة HTML tag:
   - سيعطيك Google كود مثل: `<meta name="google-site-verification" content="ABC123..." />`
   - **أرسل لي الكود** وسأضيفه للموقع وأعيد النشر
5. بعد التحقق، اذهب إلى **Sitemaps** وأرسل:
   ```
   https://abonasr0907-beep.github.io/-/sitemap.xml
   ```
6. اذهب إلى **URL Inspection** واطلب فهرسة كل صفحة:
   - `https://abonasr0907-beep.github.io/-/`
   - `https://abonasr0907-beep.github.io/-/farms.html`
   - `https://abonasr0907-beep.github.io/-/resthouses.html`
   - `https://abonasr0907-beep.github.io/-/lands.html`
   - `https://abonasr0907-beep.github.io/-/services.html`
   - `https://abonasr0907-beep.github.io/-/contact.html`

### الطريقة الثانية: Bing Webmaster Tools

1. اذهب إلى: **https://www.bing.com/webmasters**
2. أضف موقعك: `https://abonasr0907-beep.github.io/-/`
3. أرسل sitemap: `https://abonasr0907-beep.github.io/-/sitemap.xml`

---

## ⏱️ كم يستغرق ظهور الموقع في نتائج البحث؟

- **ظهور أولي:** 2-7 أيام بعد طلب الفهرسة
- **فهرسة كاملة:** 1-4 أسابيع
- **تحسين الترتيب:** مستمر (يعتمد على المحتوى، الروابط، تحديث العروض)

---

## 🚂 إعدادات Railway (لبوت تيليجرام)

### المتغيرات المطلوبة في لوحة Railway:

| المتغير | القيمة | الوصف |
|--------|--------|-------|
| `GITHUB_TOKEN` | (توكن GitHub الخاص بك) | لرفع الصور والعروض للموقع |
| `WEBHOOK_URL` | `https://مشروعك.railway.app` | رابط خدمتك على Railway (بعد النشر) |
| `PORT` | (تلقائي) | Railway يوفره تلقائياً |

### القرص الدائم (Volume) — مهم جداً:

1. في لوحة Railway → خدمتك → **Volumes**
2. أضف Volume جديد بحجم **1GB**
3. اربطه بمسار: `/app/bot/data`
4. هذا يمنع فقدان الجلسات والمسودات والنسخ الاحتياطية عند إعادة النشر

### بعد أول نشر على Railway:

1. احصل على رابط الخدمة (مثل `https://afaq-bot-production.up.railway.app`)
2. أضفه كقيمة لـ `WEBHOOK_URL` في متغيرات البيئة
3. أعد النشر (Redeploy)
4. البوت سيسجل webhook تلقائياً مع تيليجرام
