// js/compare.js (جديد)

class PropertyComparison {
    constructor() {
        this.selectedProperties = [];
    }

    addToCompare(property) {
        if (this.selectedProperties.length >= 3) {
            showToast('⚠️ يمكنك مقارنة 3 عقارات كحد أقصى.', 'warning');
            return;
        }

        if (this.selectedProperties.find(p => p.id === property.id)) {
            showToast('⚠️ هذا العقار مضاف للمقارنة بالفعل.', 'warning');
            return;
        }

        this.selectedProperties.push(property);
        this.updateCompareBar();
        showToast('✅ تم إضافة العقار للمقارنة.', 'success');
    }

    removeFromCompare(propertyId) {
        this.selectedProperties = this.selectedProperties.filter(p => p.id !== propertyId);
        this.updateCompareBar();
    }

    updateCompareBar() {
        let bar = document.getElementById('compare-bar');

        if (!bar) {
            bar = document.createElement('div');
            bar.id = 'compare-bar';
            bar.className = 'compare-bar';
            document.body.appendChild(bar);
        }

        if (this.selectedProperties.length === 0) {
            bar.style.display = 'none';
            return;
        }

        bar.style.display = 'block';
        bar.innerHTML = `
            <div class="compare-bar-content">
                <span>📊 مقارنة (${this.selectedProperties.length}/3)</span>
                <div class="compare-items">
                    ${this.selectedProperties.map(p => `
                        <div class="compare-item">
                            <img src="${(p.images && p.images[0]) ? p.images[0] : 'images/farms-bg.jpg'}" alt="${p.title || ''}">
                            <span>${(p.title || '').substring(0, 20)}...</span>
                            <button onclick="propertyComparison.removeFromCompare('${p.id}')">×</button>
                        </div>
                    `).join('')}
                </div>
                <button class="btn btn-primary" onclick="propertyComparison.showComparison()">
                    مقارنة الآن
                </button>
                <button class="btn btn-secondary" onclick="propertyComparison.clearAll()">
                    مسح الكل
                </button>
            </div>
        `;
    }

    showComparison() {
        if (this.selectedProperties.length < 2) {
            showToast('⚠️ يرجى اختيار عقارين على الأقل للمقارنة.', 'warning');
            return;
        }

        const modal = document.createElement('div');
        modal.className = 'modal-overlay comparison-modal';

        const props = this.selectedProperties;

        modal.innerHTML = `
            <div class="modal-content comparison-content">
                <h2>📊 مقارنة العقارات</h2>
                <div class="comparison-table-wrapper">
                    <table class="comparison-table">
                        <thead>
                            <tr>
                                <th>المعيار</th>
                                ${props.map(p => `
                                    <th>
                                        <img src="${(p.images && p.images[0]) ? p.images[0] : 'images/farms-bg.jpg'}" alt="${p.title || ''}">
                                        <div>${p.title || ''}</div>
                                    </th>
                                `).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>🏷️ النوع</td>
                                ${props.map(p => `<td>${p.category || p.type || ''}</td>`).join('')}
                            </tr>
                            <tr>
                                <td>📍 الموقع</td>
                                ${props.map(p => `<td>${p.area || ''}</td>`).join('')}
                            </tr>
                            <tr>
                                <td>📐 المساحة</td>
                                ${props.map(p => `<td>${Number(p.size_sqm || 0).toLocaleString('en-US')} م²</td>`).join('')}
                            </tr>
                            <tr>
                                <td>💰 السعر</td>
                                ${props.map(p => `<td class="price-cell">${p.price_text || ''}</td>`).join('')}
                            </tr>
                            <tr>
                                <td>✨ المميزات</td>
                                ${props.map(p => {
                                    const feats = Array.isArray(p.features) ? p.features : [];
                                    return `<td>${feats.slice(0, 3).join(', ')}${feats.length > 3 ? '...' : ''}</td>`;
                                }).join('')}
                            </tr>
                            <tr>
                                <td>📅 تاريخ الإضافة</td>
                                ${props.map(p => `<td>${p.date_added || ''}</td>`).join('')}
                            </tr>
                            <tr>
                                <td>🔗 الإجراءات</td>
                                ${props.map(p => `
                                    <td>
                                        <a href="?p=${p.id}" class="btn btn-sm btn-primary">عرض</a>
                                        <a href="${p.map_link || '#'}" target="_blank" class="btn btn-sm btn-secondary">خريطة</a>
                                    </td>
                                `).join('')}
                            </tr>
                        </tbody>
                    </table>
                </div>
                <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">إغلاق</button>
            </div>
        `;

        document.body.appendChild(modal);
    }

    clearAll() {
        this.selectedProperties = [];
        this.updateCompareBar();
    }
}

const propertyComparison = new PropertyComparison();
