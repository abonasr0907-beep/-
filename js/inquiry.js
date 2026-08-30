// js/inquiry.js (جديد)

class InquirySystem {
    constructor() {
        this.inquiries = JSON.parse(localStorage.getItem('afaq_inquiries') || '[]');
    }

    addInquiry(inquiry) {
        inquiry.id = `INQ-${Date.now()}`;
        inquiry.status = 'new';
        inquiry.createdAt = new Date().toISOString();

        this.inquiries.push(inquiry);
        this.save();

        // إرسال إشعار
        this.notifyAdmin(inquiry);

        return inquiry;
    }

    save() {
        localStorage.setItem('afaq_inquiries', JSON.stringify(this.inquiries));
    }

    async notifyAdmin(inquiry) {
        try {
            await fetch('/api/inquiries', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(inquiry)
            });
        } catch (e) {
            console.warn('Failed to notify admin:', e);
        }
    }

    renderInquiryButton(containerId, propertyId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <button class="btn btn-secondary" onclick="inquirySystem.showInquiryModal('${propertyId}')">
                <i class="fas fa-question-circle"></i> طلب مزيد من المعلومات
            </button>
        `;
    }

    showInquiryModal(propertyId) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content glass-card">
                <h3>📩 طلب مزيد من المعلومات</h3>
                <form id="inquiry-form">
                    <div class="form-group">
                        <label>الاسم *</label>
                        <input type="text" id="inquiry-name" required>
                    </div>
                    <div class="form-group">
                        <label>رقم الهاتف *</label>
                        <input type="tel" id="inquiry-phone" required>
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" id="inquiry-email">
                    </div>
                    <div class="form-group">
                        <label>السؤال *</label>
                        <textarea id="inquiry-question" rows="4" required></textarea>
                    </div>
                    <div class="modal-actions">
                        <button type="submit" class="btn btn-primary">إرسال</button>
                        <button type="button" class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">إلغاء</button>
                    </div>
                </form>
            </div>
        `;

        document.body.appendChild(modal);

        document.getElementById('inquiry-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit(propertyId, modal);
        });
    }

    handleSubmit(propertyId, modal) {
        const inquiry = {
            name: document.getElementById('inquiry-name').value,
            phone: document.getElementById('inquiry-phone').value,
            email: document.getElementById('inquiry-email').value,
            question: document.getElementById('inquiry-question').value,
            propertyId: propertyId,
        };

        this.addInquiry(inquiry);

        showToast('✅ تم إرسال سؤالك بنجاح! سنتواصل معك قريباً.', 'success');
        modal.remove();
    }
}

const inquirySystem = new InquirySystem();
