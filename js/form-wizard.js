/**
 * PropertyFormWizard - Smart Property Listing Wizard v2.0
 * Handles step-by-step listing creation for Rest Houses, Farms, and Residential Lands.
 */

class PropertyFormWizard {
  constructor() {
    this.currentStep = 1;
    this.totalSteps = 5;
    this.formData = {
      propertyType: null,
      location: null,
      area: null,
      details: {},
      images: [],
      mapLocation: null
    };
    this.init();
  }

  static AREAS = {
    restHouse: [2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000, 7500, 8000, 8500, 9000, 9500, 10000],
    farm: [5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000, 45000, 50000, 55000, 60000, 65000, 70000, 75000, 80000, 85000, 90000, 95000, 100000, 105000, 110000, 115000, 120000, 125000, 130000],
    residential: [5000, 10000]
  };

  static LOCATIONS = ['الرحمانية', 'الهياثم', 'الدلم', 'الضبيعة', 'العفجة'];

  static arabicToEnglish(str) {
    if (!str) return '';
    const arabicNums = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
    const englishNums = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'];
    let result = String(str);
    for (let i = 0; i < 10; i++) {
      result = result.replace(new RegExp(arabicNums[i], 'g'), englishNums[i]);
    }
    return result;
  }

  init() {
    this.renderWizard();
    this.bindEvents();
  }

  renderWizard() {
    const container = document.getElementById('form-wizard');
    if (!container) return;

    container.innerHTML = `
      <div class="wizard-container" style="background:rgba(26,26,46,0.85);backdrop-filter:blur(16px);border:1px solid rgba(255,255,255,0.18);border-radius:24px;padding:30px;max-width:750px;margin:0 auto;color:#fff;direction:rtl;text-align:right;box-shadow:0 8px 32px rgba(0,0,0,0.37);">
        <div class="wizard-steps" style="display:flex;justify-content:space-between;margin-bottom:30px;position:relative;">
          ${[1, 2, 3, 4, 5].map(i => `
            <div class="wizard-step ${i === 1 ? 'active' : ''}" data-step="${i}" style="width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,0.1);border:2px solid rgba(255,255,255,0.2);display:flex;align-items:center;justify-content:center;font-weight:700;z-index:1;transition:all 0.3s ease;">
              ${i}
            </div>
          `).join('')}
        </div>
        <div class="wizard-content" id="wizard-content" style="min-height:300px;"></div>
        <div class="wizard-buttons" style="display:flex;justify-content:space-between;margin-top:30px;gap:15px;">
          <button class="glass-btn" id="wizard-prev" style="visibility:hidden;background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:#fff;padding:10px 24px;border-radius:12px;cursor:pointer;">السابق</button>
          <button class="glass-btn" id="wizard-next" style="background:linear-gradient(135deg, #D4AF37, #B8860B);border:none;color:#1a1a2e;font-weight:700;padding:10px 28px;border-radius:12px;cursor:pointer;">التالي</button>
        </div>
      </div>
    `;
    this.renderStep(1);
  }

  renderStep(step) {
    const content = document.getElementById('wizard-content');
    if (!content) return;

    switch (step) {
      case 1:
        this.renderStep1(content);
        break;
      case 2:
        this.renderStep2(content);
        break;
      case 3:
        this.renderStep3(content);
        break;
      case 4:
        this.renderStep4(content);
        break;
      case 5:
        this.renderStep5(content);
        break;
    }
  }

