# 🏰 النواة الحقيقية والدليل الفني الشامل لمشروع مكتب آفاق الإنجاز العقاري

تضم هذه الوثيقة الدليل المكتمل والشامل لنواة مشروع **مكتب آفاق الإنجاز العقاري**، شاملاً الهيكلية، طريقة العمل، الارتباطات الداخلية والخارجية، والملفات البرمجية والتكوينية كاملة لتمكينك من الاحتفاظ بنواة المشروع وإعادة بنائها أو تطوير نسختك الجديدة دون فقدان أي التفاصيل.

---

## 1. 🏗️ الهيكلة العامة للمشروع (Project Directory Architecture)

تتألف البنية الحالية من نظام موقع إلكتروني ثابت (Static Website) مدمج مع بوت تيليجرام (Telegram Admin Bot) لإدارة العروض والبيانات بنظام نشر مباشر تلقائي.

```
.
├── index.html              # الصفحة الرئيسية للموقع (Glass Design)
├── farms.html              # صفحة عرض المزارع
├── resthouses.html         # صفحة عرض الاستراحات
├── lands.html              # صفحة عرض الأراضي السكنية
├── services.html           # صفحة خدمات ما بعد البيع (رخص، مقاولات، آبار...)
├── list-property.html      # صفحة نموذج عرض عقار من قبل الزائر
├── inquiry.html            # صفحة نموذج طلب استفسار/عقار مخصص
├── contact.html            # صفحة أرقام التواصل وروابط شبكات التواصل
├── robots.txt              # تعليمات محركات البحث
├── sitemap.xml             # خريطة الموقع لمحركات البحث
├── site.webmanifest        # ملف تعريف تطبيق الويب (PWA Manifest)
├── .nojekyll               # منع جيكيل في GitHub Pages
├── css/
│   └── style.css           # ملف التنسيق الرئيسي المتكامل (Glassmorphic Styles)
├── js/
│   └── main.js             # البرمجية التفاعلية، جلب البيانات، المساعد الذكي والنماذج
├── offers-data/
│   ├── offers.json         # قاعدة بيانات العروض المباشرة (العروض الفعالة)
│   └── office-data.json    # البيانات الأساسية للمكتب ومؤشرات أسعار المناطق (البوصلة)
├── images/                 # الصور والأصول المرئية
│   ├── logo.jpg / logo-original.jpg
│   ├── homepage-hero.png / farms-bg.jpg / resthouse-bg.jpg / land-bg.jpg / services-bg.jpg / well-drilling.jpg
│   └── bot/                # الصور المرفوعة عبر بوت التليجرام
├── bot/
│   ├── bot.py              # بوت تيليجرام التفاعلي لإدارة العروض والنشر المباشر والمعالجة بالذكاء الاصطناعي
│   ├── config.json         # إعدادات البوت والمدراء
│   └── data/
│       └── visitor_requests.json  # تخزين الطلبات والاستفسارات المستلمة
├── docs/
│   ├── bot-manual.md       # دليل استخدام بوت التيليجرام
│   ├── guide.html          # الصفحة الإرشادية للمكتب
│   └── CORE_PROJECT_DOCUMENTATION.md # الوثيقة الحالية الشاملة للنواة
└── .github/
    └── workflows/
        ├── static.yml      # إجراءات النشر التلقائي على GitHub Pages عند الدفع إلى main
        └── backups.yml     # النسخ الاحتياطي اليومي للبيانات مع تدوير 7 أيام
```

---

## 2. 🔗 كيفية عمل المشروع والارتباطات (Workflow & Integration Architecture)

1. **الواجهة الأمامية (Frontend)**:
   - مبنية باستخدام **Vanilla JavaScript** و **HTML5/CSS3** بدون أطر عمل خارجية معقدة لضمان السرعة المطلقة والتحميل الخفيف.
   - يعتمد الموقع على الخطوط العربية `Tajawal` و `Cairo` من **Google Fonts**، والأيقونات من **FontAwesome (v6.4.0)** عبر CDN.
   - يتصل الملف `js/main.js` بالملفات `offers-data/offers.json` و `offers-data/office-data.json` عن طريق `fetch(..., { cache: 'no-store' })` لعرض البيانات الحية دائماً.

2. **البوت ولوحة التحكم (Telegram Admin Bot)**:
   - مكتوب بلغة **Python 3** باستخدام مكتبة `python-telegram-bot` ومكتبة `Pillow` لتحسين الصور.
   - يقوم الأدمن برفع الصور من التيليجرام، فيقوم البوت بالمعالجة بالذكاء الاصطناعي (Sharpness, Contrast, Color enhancement) وحفظها في `images/bot/`.
   - يولد البوت نصاً تسويقياً تلقائياً، ويصنف العرض (مزرعة/استراحة/أرض) تلقائياً بناءً على الكلمات المفتاحية.
   - عند تأكيد العرض، يقوم البوت بالكتابة المباشرة في `offers-data/offers.json` مما يحدث الموقع فوراً على GitHub Pages عند الـ Push أو التحديث.

