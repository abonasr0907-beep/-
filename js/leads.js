/* js/leads.js - Phase M3 Silent Leads Form Ingestion */

(function() {
  'use strict';

  const INGEST_SECRET = 'a8f9c2d1e3b4a7065983412098734561';

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', injectSilentFormsContainer);
  } else {
    injectSilentFormsContainer();
  }

  function injectSilentFormsContainer() {
    if (document.getElementById('silent-leads-container')) return;

    let target = document.querySelector('footer');

    const wrapper = document.createElement('div');
    wrapper.className = 'silent-leads-container';
    wrapper.id = 'silent-leads-container';

    wrapper.innerHTML = `
      <!-- Section 1: Connect Me To A Property -->
      <div class="lead-section-card" id="section-lead">
        <div class="lead-card-header">
          <h2><i class="fas fa-bullhorn" style="color:#C5A059;"></i> أوصلني بعقار (طلب خاص)</h2>
          <p>لم تجد طلبك بالموقع؟ أدخل مواصفاتك وسنقوم بالبحث الميداني وتزويدك بأفضل العروض المتاحة.</p>
        </div>
        <form class="lead-form" onsubmit="handleLeadSubmit(event, 'lead')">
          <div class="lead-form-grid">
            <div class="lead-form-group">
              <label for="lead-category">فئة العقار</label>
              <select id="lead-category" required>
                <option value="">اختر الفئة...</option>
                <option value="مزرعة">مزرعة</option>
                <option value="استراحة">استراحة / شاليه</option>
                <option value="أرض سكنية">أرض سكنية</option>
                <option value="عقار تجاري">عقار تجاري</option>
              </select>
            </div>

            <div class="lead-form-group">
              <label for="lead-budget">الميزانية التقريبية (ريال)</label>
              <input type="text" id="lead-budget" placeholder="مثال: 500,000" required>
            </div>

            <div class="lead-form-group">
              <label for="lead-area">المنطقة / الحي المطلوب</label>
              <input type="text" id="lead-area" placeholder="مثال: الخرج - الدلم، أو الرياض - شمال" required>
            </div>

            <div class="lead-form-group">
              <label for="lead-phone">رقم الجوال (للتواصل)</label>
              <input type="tel" id="lead-phone" placeholder="05xxxxxxxx" pattern="05[0-9]{8}" required>
            </div>

            <button type="submit" class="lead-submit-btn">
              <i class="fas fa-paper-plane"></i> إرسال الطلب الآن
            </button>
          </div>
        </form>
        <div class="lead-success-message" id="success-lead">
          <p><i class="fas fa-check-circle"></i> تم إرسال طلبك بنجاح! سيتواصل معك مستشارك العقاري قريباً.</p>
          <a href="https://wa.me/966545888931" target="_blank" class="lead-wa-btn">
            <i class="fab fa-whatsapp"></i> مراجعة الطلب فوراً عبر واتساب
          </a>
        </div>
      </div>

      <!-- Section 2: Free Property Valuation -->
      <div class="lead-section-card" id="section-valuation">
        <div class="lead-card-header">
          <h2><i class="fas fa-calculator" style="color:#C5A059;"></i> قيّم عقارك مجاناً</h2>
          <p>أدخل بيانات عقارك بالخرج أو الرياض ليقوم خبراؤنا بتقدير القيمة السوقية العادلة مجاناً.</p>
        </div>
        <form class="lead-form" onsubmit="handleLeadSubmit(event, 'valuation')">
          <div class="lead-form-grid">
            <div class="lead-form-group">
              <label for="val-type">نوع العقار</label>
              <select id="val-type" required>
                <option value="">اختر النوع...</option>
                <option value="مزرعة">مزرعة</option>
                <option value="استراحة">استراحة</option>
                <option value="أرض">أرض</option>
                <option value="عمائر/مباني">عمائر / مباني</option>
              </select>
            </div>

            <div class="lead-form-group">
              <label for="val-location">الموقع التفصيلي</label>
              <input type="text" id="val-location" placeholder="مثال: الخرج - مخطط 101" required>
            </div>

            <div class="lead-form-group">
              <label for="val-size">المساحة الإجمالية (م²)</label>
              <input type="text" id="val-size" placeholder="مثال: 10,000 م²" required>
            </div>

            <div class="lead-form-group">
              <label for="val-phone">رقم الجوال</label>
              <input type="tel" id="val-phone" placeholder="05xxxxxxxx" pattern="05[0-9]{8}" required>
            </div>

            <button type="submit" class="lead-submit-btn">
              <i class="fas fa-chart-line"></i> طلب التقييم المجاني
            </button>
          </div>
        </form>
        <div class="lead-success-message" id="success-valuation">
          <p><i class="fas fa-check-circle"></i> تم استقبال طلب التقييم بنجاح! سيتم إعداد التقرير المبدئي والتواصل معكم.</p>
          <a href="https://wa.me/966545888931" target="_blank" class="lead-wa-btn">
            <i class="fab fa-whatsapp"></i> استفسار مباشر عبر واتساب
          </a>
        </div>
      </div>

      <!-- Section 3: Booking Inspection -->
      <div class="lead-section-card" id="section-booking">
        <div class="lead-card-header">
          <h2><i class="fas fa-calendar-check" style="color:#C5A059;"></i> حجز معاينة ميدانية</h2>
          <p>حدد الموعد المناسب لك لمرافقة خبيرنا العقاري ومعاينة العقار على أرض الواقع.</p>
        </div>
        <form class="lead-form" onsubmit="handleLeadSubmit(event, 'booking')">
          <div class="lead-form-grid">
            <div class="lead-form-group">
              <label for="book-date">التاريخ المفضل للمعاينة</label>
              <input type="date" id="book-date" required>
            </div>

            <div class="lead-form-group">
              <label for="book-period">الفترة المفضلة</label>
              <select id="book-period" required>
                <option value="صباحاً (9 ص - 12 ظ)">صباحاً (9 ص - 12 ظ)</option>
                <option value="عصراً (4 م - 6 م)">عصراً (4 م - 6 م)</option>
                <option value="مساءً (7 م - 9 م)">مساءً (7 م - 9 م)</option>
              </select>
            </div>

            <div class="lead-form-group">
              <label for="book-name">الاسم الكريم</label>
              <input type="text" id="book-name" placeholder="الاسم الكامل" required>
            </div>

            <div class="lead-form-group">
              <label for="book-phone">رقم الجوال</label>
              <input type="tel" id="book-phone" placeholder="05xxxxxxxx" pattern="05[0-9]{8}" required>
            </div>

            <button type="submit" class="lead-submit-btn">
              <i class="fas fa-clock"></i> تأكيد حجز الموعد
            </button>
          </div>
        </form>
        <div class="lead-success-message" id="success-booking">
          <p><i class="fas fa-check-circle"></i> تم حجز موعدك بنجاح! سنقوم بالتواصل لتأكيد التفاصيل والموقع الميداني.</p>
          <a href="https://wa.me/966545888931" target="_blank" class="lead-wa-btn">
            <i class="fab fa-whatsapp"></i> تأكيد الموعد عبر واتساب
          </a>
        </div>
      </div>
    `;

    if (target) {
      target.parentNode.insertBefore(wrapper, target);
    } else {
      document.body.appendChild(wrapper);
    }
  }

  window.handleLeadSubmit = function(e, kind) {
    e.preventDefault();

    let payload = {
      kind: kind,
      timestamp: new Date().toISOString(),
      page: window.location.pathname
    };

    if (kind === 'lead') {
      payload.category = document.getElementById('lead-category').value;
      payload.budget = document.getElementById('lead-budget').value;
      payload.area = document.getElementById('lead-area').value;
      payload.phone = document.getElementById('lead-phone').value;
    } else if (kind === 'valuation') {
      payload.type = document.getElementById('val-type').value;
      payload.location = document.getElementById('val-location').value;
      payload.size = document.getElementById('val-size').value;
      payload.phone = document.getElementById('val-phone').value;
    } else if (kind === 'booking') {
      payload.date = document.getElementById('book-date').value;
      payload.period = document.getElementById('book-period').value;
      payload.name = document.getElementById('book-name').value;
      payload.phone = document.getElementById('book-phone').value;
    }

    // Always show success message silently regardless of network outcome
    const form = e.target;
    const successDiv = document.getElementById('success-' + kind);

    if (form) form.style.display = 'none';
    if (successDiv) successDiv.style.display = 'block';

    // POST to /ingest with X-Ingest-Secret
    fetch('/ingest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Ingest-Secret': INGEST_SECRET
      },
      body: JSON.stringify(payload)
    }).catch(err => {
      // Silent error - success message stays visible
      console.log('Silent ingest dispatch');
    });
  };
})();
