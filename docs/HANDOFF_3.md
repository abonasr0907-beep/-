# HANDOFF 3 — إنعاش البوت وإصلاح التدفقات

## الحالة العامة
- **البيئة:** موقع ستاتيك + بوت بايثون على Railway ينشر من GitHub تلقائيًا (push إلى main فقط).
- **الفرع:** main — محمية إضافة فقط: sitemap.xml / robots.txt / config.json / offers.json.
- **SITE_BASE_URL الافتراضي:** https://urldra.cloud.huawei.com/BExUoXngu4 (يُعتمد عند غياب المتغير).
- **الأدوار:** owner / admin / manager(full_admin) / visitor — المدير ينشر مباشرة.
- **الأرقام:** واتساب 0545888931، مكالمات 0544699933، واتساب+مكالمات 0561610748، و0548601430 في Schema فقط.
- **اسم البوت:** من OFFICE_DATA (لا hardcoded).

---

## الجزء 0 — إنعاش البوت ✅ مكتمل
- **المشكلة:** `logger` استُخدم قبل تعريفه في كتل استيراد SEO/normalizer/bounce_guard (NameError مزدوج → Crash).
- **الإصلاح:** نقل تهيئة logger لأعلى `bot/bot.py` بعد الاستيرادات (سطر 39-43) + `print` في except SEO + إزالة التكرار.
- **التحقق:** `py_compile` نظيف ✅ | `origin/main -1` = `3e0e924d` ✅
- **الحالة:** مدفوع إلى main — Railway يقلع تلقائيًا.

## الجزء 1 — حارس شامل + إحياء الأوامر والأزرار ✅ مكتمل
- [x] الحارس الشامل: `error_handler` (PTB v20 add_error_handler) يلتقط كل استثناءات handlers؛ حُدّث ليرسل تنبيهًا نصيًا فوريًا للمالك/المدراء عند الأخطاء غير المتوقعة (commit 0706f174).
- [x] إحياء الأوامر والأزرار: الكسر الجذري = worker crash (أُصلح في الجزء 0). بعد الإنعاش كل المعالجات الحرجة سليمة: إضافة عرض (add_offer_start)، أزرار الكيبورد (handle_callback)، /listings، /pending، الموافقات (vreq_approve_/vreq_reject_) — تعديل جراحي فقط، لا إعادة بناء.
- [x] التحقق: py_compile ✅ + فحص AST (162 دالة، لا مفقود) ✅

## الجزء 2 — التدفق الصامت 🔄 قيد الإكمال (0.2 ✅)
- [x] حذف إحالات البوت من واجهات الزوار (attach_ + "أرسل عبر البوت") — commit 2ebaf029.
- [x] مسار POST /ingest (سر في هيدر X-Ingest-Secret) يستقبل JSON — موجود من الوسم hotfix-bot-flows.
- [x] JS: ضغط صور client-side (canvas ≤1280px جودة .8) + fetch POST /ingest — compressImage/compressImages/postToIngest.
- [ ] عند الاستقبال: ملاحظة للمدراء + sendPhoto + link_images_to_property (لا عرض منشور).
- [ ] معالج attach_ للمدراء فقط (0.3 التالي).

## الجزء 3 — الإغلاق النهائي M4 مكتمل ✅
- [x] Dark Mode مفعل وزر التبديل بالهيدر وسكربت منع CLS.
- [x] حاسبة ROI للعقارات بجميع المعطيات والتحميل المؤجل وإخلاء المسؤولية.
- [x] زر "🔄 تجديد الأدلة" للمدراء فقط مع التحديث التلقائي و `data/guides.json`.
- [x] صفحات الهبوط الأربعة بالخرج مكتملة ومحدثة.
- [x] نظام Guardian وموديولاته الشاملة + حارس السرية الدوري + تقارير Telegram.
- [x] الاختبارات 50-68 مكتملة واجتازت الفحوصات بنجاح.
- [x] الوسم النهائي: phase-3-final.
