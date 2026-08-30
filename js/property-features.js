// js/property-features.js (جديد)

const PROPERTY_FEATURES = [
    { id: 'land_area', label: 'مساحة الأرض', icon: '📐', unit: 'م²', type: 'number' },
    { id: 'building_area', label: 'مساحة البناء', icon: '🏗️', unit: 'م²', type: 'number' },
    { id: 'facade', label: 'الواجهة', icon: '🧭', type: 'select', options: ['شمال', 'جنوب', 'شرق', 'غرب', 'زاوية'] },
    { id: 'age', label: 'عمر العقار', icon: '📅', unit: 'سنة', type: 'number' },
    { id: 'finish_type', label: 'نوع التشطيب', icon: '✨', type: 'select', options: ['عادي', 'VIP', 'فاخر'] },
    { id: 'bedrooms', label: 'عدد الغرف', icon: '🛏️', type: 'number' },
    { id: 'bathrooms', label: 'عدد دورات المياه', icon: '🚿', type: 'number' },
    { id: 'floors', label: 'عدد الأدوار', icon: '🏢', type: 'number' },
    { id: 'parking', label: 'مواقف السيارات', icon: '🅿️', type: 'number' },
    { id: 'pool', label: 'مسبح', icon: '🏊', type: 'boolean' },
    { id: 'garden', label: 'حديقة', icon: '🌳', type: 'boolean' },
    { id: 'maid_room', label: 'غرفة خادمة', icon: '👩‍🍳', type: 'boolean' },
    { id: 'driver_room', label: 'غرفة سائق', icon: '🚗', type: 'boolean' },
    { id: 'elevator', label: 'مصعد', icon: '🛗', type: 'boolean' },
    { id: 'central_ac', label: 'تكييف مركزي', icon: '❄️', type: 'boolean' },
    { id: 'security', label: 'نظام أمني', icon: '🔒', type: 'boolean' },
    { id: 'cctv', label: 'كاميرات مراقبة', icon: '📹', type: 'boolean' },
    { id: 'fiber', label: 'إنترنت فايبر', icon: '🌐', type: 'boolean' },
    { id: 'water_tank', label: 'خزان ماء', icon: '💧', type: 'boolean' },
    { id: 'gas', label: 'غاز مركزي', icon: '🔥', type: 'boolean' },
    { id: 'electricity', label: 'كهرباء مستقلة', icon: '⚡', type: 'boolean' },
    { id: 'deed', label: 'صك إلكتروني', icon: '📜', type: 'boolean' },
    { id: 'permit', label: 'رخصة بناء', icon: '🏗️', type: 'boolean' },
    { id: 'approved_plan', label: 'مخطط معتمد', icon: '📋', type: 'boolean' },
    { id: 'commercial_street', label: 'شارع تجاري', icon: '🏪', type: 'boolean' },
    { id: 'near_mosque', label: 'قريب من المسجد', icon: '🕌', type: 'boolean' },
    { id: 'near_school', label: 'قريب من المدرسة', icon: '🎓', type: 'boolean' },
    { id: 'near_services', label: 'قريب من الخدمات', icon: '🏥', type: 'boolean' },
    { id: 'view', label: 'إطلالة', icon: '🌅', type: 'select', options: ['شارع', 'حديقة', 'مسبح', 'بحر'] },
    { id: 'corner', label: 'زاوية', icon: '🔷', type: 'boolean' },
    { id: 'duplex', label: 'دوبلكس', icon: '🏰', type: 'boolean' },
    { id: 'roof', label: 'روف', icon: '🌇', type: 'boolean' },
    { id: 'villa', label: 'فيلا منفصلة', icon: '🏡', type: 'boolean' },
    { id: 'apartment', label: 'شقة داخل عمارة', icon: '🏢', type: 'boolean' },
    { id: 'residential_land', label: 'أرض سكنية', icon: '📐', type: 'boolean' },
];

function renderPropertyFeatures(containerId, propertyFeatures = {}) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
        <div class="features-grid">
            ${PROPERTY_FEATURES.map(feature => {
                const value = propertyFeatures[feature.id];
                const isActive = value !== undefined && value !== false && value !== 0 && value !== '';

                return `
                    <div class="feature-item ${isActive ? 'active' : 'inactive'}">
                        <span class="feature-icon">${feature.icon}</span>
                        <span class="feature-label">${feature.label}</span>
                        ${isActive ? `
                            <span class="feature-value">
                                ${feature.type === 'boolean' ? '✓' : value}
                                ${feature.unit || ''}
                            </span>
                        ` : '<span class="feature-value">--</span>'}
                    </div>
                `;
            }).join('')}
        </div>
    `;
}