3. **أنظمة التواصل والتوجيه خارجيًا**:
   - **WhatsApp Integration**: جميع نماذج العرض (`list-property.html`) والاستفسار (`inquiry.html`) وبطاقات العروض تقوم بتوليد روابط `wa.me/966...` مجهزة بنص الاستفسار وتفتح الواتساب مباشرة لدى العميل.
   - **Google / Petal Maps**: كل عرض يرتبط بموقعه على الخريطة عبر `map_link` مع رابط fallback محدد لموقع المكتب الرئيسي.
   - **البوصلة العقارية**: تعتمد على مؤشرات الهيئة العامة للعقار المعرفة في `office-data.json`.

---

## 3. 📜 الأكواد البرمجية والملفات التكوينية كاملة (Complete Source Code Core)

---

### 📄 1. `offers-data/office-data.json` (بيانات المكتب والمناطق)
```json
{
  "office": {
    "name": "مكتب آفاق الإنجاز العقاري",
    "nameEn": "Afaq Al-Injaz Real Estate Office",
    "experience": "20 سنة خبرة في المجال العقاري",
    "established": "2005",
    "city": "الرياض - الخرج",
    "email": "afaqalqary@gmail.com",
    "phones": {
      "whatsapp_calls": "0545888931",
      "calls_only": "0544699933",
      "whatsapp_calls_2": "0561610748"
    },
    "social": {
      "snapchat": "https://www.snapchat.com/add/mmnf2278?share_id=N54BP0E_h1k&locale=ar-SA",
      "tiktok": "https://www.tiktok.com/@whatyouarelookingforisw3?_r=1&_t=ZS-98ddjIoDMEJ"
    },
    "google_maps": "https://maps.app.goo.gl/SQhqCtgpeLNLb56w8?g_st=aw",
    "default_location": "مخطط الرحمانية - الخرج",
    "telegram_bot": "https://t.me/afaq_alinjaz_bot"
  },
  "areas": {
    "الرحمانية": {
      "land_avg_price_sqm": "850",
      "farm_avg_price_sqm": "120",
      "resthouse_avg_price": "350,000 - 1,200,000",
      "description": "مخطط الرحمانية من أبرز المخططات في الخرج، يتميز بقربه من الهياثم والدلم"
    },
    "الهياثم": {
      "land_avg_price_sqm": "1100",
      "farm_avg_price_sqm": "150",
      "resthouse_avg_price": "400,000 - 1,500,000",
      "description": "حي الهياثم من الأحياء الحيوية في الخرج، قريب من الخدمات"
    },
    "الدلم": {
      "land_avg_price_sqm": "600",
      "farm_avg_price_sqm": "90",
      "resthouse_avg_price": "250,000 - 900,000",
      "description": "الدلم مركز تاريخي زراعي، مشهور بمزارعه وأراضيه الزراعية الواسعة"
    },
    "الضبيعة": {
      "land_avg_price_sqm": "700",
      "farm_avg_price_sqm": "100",
      "resthouse_avg_price": "280,000 - 1,000,000",
      "description": "منطقة زراعية هادئة بقرب من الخرج، مناسبة للمزارع والاستراحات"
    },
    "العفجة": {
      "land_avg_price_sqm": "650",
      "farm_avg_price_sqm": "95",
      "resthouse_avg_price": "260,000 - 950,000",
      "description": "منطقة زراعية بمنطقة الخرج، تتميز بأراضيها الخصبة"
    }
  },
  "services": [
    {
      "id": "post-sale",
      "title": "خدمات ما بعد البيع",
      "icon": "fas fa-handshake",
      "items": [
        { "name": "استخراج رخص البناء", "desc": "إنجاز جميع معاملات رخص البناء بكفاءة وسرعة" },
        { "name": "المقاولات", "desc": "تنفيذ المشاريع الإنشائية بأعلى معايير الجودة" },
        { "name": "التشطيب", "desc": "تشطيبات داخلية وخارجية بأحدث التصاميم" },
        { "name": "إدارة الأملاك", "desc": "إدارة عقاراتك بالكامل من تأجير وصيانة" },
        { "name": "حفر الآبار", "desc": "حفر الآبار وتحديد مواقعها وتصويرها" },
        { "name": "تصوير العقارات", "desc": "تصوير احترافي للعقارات لأغراض التسويق" }
      ]
    }
  ]
}
```

