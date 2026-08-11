# دليل إعادة الفهرسة في Google Search Console
# Google Search Console Re-indexing Guide

**الموقع:** https://abonasr0907-beep.github.io/-/  
**التاريخ:** 11 أغسطس 2025

---

## الخطوة 1: إضافة Sitemap

1. اذهب إلى [Google Search Console](https://search.google.com/search-console)
2. إذا لم يكن الموقع مضافاً، أضف خاصية جديدة:
   - اختر "URL prefix"
   - أدخل: `https://abonasr0907-beep.github.io/-/`
   - استخدم ملف التحقق: `googlec20a83d8c0150679.html` (موجود بالفعل في الموقع)
3. اذهب إلى **Sitemaps** من القائمة الجانبية
4. أدخل في حقل "Add a new sitemap":
   ```
   sitemap.xml
   ```
5. اضغط **Submit**
6. انتظر ظهور حالة "Success" بجانب الـ sitemap

---

## الخطوة 2: طلب فهرسة كل صفحة (URL Inspection)

لكل رابط من الروابط التالية، استخدم أداة **URL Inspection**:

1. في Search Console، الصق الرابط في شريط البحث العلوي
2. انتظر ظهور نتائج الفحص
3. اضغط **Request Indexing**
4. كرر للرابط التالي

### الروابط الـ 19 للفهرسة (بالترتيب الموصى به):

#### الأولوية القصوى (الصفحة الرئيسية + صفحات الهبوط الجديدة):

1. `https://abonasr0907-beep.github.io/-/`
2. `https://abonasr0907-beep.github.io/-/real-estate-riyadh/`
3. `https://abonasr0907-beep.github.io/-/real-estate-alkharj/`
4. `https://abonasr0907-beep.github.io/-/farms-riyadh/`
5. `https://abonasr0907-beep.github.io/-/farms-alkharj/`
6. `https://abonasr0907-beep.github.io/-/resthouses-riyadh/`
7. `https://abonasr0907-beep.github.io/-/resthouses-alkharj/`
8. `https://abonasr0907-beep.github.io/-/lands-riyadh/`
9. `https://abonasr0907-beep.github.io/-/lands-alkharj/`
10. `https://abonasr0907-beep.github.io/-/property-management-riyadh/`
11. `https://abonasr0907-beep.github.io/-/well-drilling-services/`
12. `https://abonasr0907-beep.github.io/-/well-location-services/`

#### الأولوية الثانية (الصفحات الرئيسية المُحدّثة):

13. `https://abonasr0907-beep.github.io/-/farms.html`
14. `https://abonasr0907-beep.github.io/-/resthouses.html`
15. `https://abonasr0907-beep.github.io/-/lands.html`
16. `https://abonasr0907-beep.github.io/-/services.html`
17. `https://abonasr0907-beep.github.io/-/contact.html`
18. `https://abonasr0907-beep.github.io/-/inquiry.html`
19. `https://abonasr0907-beep.github.io/-/list-property.html`

---

## الخطوة 3: مراقبة النتائج

بعد طلب إعادة الفهرسة:

- **خلال 24-48 ساعة:** ابدأ بمراقبة حالة الفهرسة في **Coverage** report
- **خلال 3-7 أيام:** معظم الصفحات يجب أن تظهر في نتائج البحث
- **خلال 1-2 أسبوع:** تحقق من أداء الكلمات المفتاحية في **Performance** report

### ما يجب مراقبته:

1. **Coverage** → تأكد من عدم وجود أخطاء (Errors)
2. **Sitemaps** → تأكد من أن جميع الروابط الـ 19 تم اكتشافها
3. **Performance** → ابحث عن الكلمات المفتاحية المستهدفة:
   - عقارات في الرياض
   - عقارات في الخرج
   - مزارع للبيع
   - استراحات للبيع
   - أراضي سكنية
   - إدارة الأملاك العقارية
   - حفر الآبار

---

## ملاحظات مهمة

- Google تفرض حدّاً يومياً على عدد طلبات الفهرسة (عادة 10-20 طلب/يوم)
- إذا وصلت للحد، انتظر 24 ساعة ثم أكمل بقية الروابط
- صفحات الهبوط الجديدة (11 صفحة) لم تُفهرس من قبل، لذا قد تستغرق وقتاً أطول
- البوت يعمل تلقائياً على تحديث `news.json` — هذا لا يؤثر على الفهرسة (التحديثات تتجاهلها GitHub Actions)

---

## Sitemap URL المباشر

```
https://abonasr0907-beep.github.io/-/sitemap.xml
```

---

*تم إنشاء هذا الدليل بواسطة SuperNinja Autonomous Agent*
