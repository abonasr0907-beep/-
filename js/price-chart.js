// js/price-chart.js (جديد)

// يتطلب إضافة Chart.js في index.html:
// <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

class PriceChart {
    constructor() {
        this.charts = {};
    }

    renderPriceTrend(containerId, data) {
        const elem = document.getElementById(containerId);
        if (!elem) return;

        if (typeof Chart === 'undefined') {
            console.warn('Chart.js library is not loaded');
            return;
        }

        const ctx = elem.getContext('2d');

        if (this.charts[containerId]) {
            this.charts[containerId].destroy();
        }

        this.charts[containerId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: 'متوسط السعر لكل م²',
                    data: data.prices,
                    borderColor: '#d4af37',
                    backgroundColor: 'rgba(212, 175, 55, 0.1)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: '#d4af37',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 5,
                    pointHoverRadius: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        labels: {
                            color: '#fff',
                            font: { size: 14 }
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#d4af37',
                        bodyColor: '#fff',
                        borderColor: '#d4af37',
                        borderWidth: 1,
                        callbacks: {
                            label: function(context) {
                                return context.parsed.y.toLocaleString('en-US') + ' SAR/m²';
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: { color: '#fff' }
                    },
                    y: {
                        grid: { color: 'rgba(255, 255, 255, 0.1)' },
                        ticks: {
                            color: '#fff',
                            callback: function(value) {
                                return value.toLocaleString('en-US');
                            }
                        }
                    }
                }
            }
        });
    }
}

const priceChart = new PriceChart();
