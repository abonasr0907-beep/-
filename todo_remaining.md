# المهام المتبقية - Remaining Tasks (Phase 4)

## المرجع: PHASE3_FINAL_REPORT.md + CHECKPOINT_PHASE2.md (Stable)
القاعدة: Incremental Update فقط — لا إعادة بناء، لا تغيير GitHub/Railway/Telegram/Webhook.

## المهام
- [x] **1. إصلاح إرسال صور طلبات الزوار إلى Telegram Bot**
  - المشكلة: الإشعار الأصلي يصل بدون الصور (نص فقط)، والصور تصل منفصلة بلا أزرار.
  - الحل: إرفاق الصور فعلياً في رسالة الإشعار الأصلية (sendMediaGroup مع reply_markup غير مدعوم → إرسال صورة واحدة كـ sendPhoto مع caption + أزرار، أو إرسال الإشعار النصي بأزرار + الصور كرسالة منفصلة مرتبطة).
  - ربط الصور بالطلب في bot.py عند الموافقة (قراءة images من item).

- [x] **2. تحسين نظام Request Management**
  - عدم حذف الطلب بعد النشر (إزالة query.message.delete() في _approve_visitor_request).
  - إنشاء حالات: NEW, UNDER_REVIEW, APPROVED, PUBLISHING, PUBLISHED, ARCHIVED.
  - تحديث _approve_visitor_request لاستخدام هذه الحالات.
  - حفظ روابط الصور وربطها بالطلب.

- [x] **3. عند النشر — التحقق قبل رسالة النجاح**
  - التأكد من وجود العرض داخل الموقع (offers.json) — موجود فعلاً (verify_ok).
  - التأكد من القسم الصحيح.
  - حفظ المعرف الجديد (published_offer_id) — موجود فعلاً.
  - عدم إظهار رسالة النجاح إلا بعد التحقق — موجود فعلاً، يحتاج تحسين القسم.

- [x] **4. تحسين الخريطة**
  - وضع دبوس بالضغط.
  - تحريك الدبوس بالسحب.
  - حفظ Latitude Longitude.
  - إضافة مربع بحث.
  - إظهار العقارات على الخريطة.
  - (في list-property.html أو صفحة منفصلة + js)

- [x] **5. إضافة نظام التصنيف**
  - القسم + المنطقة + نوع العقار.
  - استخدامها في عرض العقارات بالموقع.
  - (في offers.json + main.js + صفحات العرض)

- [x] **6. نظام الإبلاغ عن الأخطاء**
  - أي مشكلة → smart_repair.py + AI Monitor مع تقرير نجاح/فشل.

- [x] **7. Commit + Push + Railway**
  - إنشاء فرع feature، commit، push، PR، دمج، التحقق من Railway.

- [x] **8. تقرير FINAL_REMAINING_TASKS.md**