---

### 📄 2. `bot/config.json` (إعدادات البوت)
```json
{
  "admin_ids": [],
  "office_location": "https://maps.app.goo.gl/SQhqCtgpeLNLb56w8?g_st=aw",
  "website_url": "https://afaqalqary.pages.dev/",
  "offers_file": "../offers-data/offers.json",
  "auto_renew": true,
  "max_images": 5
}
```

---

### 📄 3. `.github/workflows/static.yml` (سير عمل النشر تلقائياً)
```yaml
name: Deploy static content to Pages
on:
  push:
    branches: ["main"]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
concurrency:
  group: "pages"
  cancel-in-progress: false
jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
      - name: Setup Pages
        uses: actions/configure-pages@v5
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

### 📄 4. `.github/workflows/backups.yml` (النسخ الاحتياطي التلقائي)
```yaml
name: Daily Data Backups & 7-Day Rotation

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

permissions:
  contents: write

jobs:
  backup:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repository
        uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683 # v4.2.2
        with:
          fetch-depth: 0

      - name: Create Backup and Rotate
        run: |
          git config --global user.name "Afaq Backup Bot"
          git config --global user.email "backup@afaq.local"

          DATE=$(date +'%Y-%m-%d_%H%M%S')
          TARGET_DIR="backups/data_backup_$DATE"

          mkdir -p "$TARGET_DIR/data" "$TARGET_DIR/offers-data"
          cp -r data/*.json "$TARGET_DIR/data/" 2>/dev/null || true
          cp -r offers-data/*.json "$TARGET_DIR/offers-data/" 2>/dev/null || true

          # Rotate: remove backups older than 7 days
          find backups/ -maxdepth 1 -type d -name "data_backup_*" -mtime +7 -exec rm -rf {} + 2>/dev/null || true

          git checkout -B backups
          git add backups/
          if ! git diff --staged --quiet; then
            git commit -m "Automated daily backup: $DATE"
            git push origin backups --force
          else
            echo "No data changes to backup."
          fi
```

---

### 📄 5. `robots.txt`
```
User-agent: *
Allow: /
Sitemap: https://abonasr0907-beep.github.io/-/sitemap.xml
```

---

### 📄 6. `sitemap.xml`
```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://abonasr0907-beep.github.io/-/</loc>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/farms.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/resthouses.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/lands.html</loc>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/services.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/list-property.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/inquiry.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.6</priority>
  </url>
  <url>
    <loc>https://abonasr0907-beep.github.io/-/contact.html</loc>
    <changefreq>monthly</changefreq>
    <priority>0.5</priority>
  </url>
</urlset>
```

---

### 📄 7. `site.webmanifest`
```json
{
  "name": "مكتب آفاق الإنجاز العقاري",
  "short_name": "آفاق الإنجاز",
  "start_url": "/index.html",
  "display": "standalone",
  "background_color": "#F5F1E8",
  "theme_color": "#2A5050",
  "icons": [
    {
      "src": "images/logo.jpg",
      "sizes": "192x192",
      "type": "image/jpeg"
    },
    {
      "src": "images/logo.jpg",
      "sizes": "512x512",
      "type": "image/jpeg"
    }
  ]
}
```

---

## 4. 💡 ملاحظات وإرشادات هامة لنقل وبناء النسخة الجديدة دون مفقودات

1. **إعادة بناء النظام على بيئة جديدة**:
   - احرص على نقل مجلد `offers-data/` ومجلد `images/` كاملين، فهما يمثلان البيانات الأساسية والأصول المرئية للنظام.
   - لتشغيل بوت التيليجرام مستقبلاً، قم بتنصيب التبعيات `python-telegram-bot` و `Pillow` و `requests` عبر `pip install python-telegram-bot Pillow requests`.
   - قم بتعيين المتغير البيئي `BOT_TOKEN` للبوت لكي يعمل بتكامليته التامة مع `bot/bot.py`.

2. **قواعد البيانات الحية والنشر المباشر**:
   - يعتمد الموقع على القراءة المباشرة المحدثة بدون كاش عبر `{ cache: 'no-store' }` في `js/main.js` لضمان استلام العروض الفورية المحدثة بواسطة البوت في `offers-data/offers.json`.

3. **الامتثال للهوية والترخيص**:
   - ترخيص فال للمكتب: **1100004208**.
   - أرقام التواصل الرسمية المتاحة للجمهور:
     - الواتساب العام: `0545888931`
     - الاتصال الهاتفية: `0544699933`
     - الواتساب والاتصال الثاني: `0561610748`
   - تذكر أن رقم الجوال `0548601430` مخصص فقط لـ Schema Markup في محركات البحث.
