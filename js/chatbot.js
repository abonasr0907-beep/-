// js/chatbot.js -- النسخة المحدثة

const AI_KNOWLEDGE = {
    // الأسئلة العامة
    "ما هو مكتب آفاق الإنجاز": "مكتب آفاق الإنجاز للخدمات العقارية هو مكتب متخصص في بيع وشراء العقارات في منطقة الخرج وضواحيها. نقدم خدمات شاملة تشمل: المزارع، الاستراحات، الأراضي السكنية، والعقارات التجارية.",
    "ما هي خدماتكم": "نقدم خدمات متنوعة تشمل:\n1. بيع وشراء العقارات\n2. إدارة العقارات\n3. استشارات عقارية\n4. تقييم عقاري\n5. التسويق العقاري",
    "كيف أتواصل معكم": "يمكنك التواصل معنا عبر:\n📱 واتساب: 0567890123\n📧 البريد: info@afaqalanjaz.com\n📍 العنوان: شارع الملك فهد، الخرج",

    // الأسئلة المتعلقة بالعقار الحالي
    "ما هو سعر هذا العقار": (context) => {
        if (context.currentProperty) {
            return `سعر هذا العقار هو: ${context.currentProperty.price_text}`;
        }
        return "يرجى اختيار عقار أولاً لمعرفة السعر.";
    },
    "ما هي مساحة هذا العقار": (context) => {
        if (context.currentProperty) {
            return `مساحة هذا العقار: ${context.currentProperty.size_sqm.toLocaleString('en-US')} متر مربع`;
        }
        return "يرجى اختيار عقار أولاً.";
    },
    "أين يقع هذا العقار": (context) => {
        if (context.currentProperty) {
            return `موقع العقار: ${context.currentProperty.area}`;
        }
        return "يرجى اختيار عقار أولاً.";
    },
    "ما هي مميزات هذا العقار": (context) => {
        if (context.currentProperty) {
            const features = context.currentProperty.features;
            if (Array.isArray(features) && features.length > 0) {
                return `مميزات العقار:\n${features.map(f => `• ${f}`).join('\n')}`;
            }
            return "لا توجد مميزات مسجلة لهذا العقار.";
        }
        return "يرجى اختيار عقار أولاً.";
    },

    // المقارنات
    "قارن لي بين عقارين": (context) => {
        return "يمكنك استخدام أداة المقارنة. أرسل 'مقارنة' ثم اختر العقارين.";
    },

    // التمويل
    "كيف أحسب التمويل": (context) => {
        return "يمكنك استخدام حاسبة التمويل. أرسل 'تمويل' لبدء الحساب.";
    },

    // الحجز
    "أريد حجز موعد": (context) => {
        return "لحجز موعد للمعاينة، يرجى إرسال:\n1. اسمك\n2. رقم هاتفك\n3. التاريخ والوقت المفضل\n4. العقار المراد معاينته";
    },
};

// سياق المحادثة
let chatContext = {
    currentProperty: null,
    lastQuestion: null,
    userName: null,
    userPhone: null,
};

function setChatContext(property) {
    chatContext.currentProperty = property;
}

function getAIResponse(input) {
    const normalized = input.toLowerCase().trim();

    // البحث في المعرفة
    for (const [question, answer] of Object.entries(AI_KNOWLEDGE)) {
        if (normalized.includes(question.toLowerCase()) ||
            calculateSimilarity(normalized, question.toLowerCase()) > 0.7) {
            return typeof answer === 'function' ? answer(chatContext) : answer;
        }
    }

    // رد افتراضي
    return "شكراً لسؤالك! يمكنني مساعدتك في:\n• معلومات عن العقارات\n• المقارنات\n• حاسبة التمويل\n• حجز موعد\n• التواصل مع المكتب\n\nما الذي تريد معرفته؟";
}

// دالة حساب التشابه (بسيطة)
function calculateSimilarity(str1, str2) {
    const words1 = str1.split(' ');
    const words2 = str2.split(' ');
    const common = words1.filter(w => words2.includes(w));
    return common.length / Math.max(words1.length, words2.length);
}
