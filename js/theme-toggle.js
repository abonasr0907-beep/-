// js/theme-toggle.js (جديد)

class ThemeManager {
    constructor() {
        this.currentTheme = localStorage.getItem('afaq_theme') || 'dark';
        this.init();
    }

    init() {
        this.applyTheme(this.currentTheme);
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.renderToggle());
        } else {
            this.renderToggle();
        }
    }

    applyTheme(theme) {
        document.documentElement.setAttribute('data-theme', theme);

        if (theme === 'light') {
            document.documentElement.style.setProperty('--bg-color', '#f5f5f5');
            document.documentElement.style.setProperty('--text-color', '#1a1a1a');
            document.documentElement.style.setProperty('--glass-bg', 'rgba(255, 255, 255, 0.8)');
            document.documentElement.style.setProperty('--glass-border', 'rgba(0, 0, 0, 0.1)');
        } else {
            document.documentElement.style.setProperty('--bg-color', '#0a0a0a');
            document.documentElement.style.setProperty('--text-color', '#ffffff');
            document.documentElement.style.setProperty('--glass-bg', 'rgba(255, 255, 255, 0.05)');
            document.documentElement.style.setProperty('--glass-border', 'rgba(255, 255, 255, 0.1)');
        }

        localStorage.setItem('afaq_theme', theme);
    }

    toggle() {
        this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
        this.applyTheme(this.currentTheme);
        const icon = document.querySelector('.theme-toggle i');
        if (icon) {
            icon.className = `fas fa-${this.currentTheme === 'dark' ? 'sun' : 'moon'}`;
        }
    }

    renderToggle() {
        const header = document.querySelector('.header .header-container') || document.querySelector('.header .container');
        if (!header || header.querySelector('.theme-toggle')) return;

        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'theme-toggle';
        toggleBtn.setAttribute('aria-label', 'تبديل المظهر');
        toggleBtn.innerHTML = `<i class="fas fa-${this.currentTheme === 'dark' ? 'sun' : 'moon'}"></i>`;
        toggleBtn.onclick = () => this.toggle();

        header.appendChild(toggleBtn);
    }
}

const themeManager = new ThemeManager();
