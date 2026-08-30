// js/booking.js (جديد)

class BookingSystem {
    constructor() {
        this.bookings = JSON.parse(localStorage.getItem('afaq_bookings') || '[]');
    }

    addBooking(booking) {
        booking.id = `BOOK-${Date.now()}`;
        booking.status = 'pending';
        booking.createdAt = new Date().toISOString();

        this.bookings.push(booking);
        this.save();

        // إرسال إشعار للبوت
        this.notifyAdmin(booking);

        return booking;
    }

    save() {
        localStorage.setItem('afaq_bookings', JSON.stringify(this.bookings));
    }

    async notifyAdmin(booking) {
        try {
            await fetch('/api/bookings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(booking)
            });
        } catch (e) {
            console.warn('Failed to notify admin:', e);
        }
    }

    renderBookingForm(containerId, propertyId = null) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="booking-form glass-card">
                <h3>📅 حجز موعد للمعاينة</h3>
                <form id="booking-form">
                    <div class="form-group">
                        <label>الاسم الكامل *</label>
                        <input type="text" id="booking-name" required placeholder="محمد أحمد">
                    </div>
                    <div class="form-group">
                        <label>رقم الهاتف *</label>
                        <input type="tel" id="booking-phone" required placeholder="05xxxxxxxx">
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" id="booking-email" placeholder="example@email.com">
                    </div>
                    <div class="form-group">
                        <label>التاريخ المفضل *</label>
                        <input type="date" id="booking-date" required min="${new Date().toISOString().split('T')[0]}">
                    </div>
                    <div class="form-group">
                        <label>الوقت المفضل *</label>
                        <select id="booking-time" required>
                            <option value="">اختر الوقت</option>
                            <option value="09:00">9:00 صباحاً</option>
                            <option value="10:00">10:00 صباحاً</option>
                            <option value="11:00">11:00 صباحاً</option>
                            <option value="14:00">2:00 مساءً</option>
                            <option value="15:00">3:00 مساءً</option>
                            <option value="16:00">4:00 مساءً</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>ملاحظات</label>
                        <textarea id="booking-notes" rows="3" placeholder="أي ملاحظات إضافية..."></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-calendar-check"></i> تأكيد الحجز
                    </button>
                </form>
            </div>
        `;

        document.getElementById('booking-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleSubmit(propertyId);
        });
    }

    handleSubmit(propertyId) {
        const booking = {
            name: document.getElementById('booking-name').value,
            phone: document.getElementById('booking-phone').value,
            email: document.getElementById('booking-email').value,
            date: document.getElementById('booking-date').value,
            time: document.getElementById('booking-time').value,
            notes: document.getElementById('booking-notes').value,
            propertyId: propertyId,
        };

        this.addBooking(booking);

        showToast('✅ تم حجز الموعد بنجاح! سنتواصل معك قريباً.', 'success');

        // إعادة تعيين النموذج
        document.getElementById('booking-form').reset();
    }
}

const bookingSystem = new BookingSystem();
