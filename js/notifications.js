/**
 * NotificationSystem - UI Toast Notifications System
 * Handles elegant non-blocking alerts across the site.
 */

class NotificationSystem {
  constructor() {
    this.container = null;
    this.init();
  }

  init() {
    this.createContainer();
  }

  createContainer() {
    if (document.getElementById('notification-container')) {
      this.container = document.getElementById('notification-container');
      return;
    }
    this.container = document.createElement('div');
    this.container.id = 'notification-container';
    this.container.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 10000;
      display: flex;
      flex-direction: column;
      gap: 10px;
      pointer-events: none;
      direction: rtl;
    `;
    document.body.appendChild(this.container);
  }

  show(message, type = 'info', duration = 5000) {
    if (!this.container) this.createContainer();

    const toast = document.createElement('div');
    toast.className = `notification-toast ${type}`;
    toast.style.cssText = `
      background: rgba(26, 26, 46, 0.95);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(255, 255, 255, 0.18);
      border-radius: 12px;
      padding: 14px 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
      color: #fff;
      min-width: 280px;
      max-width: 360px;
      pointer-events: auto;
      transform: translateX(400px);
      transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    `;

    if (type === 'success') toast.style.borderLeft = '4px solid #2ECC71';
    else if (type === 'error') toast.style.borderLeft = '4px solid #e74c3c';
    else if (type === 'warning') toast.style.borderLeft = '4px solid #f39c12';
    else toast.style.borderLeft = '4px solid #3498db';

    toast.innerHTML = `
      <div style="display:flex;align-items:center;gap:12px;">
        <span style="font-size:22px;">${this.getIcon(type)}</span>
        <div>
          <div style="font-weight:700;color:#D4AF37;margin-bottom:2px;font-size:0.95rem;">${this.getTitle(type)}</div>
          <div style="color:rgba(255,255,255,0.85);font-size:0.85rem;line-height:1.4;">${message}</div>
        </div>
      </div>
    `;

    this.container.appendChild(toast);

    requestAnimationFrame(() => {
      toast.style.transform = 'translateX(0)';
    });

    setTimeout(() => {
      toast.style.transform = 'translateX(400px)';
      setTimeout(() => toast.remove(), 400);
    }, duration);
  }

  getIcon(type) {
    const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️', newOffer: '🏠' };
    return icons[type] || icons.info;
  }

  getTitle(type) {
    const titles = { success: 'تم بنجاح', error: 'تنبيه', info: 'إشعار', warning: 'تنبيه مهم', newOffer: 'عرض جديد' };
    return titles[type] || titles.info;
  }
}

function showNotification(message, type = 'info', duration) {
  if (!window.notificationSystem) window.notificationSystem = new NotificationSystem();
  window.notificationSystem.show(message, type, duration);
}

window.NotificationSystem = NotificationSystem;
window.showNotification = showNotification;
