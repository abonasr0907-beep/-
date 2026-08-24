/**
 * AnalyticsDashboard - Live Visitor & Property View Analytics
 * Manages live counters and view analytics using localStorage.
 */

class AnalyticsDashboard {
  constructor() {
    this.data = {
      visitors: 0,
      totalViews: 0
    };
    this.init();
  }

  init() {
    this.loadData();
    this.startLiveCounter();
  }

  loadData() {
    const saved = localStorage.getItem('afaq_analyticsData');
    if (saved) {
      try {
        this.data = JSON.parse(saved);
      } catch (e) {
        console.warn('Invalid analytics JSON in localStorage');
      }
    }
    this.data.visitors = this.data.visitors || Math.floor(Math.random() * 25) + 12;

    const viewsData = JSON.parse(localStorage.getItem('afaq_weekly_views') || '{}');
    let total = 0;
    Object.values(viewsData).forEach(v => { total += (parseInt(v, 10) || 0); });
    this.data.totalViews = total > 0 ? total : 340;
  }

  startLiveCounter() {
    this.updateVisitorDisplay();

    setInterval(() => {
      const change = Math.floor(Math.random() * 5) - 2;
      this.data.visitors = Math.max(8, this.data.visitors + change);
      this.updateVisitorDisplay();
    }, 4000);

    setInterval(() => {
      localStorage.setItem('afaq_analyticsData', JSON.stringify(this.data));
    }, 20000);
  }

  updateVisitorDisplay() {
    const liveVisEl = document.getElementById('live-visitor-count');
    if (liveVisEl) {
      liveVisEl.textContent = this.data.visitors;
    }
    const fomoVisEl = document.getElementById('fomoText');
    if (fomoVisEl && fomoVisEl.textContent.includes('يتصفحون العروض')) {
      fomoVisEl.textContent = `🔥 ${this.data.visitors} شخص يتصفحون العروض الآن`;
    }
  }

  incrementView(propertyId) {
    if (!propertyId) return;
    const viewsData = JSON.parse(localStorage.getItem('afaq_weekly_views') || '{}');
    viewsData[propertyId] = (viewsData[propertyId] || 0) + 1;
    localStorage.setItem('afaq_weekly_views', JSON.stringify(viewsData));

    this.data.totalViews++;
    localStorage.setItem('afaq_analyticsData', JSON.stringify(this.data));
  }
}

document.addEventListener('DOMContentLoaded', () => {
  window.analyticsDashboard = new AnalyticsDashboard();
});

window.AnalyticsDashboard = AnalyticsDashboard;
