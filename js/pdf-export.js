// js/pdf-export.js (جديد)

class PDFExporter {
    async exportProperty(property) {
        if (!property) return;

        // استخدام مكتبة html2pdf.js أو jsPDF
        // يجب إضافة المكتبة في index.html:
        // <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

        const content = document.createElement('div');
        const priceText = property.price_text || (property.price ? `${property.price.toLocaleString('en-US')} SAR` : 'حسب السوم');
        const sizeSqm = property.size_sqm ? property.size_sqm.toLocaleString('en-US') : (property.area_sqm ? property.area_sqm.toLocaleString('en-US') : 'غير محدد');
        const features = Array.isArray(property.features) ? property.features : [];

        content.innerHTML = `
            <div style="padding: 40px; font-family: Arial, sans-serif; direction: rtl;">
                <div style="text-align: center; margin-bottom: 30px;">
                    <img src="images/logo.png" style="width: 100px;" alt="Logo" onerror="this.src='images/logo.jpg'" />
                    <h1 style="color: #d4af37;">آفاق الإنجاز للخدمات العقارية</h1>
                    <p>تقرير عقاري رسمي</p>
                </div>

                <div style="border: 2px solid #d4af37; padding: 20px; margin-bottom: 20px;">
                    <h2 style="color: #d4af37;">${property.title || 'عقار مميز'}</h2>
                    <p><strong>السعر:</strong> ${priceText}</p>
                    <p><strong>الموقع:</strong> ${property.area || property.location || 'غير محدد'}</p>
                    <p><strong>المساحة:</strong> ${sizeSqm} م²</p>
                    <p><strong>النوع:</strong> ${property.category || property.type || 'عقار'}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="color: #d4af37;">الوصف</h3>
                    <p>${property.description || 'لا يوجد وصف'}</p>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="color: #d4af37;">المميزات</h3>
                    <ul>
                        ${features.map(f => `<li>${f}</li>`).join('')}
                    </ul>
                </div>

                <div style="text-align: center; margin-top: 40px; border-top: 1px solid #ccc; padding-top: 20px;">
                    <p>📱 للتواصل: 0567890123</p>
                    <p>📧 info@afaqalanjaz.com</p>
                    <p>🌐 www.afaqalanjaz.com</p>
                </div>
            </div>
        `;

        const opt = {
            margin: 10,
            filename: `عقار_${property.id || 'export'}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        if (typeof html2pdf !== 'undefined') {
            await html2pdf().set(opt).from(content).save();
        } else {
            console.warn('html2pdf library is not loaded');
        }
    }
}

const pdfExporter = new PDFExporter();
