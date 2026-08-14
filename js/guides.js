/* js/guides.js - Phase M3 Guides Content Rendering */

(function() {
  'use strict';

  let allGuides = [];

  function initGuides() {
    fetchGuides();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initGuides);
  } else {
    initGuides();
  }

  function fetchGuides() {
    fetch('data/guides.json')
      .then(response => {
        if (!response.ok) {
          throw new Error('Failed to load guides data');
        }
        return response.json();
      })
      .then(data => {
        allGuides = data;
        renderGuidesUI();
      })
      .catch(err => {
        console.error('Guides loading error:', err);
      });
  }

  function renderGuidesUI() {
    const container = document.getElementById('guides-app-container');
    if (!container) return;

    // Build Category Nav
    const categories = ['الكل', 'الأدلة العقارية', 'شراء المزارع', 'الاستراحات', 'الاستثمار العقاري'];

    let html = `
      <div class="guides-container">
        <div class="guides-categories-nav">
          ${categories.map((cat, idx) => `
            <button class="guide-cat-btn ${idx === 0 ? 'active' : ''}" data-category="${cat}">
              <i class="fas ${getCategoryIcon(cat)}"></i> ${cat}
            </button>
          `).join('')}
        </div>
        <div class="guides-grid" id="guides-grid"></div>
      </div>

      <!-- Article Modal -->
      <div class="guide-modal" id="guide-modal">
        <div class="guide-modal-content" id="guide-modal-content">
          <button class="guide-modal-close" onclick="closeGuideModal()">&times;</button>
          <div id="guide-article-render"></div>
        </div>
      </div>
    `;

    container.innerHTML = html;

    // Attach Category Click Events
    const catBtns = container.querySelectorAll('.guide-cat-btn');
    catBtns.forEach(btn => {
      btn.addEventListener('click', function() {
        catBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const cat = this.getAttribute('data-category');
        filterAndRenderGuides(cat);
      });
    });

    // Render Initial (All)
    filterAndRenderGuides('الكل');
  }

  function getCategoryIcon(cat) {
    switch (cat) {
      case 'الأدلة العقارية': return 'fa-book';
      case 'شراء المزارع': return 'fa-seedling';
      case 'الاستراحات': return 'fa-home';
      case 'الاستثمار العقاري': return 'fa-chart-line';
      default: return 'fa-th';
    }
  }

  function filterAndRenderGuides(cat) {
    const grid = document.getElementById('guides-grid');
    if (!grid) return;

    const filtered = (cat === 'الكل') ? allGuides : allGuides.filter(g => g.category === cat);

    if (filtered.length === 0) {
      grid.innerHTML = '<p class="no-guides">لا توجد مقالات متاحة في هذا القسم حالياً.</p>';
      return;
    }

    grid.innerHTML = filtered.map(guide => `
      <div class="guide-card">
        <div class="guide-card-header">
          <span class="guide-card-category">${guide.category}</span>
          <h3 class="guide-card-title">${guide.title}</h3>
        </div>
        <div class="guide-card-body">
          <p class="guide-card-summary">${guide.summary}</p>
          <div class="guide-card-meta">
            <span><i class="fas fa-user-edit"></i> ${guide.author}</span>
            <span><i class="fas fa-clock"></i> ${guide.readTime}</span>
          </div>
          <button class="guide-read-btn" onclick="openGuideModal('${guide.id}')">
            <i class="fas fa-book-open"></i> قراءة المقال الكامل
          </button>
        </div>
      </div>
    `).join('');
  }

  window.openGuideModal = function(guideId) {
    const guide = allGuides.find(g => g.id === guideId);
    if (!guide) return;

    const modal = document.getElementById('guide-modal');
    const renderDiv = document.getElementById('guide-article-render');
    if (!modal || !renderDiv) return;

    const waMsg = encodeURIComponent(`السلام عليكم، قرأت مقال "${guide.title}" على موقعكم واستفسر عن الفرص العقارية المناسبة.`);

    renderDiv.innerHTML = `
      <span class="guide-article-category">${guide.category}</span>
      <h2 class="guide-article-title">${guide.title}</h2>
      <div class="guide-article-meta">
        <span><i class="fas fa-user"></i> ${guide.author}</span>
        <span><i class="fas fa-calendar-alt"></i> ${guide.date}</span>
        <span><i class="fas fa-clock"></i> ${guide.readTime}</span>
      </div>
      <div class="guide-article-body">${guide.content}</div>
      <div class="guide-article-actions">
        <a href="https://wa.me/966545888931?text=${waMsg}" target="_blank" class="guide-action-btn wa">
          <i class="fab fa-whatsapp"></i> استشارة خبير عقاري عبر واتساب
        </a>
      </div>
    `;

    // Inject Article Schema dynamically
    injectArticleSchema(guide);

    modal.style.display = 'block';
    document.body.style.overflow = 'hidden';
  };

  window.closeGuideModal = function() {
    const modal = document.getElementById('guide-modal');
    if (modal) {
      modal.style.display = 'none';
      document.body.style.overflow = '';
    }
  };

  // Close on backdrop click
  window.addEventListener('click', function(e) {
    const modal = document.getElementById('guide-modal');
    if (e.target === modal) {
      closeGuideModal();
    }
  });

  function injectArticleSchema(guide) {
    let schemaScript = document.getElementById('dynamic-article-schema');
    if (!schemaScript) {
      schemaScript = document.createElement('script');
      schemaScript.id = 'dynamic-article-schema';
      schemaScript.type = 'application/ld+json';
      document.head.appendChild(schemaScript);
    }

    const schemaData = {
      "@context": "https://schema.org",
      "@type": "Article",
      "headline": guide.title,
      "description": guide.summary,
      "author": {
        "@type": "Organization",
        "name": guide.author
      },
      "publisher": {
        "@type": "Organization",
        "name": "مكتب آفاق الإنجاز العقاري",
        "logo": {
          "@type": "ImageObject",
          "url": "https://abonasr0907-beep.github.io/-/images/logo.jpg"
        }
      },
      "datePublished": guide.date,
      "mainEntityOfPage": {
        "@type": "WebPage",
        "@id": window.location.href
      }
    };

    schemaScript.textContent = JSON.stringify(schemaData);
  }
})();
