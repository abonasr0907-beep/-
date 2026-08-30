// js/faq.js (جديد)

const FAQ_DATA = [
    {
        question: "ما هي خطوات شراء عقار؟",
        answer: "خطوات شراء عقار:\n1. اختيار العقار المناسب\n2. زيارة المعاينة\n3. التفاوض على السعر\n4. توقيع العقد\n5. إتمام الصفقة"
    },
    {
        question: "هل تقدمون خدمة التقييم العقاري؟",
        answer: "نعم، نقدم خدمة التقييم العقاري المجاني لجميع عملائنا."
    },
    {
        question: "ما هي المناطق التي تغطونها؟",
        answer: "نغطي منطقة الخرج وضواحيها بما في ذلك: الرحمانية، الهياثم، الدلم، الضبيعة، العفجة."
    },
    {
        question: "هل يمكنني البيع من خلالكم؟",
        answer: "نعم، نقدم خدمة بيع العقارات بعمولة تنافسية."
    },
    {
        question: "ما هي طرق الدفع المتاحة؟",
        answer: "نقبل: التحويل البنكي، الشيكات، والدفع النقدي."
    },
];

function renderFAQ() {
    const container = document.getElementById('faq-container');
    if (!container) return;

    container.innerHTML = FAQ_DATA.map((item, index) => `
        <div class="faq-item">
            <div class="faq-question" onclick="toggleFAQ(${index})">
                <span>${item.question}</span>
                <i class="fas fa-chevron-down" id="faq-icon-${index}"></i>
            </div>
            <div class="faq-answer" id="faq-answer-${index}" style="display:none;">
                ${item.answer}
            </div>
        </div>
    `).join('');
}

function toggleFAQ(index) {
    const answer = document.getElementById(`faq-answer-${index}`);
    const icon = document.getElementById(`faq-icon-${index}`);

    if (answer.style.display === 'none') {
        answer.style.display = 'block';
        icon.style.transform = 'rotate(180deg)';
    } else {
        answer.style.display = 'none';
        icon.style.transform = 'rotate(0deg)';
    }
}
