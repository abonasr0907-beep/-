// js/marketing-phrases.js (جديد)

const MARKETING_PHRASES = {
    // كلمات مفتاحية -> عبارات تسويقية
    'مسبح': '🏊 فيلا بمسبح خاص -- استمتع بالرفاهية',
    'حديقة': '🌳 حديقة واسعة -- طبيعة في بيتك',
    'قريب من المسجد': '🕌 قريب من المسجد -- روحانية يومية',
    'قريب من المدرسة': '🎓 قريب من المدارس -- تعليم ممتاز لأطفالك',
    'شارع تجاري': '🏪 شارع تجاري -- فرصة استثمارية ذهبية',
    'زاوية': '🔷 زاوية -- مساحة إضافية وإطلالة مميزة',
    'دوبلكس': '🏰 دوبلكس فاخر -- مساحة معيشة مضاعفة',
    'روف': '🌇 روف بانورامي -- إطلالة ساحرة على المدينة',
    'مصعد': '🛗 مصعد -- راحة وسلاسة في التنقل',
    'تكييف مركزي': '❄️ تكييف مركزي -- برودة في كل زاوية',
    'نظام أمني': '🔒 نظام أمني متكامل -- أمان لعائلتك',
    'صك إلكتروني': '📜 صك إلكتروني -- أمان قانوني كامل',
    'غرفة خادمة': '👩‍🍳 غرفة خادمة -- راحة منزلية كاملة',
    'غرفة سائق': '🚗 غرفة سائق -- خصوصية وراحة',
    'موقف سيارات': '🅿️ موقف سيارات -- راحة وصول سهلة',
    'إنترنت فايبر': '🌐 إنترنت فايبر -- سرعة لا تتوقف',
};

function extractMarketingPhrases(property) {
    if (!property) return [];
    const phrases = [];
    const features = property.features || [];
    const description = property.description || '';

    // البحث في المميزات
    if (Array.isArray(features)) {
        features.forEach(feature => {
            const featureStr = String(feature).toLowerCase();
            for (const [keyword, phrase] of Object.entries(MARKETING_PHRASES)) {
                if (featureStr.includes(keyword.toLowerCase())) {
                    phrases.push(phrase);
                }
            }
        });
    }

    // البحث في الوصف
    const descLower = description.toLowerCase();
    for (const [keyword, phrase] of Object.entries(MARKETING_PHRASES)) {
        if (descLower.includes(keyword.toLowerCase()) && !phrases.includes(phrase)) {
            phrases.push(phrase);
        }
    }

    // عبارات افتراضية حسب النوع
    if (phrases.length === 0) {
        const defaults = {
            'farm': '🌾 مزرعة استثنائية -- فرصة لا تتكرر',
            'resthouse': '🏡 استراحة فاخرة -- استرخاء بأفضل صورة',
            'land': '📐 أرض استثمارية -- بناء مستقبلك يبدأ هنا',
        };
        phrases.push(defaults[property.type] || '🏠 عقار مميز -- فرصة استثنائية');
    }

    return phrases.slice(0, 3); // أقصى 3 عبارات
}

function renderMarketingPhrases(containerId, property) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const phrases = extractMarketingPhrases(property);

    container.innerHTML = phrases.map(phrase => `
        <div class="marketing-phrase">${phrase}</div>
    `).join('');
}
