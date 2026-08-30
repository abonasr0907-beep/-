// js/mortgage-calculator.js (جديد)

class MortgageCalculator {
    renderCalculator(containerId) {
        const container = document.getElementById(containerId);
        if (!container) return;

        container.innerHTML = `
            <div class="mortgage-calculator glass-card">
                <h3>🏦 حاسبة التمويل العقاري</h3>
                <form id="mortgage-form">
                    <div class="form-group">
                        <label>سعر العقار (SAR) *</label>
                        <input type="number" id="mortgage-price" required min="100000" placeholder="1200000">
                    </div>
                    <div class="form-group">
                        <label>الدفعة الأولى (%)</label>
                        <input type="number" id="mortgage-downpayment" value="30" min="10" max="50">
                    </div>
                    <div class="form-group">
                        <label>مدة التمويل (سنة)</label>
                        <input type="number" id="mortgage-years" value="20" min="5" max="30">
                    </div>
                    <div class="form-group">
                        <label>نسبة الفائدة السنوية (%)</label>
                        <input type="number" id="mortgage-rate" value="3.5" min="1" max="10" step="0.1">
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-calculator"></i> حساب
                    </button>
                </form>
                <div id="mortgage-result" style="display:none; margin-top:20px;"></div>
            </div>
        `;

        document.getElementById('mortgage-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.calculate();
        });
    }

    calculate() {
        const price = parseFloat(document.getElementById('mortgage-price').value);
        const downPaymentPercent = parseFloat(document.getElementById('mortgage-downpayment').value);
        const years = parseInt(document.getElementById('mortgage-years').value);
        const rate = parseFloat(document.getElementById('mortgage-rate').value);

        const downPayment = price * (downPaymentPercent / 100);
        const loanAmount = price - downPayment;
        const monthlyRate = rate / 100 / 12;
        const numPayments = years * 12;

        // صيغة القرض العادي
        const monthlyPayment = loanAmount *
            (monthlyRate * Math.pow(1 + monthlyRate, numPayments)) /
            (Math.pow(1 + monthlyRate, numPayments) - 1);

        const totalPayment = monthlyPayment * numPayments;
        const totalInterest = totalPayment - loanAmount;

        const resultDiv = document.getElementById('mortgage-result');
        resultDiv.style.display = 'block';
        resultDiv.innerHTML = `
            <div class="mortgage-results">
                <h4>📊 نتائج الحساب</h4>
                <div class="result-row">
                    <span>💰 سعر العقار:</span>
                    <strong>${price.toLocaleString('en-US')} SAR</strong>
                </div>
                <div class="result-row">
                    <span>💵 الدفعة الأولى:</span>
                    <strong>${downPayment.toLocaleString('en-US')} SAR (${downPaymentPercent}%)</strong>
                </div>
                <div class="result-row">
                    <span>🏦 مبلغ التمويل:</span>
                    <strong>${loanAmount.toLocaleString('en-US')} SAR</strong>
                </div>
                <div class="result-row highlight">
                    <span>📅 القسط الشهري:</span>
                    <strong>${Math.round(monthlyPayment).toLocaleString('en-US')} SAR</strong>
                </div>
                <div class="result-row">
                    <span>📊 إجمالي الفائدة:</span>
                    <strong>${Math.round(totalInterest).toLocaleString('en-US')} SAR</strong>
                </div>
                <div class="result-row">
                    <span>💵 إجمالي المدفوع:</span>
                    <strong>${Math.round(totalPayment + downPayment).toLocaleString('en-US')} SAR</strong>
                </div>
                <p class="mortgage-note">⚠️ هذه الحسابات تقريبية. يرجى التواصل مع البنك للحصول على عرض تمويل دقيق.</p>
            </div>
        `;
    }
}

const mortgageCalculator = new MortgageCalculator();