  renderStep1(content) {
    content.innerHTML = `
      <h3 style="color:#D4AF37;margin-bottom:20px;text-align:center;font-size:1.4rem;">الخطوة 1: اختر نوع العقار</h3>
      <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));gap:15px;">
        <button type="button" class="glass-btn property-type-btn ${this.formData.propertyType === 'استراحة' ? 'selected' : ''}" data-type="استراحة" style="padding:25px;text-align:center;font-size:1.1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(212,175,55,0.3);color:#fff;border-radius:16px;cursor:pointer;transition:all 0.3s ease;">
          🏡 استراحة
        </button>
        <button type="button" class="glass-btn property-type-btn ${this.formData.propertyType === 'أرض سكنية' ? 'selected' : ''}" data-type="أرض سكنية" style="padding:25px;text-align:center;font-size:1.1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(212,175,55,0.3);color:#fff;border-radius:16px;cursor:pointer;transition:all 0.3s ease;">
          🏞️ أرض سكنية
        </button>
        <button type="button" class="glass-btn property-type-btn ${this.formData.propertyType === 'مزرعة' ? 'selected' : ''}" data-type="مزرعة" style="padding:25px;text-align:center;font-size:1.1rem;background:rgba(255,255,255,0.06);border:1px solid rgba(212,175,55,0.3);color:#fff;border-radius:16px;cursor:pointer;transition:all 0.3s ease;">
          🌾 مزرعة
        </button>
      </div>
    `;

    content.querySelectorAll('.property-type-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        content.querySelectorAll('.property-type-btn').forEach(b => {
          b.style.background = 'rgba(255,255,255,0.06)';
          b.style.borderColor = 'rgba(212,175,55,0.3)';
        });
        const target = e.currentTarget;
        target.style.background = 'rgba(212,175,55,0.2)';
        target.style.borderColor = '#D4AF37';
        this.formData.propertyType = target.dataset.type;
      });
    });
  }

  renderStep2(content) {
    const areas = PropertyFormWizard.AREAS;
    let areaList = [];
    if (this.formData.propertyType === 'استراحة') areaList = areas.restHouse;
    else if (this.formData.propertyType === 'مزرعة') areaList = areas.farm;
    else areaList = areas.residential;

    content.innerHTML = `
      <h3 style="color:#D4AF37;margin-bottom:20px;text-align:center;font-size:1.4rem;">الخطوة 2: اختر الموقع والمساحة</h3>

      <div style="margin-bottom:25px;">
        <label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:12px;font-weight:600;">📍 اختر الموقع:</label>
        <div class="area-buttons" id="location-buttons" style="display:flex;flex-wrap:wrap;gap:10px;">
          ${PropertyFormWizard.LOCATIONS.map(loc => `
            <button type="button" class="area-btn location-btn ${this.formData.location === loc ? 'selected' : ''}" data-value="${loc}" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:10px;padding:10px 18px;color:#fff;cursor:pointer;">${loc}</button>
          `).join('')}
          <button type="button" class="area-btn location-btn ${this.formData.location && !PropertyFormWizard.LOCATIONS.includes(this.formData.location) ? 'selected' : ''}" data-value="other" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:10px;padding:10px 18px;color:#fff;cursor:pointer;">منطقة أخرى</button>
        </div>
        <input type="text" id="custom-location" placeholder="اكتب اسم المنطقة" value="${this.formData.location && !PropertyFormWizard.LOCATIONS.includes(this.formData.location) ? this.formData.location : ''}" style="display:${this.formData.location && !PropertyFormWizard.LOCATIONS.includes(this.formData.location) ? 'block' : 'none'};width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(212,175,55,0.4);border-radius:10px;color:#fff;margin-top:12px;box-sizing:border-box;">
      </div>

      <div style="margin-bottom:20px;">
        <label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:12px;font-weight:600;">📐 المساحة (م²):</label>
        <div class="area-buttons" id="area-buttons" style="display:flex;flex-wrap:wrap;gap:8px;max-height:200px;overflow-y:auto;padding:5px;">
          ${areaList.map(a => `
            <button type="button" class="area-btn area-select-btn ${this.formData.area === a ? 'selected' : ''}" data-value="${a}" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;color:#fff;cursor:pointer;font-size:0.9rem;">${a.toLocaleString('en-US')}</button>
          `).join('')}
          <button type="button" class="area-btn area-select-btn" data-value="other" style="background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;padding:8px 14px;color:#fff;cursor:pointer;font-size:0.9rem;">مساحة أخرى</button>
        </div>
        <input type="text" id="custom-area" placeholder="اكتب المساحة بالأرقام" value="${this.formData.area || ''}" style="display:none;width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(212,175,55,0.4);border-radius:10px;color:#fff;margin-top:12px;box-sizing:border-box;">
      </div>
    `;

    content.querySelectorAll('.location-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        content.querySelectorAll('.location-btn').forEach(b => {
          b.style.background = 'rgba(255,255,255,0.08)';
          b.style.borderColor = 'rgba(255,255,255,0.15)';
        });
        const target = e.currentTarget;
        target.style.background = 'rgba(212,175,55,0.2)';
        target.style.borderColor = '#D4AF37';

        const customLocInput = document.getElementById('custom-location');
        if (target.dataset.value === 'other') {
          customLocInput.style.display = 'block';
        } else {
          customLocInput.style.display = 'none';
          this.formData.location = target.dataset.value;
        }
      });
    });

    document.getElementById('custom-location')?.addEventListener('input', (e) => {
      this.formData.location = e.target.value.trim();
    });

    content.querySelectorAll('.area-select-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        content.querySelectorAll('.area-select-btn').forEach(b => {
          b.style.background = 'rgba(255,255,255,0.08)';
          b.style.borderColor = 'rgba(255,255,255,0.15)';
        });
        const target = e.currentTarget;
        target.style.background = 'rgba(212,175,55,0.2)';
        target.style.borderColor = '#D4AF37';

        const customAreaInput = document.getElementById('custom-area');
        if (target.dataset.value === 'other') {
          customAreaInput.style.display = 'block';
        } else {
          customAreaInput.style.display = 'none';
          this.formData.area = parseInt(target.dataset.value, 10);
        }
      });
    });

    document.getElementById('custom-area')?.addEventListener('input', (e) => {
      let val = PropertyFormWizard.arabicToEnglish(e.target.value);
      e.target.value = val;
      this.formData.area = parseInt(val, 10) || 0;
    });
  }

  renderStep3(content) {
    const type = this.formData.propertyType;
    let questions = [];

    if (type === 'استراحة') {
      questions = [
        { key: 'rooms', label: 'عدد الغرف', type: 'number' },
        { key: 'majlis', label: 'عدد المجالس', type: 'number' },
        { key: 'livestock', label: 'أماكن مخصصة للحلال', type: 'yesno' },
        { key: 'parking', label: 'موقف سيارات خاص', type: 'yesno' },
        { key: 'kidsArea', label: 'أماكن مخصصة للأطفال', type: 'yesno' },
        { key: 'design', label: 'التصميم', type: 'choice', options: ['عادي', 'VIP'] },
        { key: 'greenArea', label: 'مسطحات خضراء', type: 'yesno' },
        { key: 'tank', label: 'خزان', type: 'yesno' },
        { key: 'palmTrees', label: 'نخيل وأشجار', type: 'yesno' },
        { key: 'artesianWell', label: 'بئر ارتوازية', type: 'yesno' },
        { key: 'fertileSoil', label: 'التربة صالحة للزراعة', type: 'yesno' }
      ];
    } else if (type === 'مزرعة') {
      questions = [
        { key: 'greenhouses', label: 'بيوت محمية', type: 'yesno_count' },
        { key: 'well', label: 'بئر', type: 'yesno' },
        { key: 'tanks', label: 'عدد الخزانات', type: 'number' },
        { key: 'wells', label: 'عدد الأبار الموجودة', type: 'number' },
        { key: 'pumps', label: 'عدد الغطاسات', type: 'number' },
        { key: 'design', label: 'التصميم', type: 'choice', options: ['عادي', 'VIP'] },
        { key: 'paved', label: 'مسفلة من الداخل', type: 'yesno' },
        { key: 'allCrops', label: 'قابلة لجميع أنواع الزراعة', type: 'yesno' }
      ];
    } else if (type === 'أرض سكنية') {
      questions = [
        { key: 'landType', label: 'نوع الأرض', type: 'choice', options: ['فضاء', 'مسورة'] }
      ];
    }

    let html = `<h3 style="color:#D4AF37;margin-bottom:20px;text-align:center;font-size:1.4rem;">الخطوة 3: تفاصيل ${type}</h3><div style="display:grid;gap:15px;max-height:380px;overflow-y:auto;padding-left:10px;">`;

    questions.forEach(q => {
      html += `<div style="background:rgba(255,255,255,0.03);padding:12px 16px;border-radius:12px;border:1px solid rgba(255,255,255,0.08);"><label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:8px;font-size:0.95rem;">${q.label}:</label>`;

      if (q.type === 'yesno' || q.type === 'yesno_count') {
        html += `
          <div class="yes-no-group" data-key="${q.key}" style="display:flex;gap:12px;">
            <button type="button" class="yes-no-btn yes" data-value="yes" style="flex:1;padding:8px;border:1px solid rgba(46,204,113,0.4);border-radius:8px;background:rgba(46,204,113,0.1);color:#2ECC71;cursor:pointer;">نعم</button>
            <button type="button" class="yes-no-btn no" data-value="no" style="flex:1;padding:8px;border:1px solid rgba(231,76,60,0.4);border-radius:8px;background:rgba(231,76,60,0.1);color:#e74c3c;cursor:pointer;">لا</button>
          </div>
        `;
        if (q.type === 'yesno_count') {
          html += `<input type="text" class="count-input" data-key="${q.key}_count" placeholder="عدد البيوت المحمية" style="display:none;width:100%;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(212,175,55,0.4);border-radius:8px;color:#fff;margin-top:8px;box-sizing:border-box;">`;
        }
      } else if (q.type === 'number') {
        html += `<input type="text" class="detail-input" data-key="${q.key}" placeholder="أدخل العدد" style="width:100%;padding:10px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.15);border-radius:8px;color:#fff;box-sizing:border-box;">`;
      } else if (q.type === 'choice') {
        html += `<div class="area-buttons" style="display:flex;gap:10px;">${q.options.map(opt => `<button type="button" class="area-btn choice-btn" data-key="${q.key}" data-value="${opt}" style="flex:1;padding:8px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;color:#fff;cursor:pointer;">${opt}</button>`).join('')}</div>`;
      }
      html += `</div>`;
    });

    if (type === 'أرض سكنية') {
      html += `
        <div id="walled-questions" style="display:none;margin-top:15px;padding-top:15px;border-top:1px solid rgba(212,175,55,0.3);">
          <h4 style="color:#D4AF37;margin-bottom:12px;">تفاصيل الأرض المسورة:</h4>
      `;
      const walledQuestions = [
        { key: 'electricity', label: 'عداد كهرباء', type: 'yesno' },
        { key: 'streets', label: 'عدد الشوارع', type: 'choice', options: ['شارع', 'شارعين', 'ثلاثة شوارع', 'أربعة شوارع'] },
        { key: 'well', label: 'بئر', type: 'yesno' },
        { key: 'waterTank', label: 'خزان مياه', type: 'yesno' }
      ];
      walledQuestions.forEach(q => {
        html += `<div style="background:rgba(255,255,255,0.03);padding:12px 16px;border-radius:12px;margin-bottom:10px;border:1px solid rgba(255,255,255,0.08);"><label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:8px;font-size:0.95rem;">${q.label}:</label>`;
        if (q.type === 'yesno') {
          html += `
            <div class="yes-no-group" data-key="${q.key}" style="display:flex;gap:12px;">
              <button type="button" class="yes-no-btn yes" data-value="yes" style="flex:1;padding:8px;border:1px solid rgba(46,204,113,0.4);border-radius:8px;background:rgba(46,204,113,0.1);color:#2ECC71;cursor:pointer;">نعم</button>
              <button type="button" class="yes-no-btn no" data-value="no" style="flex:1;padding:8px;border:1px solid rgba(231,76,60,0.4);border-radius:8px;background:rgba(231,76,60,0.1);color:#e74c3c;cursor:pointer;">لا</button>
            </div>
          `;
        } else if (q.type === 'choice') {
          html += `<div class="area-buttons" style="display:flex;flex-wrap:wrap;gap:8px;">${q.options.map(opt => `<button type="button" class="area-btn choice-btn" data-key="${q.key}" data-value="${opt}" style="padding:8px 14px;background:rgba(255,255,255,0.08);border:1px solid rgba(255,255,255,0.15);border-radius:8px;color:#fff;cursor:pointer;">${opt}</button>`).join('')}</div>`;
        }
        html += `</div>`;
      });
      html += `</div>`;
    }

    html += `</div>`;
    content.innerHTML = html;

    content.querySelectorAll('.yes-no-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const group = e.target.closest('.yes-no-group');
        group.querySelectorAll('.yes-no-btn').forEach(b => {
          b.style.opacity = '0.6';
          b.style.fontWeight = 'normal';
        });
        const target = e.currentTarget;
        target.style.opacity = '1';
        target.style.fontWeight = 'bold';

        const key = group.dataset.key;
        const isYes = target.dataset.value === 'yes';
        this.formData.details[key] = isYes;

        const countInput = content.querySelector(`.count-input[data-key="${key}_count"]`);
        if (countInput) {
          countInput.style.display = isYes ? 'block' : 'none';
        }
      });
    });

    content.querySelectorAll('.detail-input, .count-input').forEach(input => {
      input.addEventListener('input', (e) => {
        let val = PropertyFormWizard.arabicToEnglish(e.target.value);
        e.target.value = val;
        this.formData.details[e.target.dataset.key] = val;
      });
    });

    content.querySelectorAll('.choice-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const key = e.target.dataset.key;
        content.querySelectorAll(`.choice-btn[data-key="${key}"]`).forEach(b => {
          b.style.background = 'rgba(255,255,255,0.08)';
          b.style.borderColor = 'rgba(255,255,255,0.15)';
        });
        const target = e.currentTarget;
        target.style.background = 'rgba(212,175,55,0.2)';
        target.style.borderColor = '#D4AF37';
        this.formData.details[key] = target.dataset.value;

        if (key === 'landType' && this.formData.propertyType === 'أرض سكنية') {
          const walledSection = document.getElementById('walled-questions');
          if (walledSection) {
            walledSection.style.display = target.dataset.value === 'مسورة' ? 'block' : 'none';
          }
        }
      });
    });
  }

  renderStep4(content) {
    content.innerHTML = `
      <h3 style="color:#D4AF37;margin-bottom:20px;text-align:center;font-size:1.4rem;">الخطوة 4: الصور والموقع</h3>

      <div style="margin-bottom:20px;">
        <label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:10px;font-weight:600;">📷 رفع الصور (حتى 5 صور):</label>
        <input type="file" id="wizard-property-images" multiple accept="image/*" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.15);border-radius:10px;color:#fff;box-sizing:border-box;">
        <div id="wizard-image-preview" style="display:flex;gap:10px;margin-top:15px;flex-wrap:wrap;"></div>
      </div>

      <div style="margin-bottom:20px;">
        <label style="display:block;color:rgba(255,255,255,0.9);margin-bottom:10px;font-weight:600;">🗺️ خرائط Google (رابط إرشادي / إحداثيات):</label>
        <input type="text" id="wizard-map-link" placeholder="أدخل رابط موقع العقار أو اسم الشارع" value="${this.formData.mapLocation || ''}" style="width:100%;padding:12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.15);border-radius:10px;color:#fff;box-sizing:border-box;">
      </div>
    `;

    document.getElementById('wizard-property-images')?.addEventListener('change', (e) => {
      const files = Array.from(e.target.files).slice(0, 5);
      const preview = document.getElementById('wizard-image-preview');
      preview.innerHTML = '';
      this.formData.images = [];

      files.forEach(file => {
        const reader = new FileReader();
        reader.onload = (event) => {
          this.formData.images.push(event.target.result);
          preview.innerHTML += `
            <div style="width:80px;height:80px;border-radius:10px;overflow:hidden;border:2px solid #D4AF37;">
              <img src="${event.target.result}" style="width:100%;height:100%;object-fit:cover;">
            </div>
          `;
        };
        reader.readAsDataURL(file);
      });
    });

    document.getElementById('wizard-map-link')?.addEventListener('input', (e) => {
      this.formData.mapLocation = e.target.value.trim();
    });
  }

  renderStep5(content) {
    const details = this.formData.details;
    let features = [];

    const labels = {
      rooms: `${details.rooms} غرف`,
      majlis: `${details.majlis} مجالس`,
      livestock: 'أماكن مخصصة للحلال',
      parking: 'موقف سيارات خاص',
      kidsArea: 'أماكن للأطفال',
      design: `تصميم ${details.design}`,
      greenArea: 'مسطحات خضراء',
      tank: 'خزان مياه',
      palmTrees: 'نخيل وأشجار',
      artesianWell: 'بئر ارتوازية',
      fertileSoil: 'تربة صالحة للزراعة',
      greenhouses: `${details.greenhouses_count || ''} بيوت محمية`,
      well: 'بئر',
      tanks: `${details.tanks} خزانات`,
      wells: `${details.wells} آبار`,
      pumps: `${details.pumps} غطاسات`,
      paved: 'مسفلة من الداخل',
      allCrops: 'قابلة لجميع الزراعات',
      electricity: 'عداد كهرباء',
      streets: details.streets,
      waterTank: 'خزان مياه'
    };

    // Rule: Only affirmative / positive values appear in the summary card!
    for (let [key, value] of Object.entries(details)) {
      if (value === true || (value && value !== 'لا' && value !== 'no' && value !== 'فضاء')) {
        if (labels[key]) features.push(labels[key]);
      }
    }

    content.innerHTML = `
      <h3 style="color:#D4AF37;margin-bottom:20px;text-align:center;font-size:1.4rem;">الخطوة 5: مراجعة الطلب والتأكيد</h3>

      <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(212,175,55,0.3);border-radius:16px;padding:20px;margin-bottom:20px;">
        <h4 style="color:#D4AF37;margin-bottom:15px;font-size:1.1rem;border-bottom:1px solid rgba(255,255,255,0.1);padding-bottom:10px;">📋 ملخص بيانات العقار</h4>
        <table style="width:100%;color:rgba(255,255,255,0.9);line-height:2;">
          <tr><td style="width:40%;">نوع العقار:</td><td style="color:#fff;font-weight:700;">${this.formData.propertyType || 'غير حدد'}</td></tr>
          <tr><td>الموقع:</td><td style="color:#fff;font-weight:700;">${this.formData.location || 'غير محدد'}</td></tr>
          <tr><td>المساحة:</td><td style="color:#fff;font-weight:700;">${this.formData.area ? this.formData.area.toLocaleString('en-US') + ' م²' : 'غير محددة'}</td></tr>
          <tr><td>عدد الصور المرفقة:</td><td style="color:#fff;font-weight:700;">${this.formData.images.length} صور</td></tr>
        </table>
        ${features.length > 0 ? `
          <div style="margin-top:15px;padding-top:15px;border-top:1px solid rgba(255,255,255,0.1);">
            <h5 style="color:#D4AF37;margin-bottom:10px;">المميزات المسجلة:</h5>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
              ${features.map(f => `<span style="background:rgba(212,175,55,0.2);border:1px solid #D4AF37;color:#D4AF37;padding:4px 12px;border-radius:20px;font-size:0.85rem;">✓ ${f}</span>`).join('')}
            </div>
          </div>
        ` : ''}
      </div>

      <div style="background:rgba(46,204,113,0.15);border:1px solid #2ECC71;border-radius:12px;padding:15px;text-align:center;">
        <p style="color:#2ECC71;margin:0;font-weight:600;">✓ اضغط "إرسال الطلب" لإكمال إرسال البيانات فوراً لمكتب آفاق الإنجاز العقاري.</p>
      </div>
    `;
  }

  bindEvents() {
    document.getElementById('wizard-next')?.addEventListener('click', () => this.nextStep());
    document.getElementById('wizard-prev')?.addEventListener('click', () => this.prevStep());
  }

  nextStep() {
    if (this.currentStep === 1 && !this.formData.propertyType) {
      if (typeof window.showNotification === 'function') window.showNotification('يرجى اختيار نوع العقار أولاً', 'warning');
      else alert('يرجى اختيار نوع العقار أولاً');
      return;
    }

    if (this.currentStep < this.totalSteps) {
      this.currentStep++;
      this.updateSteps();
      this.renderStep(this.currentStep);
      document.getElementById('wizard-prev').style.visibility = 'visible';

      if (this.currentStep === this.totalSteps) {
        const nextBtn = document.getElementById('wizard-next');
        nextBtn.textContent = 'إرسال الطلب';
        nextBtn.style.background = 'linear-gradient(135deg, #2ECC71, #27AE60)';
        nextBtn.style.color = '#fff';
      }
    } else if (this.currentStep === this.totalSteps) {
      this.submitForm();
    }
  }

  prevStep() {
    if (this.currentStep > 1) {
      this.currentStep--;
      this.updateSteps();
      this.renderStep(this.currentStep);

      const nextBtn = document.getElementById('wizard-next');
      nextBtn.textContent = 'التالي';
      nextBtn.style.background = 'linear-gradient(135deg, #D4AF37, #B8860B)';
      nextBtn.style.color = '#1a1a2e';

      if (this.currentStep === 1) {
        document.getElementById('wizard-prev').style.visibility = 'hidden';
      }
    }
  }

  updateSteps() {
    document.querySelectorAll('.wizard-step').forEach(step => {
      const stepNum = parseInt(step.dataset.step, 10);
      step.style.background = 'rgba(255,255,255,0.1)';
      step.style.borderColor = 'rgba(255,255,255,0.2)';
      step.style.color = '#fff';

      if (stepNum === this.currentStep) {
        step.style.background = '#D4AF37';
        step.style.borderColor = '#D4AF37';
        step.style.color = '#1a1a2e';
      } else if (stepNum < this.currentStep) {
        step.style.background = '#2ECC71';
        step.style.borderColor = '#2ECC71';
        step.style.color = '#fff';
      }
    });
  }

  submitForm() {
    this.saveToArchive();
    if (typeof window.showNotification === 'function') {
      window.showNotification('تم إرسال طلبك بنجاح! سنتواصل معك قريباً.', 'success');
    } else {
      alert('تم إرسال طلبك بنجاح! سنتواصل معك قريباً.');
    }

    // Reset wizard state
    this.currentStep = 1;
    this.formData = { propertyType: null, location: null, area: null, details: {}, images: [], mapLocation: null };
    this.updateSteps();
    this.renderStep(1);

    const nextBtn = document.getElementById('wizard-next');
    if (nextBtn) {
      nextBtn.textContent = 'التالي';
      nextBtn.style.background = 'linear-gradient(135deg, #D4AF37, #B8860B)';
      nextBtn.style.color = '#1a1a2e';
    }
    document.getElementById('wizard-prev').style.visibility = 'hidden';
  }

  saveToArchive() {
    const archive = JSON.parse(localStorage.getItem('propertyArchive') || '[]');
    archive.push({
      ...this.formData,
      id: Date.now(),
      status: 'pending',
      date: new Date().toISOString()
    });
    localStorage.setItem('propertyArchive', JSON.stringify(archive));
  }
}

window.PropertyFormWizard = PropertyFormWizard;
