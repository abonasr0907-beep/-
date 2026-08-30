// js/recommendations.js (جديد)

class PropertyRecommender {
    constructor() {
        this.properties = [];
    }

    setProperties(properties) {
        this.properties = properties;
    }

    recommend(budget, area, type) {
        let filtered = this.properties.filter(p => p.status !== 'archived' && p.status !== 'sold' && p.status !== 'مباع');

        // فلترة حسب الميزانية (±20%)
        if (budget) {
            const minBudget = budget * 0.8;
            const maxBudget = budget * 1.2;
            filtered = filtered.filter(p => p.price >= minBudget && p.price <= maxBudget);
        }

        // فلترة حسب المنطقة
        if (area) {
            filtered = filtered.filter(p =>
                (p.area || '').toLowerCase().includes(area.toLowerCase())
            );
        }

        // فلترة حسب النوع
        if (type) {
            filtered = filtered.filter(p => p.type === type);
        }

        // ترتيب حسب الأقرب للميزانية
        if (budget) {
            filtered.sort((a, b) =>
                Math.abs((a.price || 0) - budget) - Math.abs((b.price || 0) - budget)
            );
        }

        return filtered.slice(0, 5);
    }

    renderRecommendationForm(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="recommendation-form glass-card">
                <h3>🔍 توصية عقارات ذكية</h3>
                <form id="recommendation-form">
                    <div class="form-group">
                        <label>الميزانية (SAR)</label>
                        <input type="number" id="rec-budget" placeholder="1000000">
                    </div>
                    <div class="form-group">
                        <label>المنطقة المفضلة</label>
                        <select id="rec-area">
                            <option value="">الكل</option>
                            <option value="الرحمانية">الرحمانية</option>
                            <option value="الهياثم">الهياثم</option>
                            <option value="الدلم">الدلم</option>
                            <option value="الضبيعة">الضبيعة</option>
                            <option value="العفجة">العفجة</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>نوع العقار</label>
                        <select id="rec-type">
                            <option value="">الكل</option>
                            <option value="farm">مزرعة</option>
                            <option value="resthouse">استراحة</option>
                            <option value="land">أرض سكنية</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-search"></i> البحث
                    </button>
                </form>
                <div id="recommendation-results" style="margin-top:20px;"></div>
            </div>
        `;

        document.getElementById('recommendation-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit();
        });
    }

    handleSubmit() {
        const budget = parseFloat(document.getElementById('rec-budget').value) || null;
        const area = document.getElementById('rec-area').value;
        const type = document.getElementById('rec-type').value;

        const recommendations = this.recommend(budget, area, type);

        const resultsDiv = document.getElementById('recommendation-results');

        if (recommendations.length === 0) {
            resultsDiv.innerHTML = '<p class="no-results">😔 لم نجد عقارات تطابق معاييرك. جرب تعديل البحث.</p>';
            return;
        }

        resultsDiv.innerHTML = `
            <h4>✨ عقارات موصى بها (${recommendations.length})</h4>
            <div class="recommendation-grid">
                ${recommendations.map(p => `
                    <div class="recommendation-card">
                        <img src="${(p.images && p.images[0]) ? p.images[0] : 'images/farms-bg.jpg'}" alt="${p.title || ''}">
                        <div class="rec-info">
                            <h5>${p.title || ''}</h5>
                            <p class="rec-price">${p.price_text || ''}</p>
                            <p class="rec-area">📍 ${p.area || ''} | 📐 ${Number(p.size_sqm || 0).toLocaleString('en-US')} م²</p>
                            <a href="?p=${p.id}" class="btn btn-sm btn-primary">عرض التفاصيل</a>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }
}

const propertyRecommender = new PropertyRecommender();
