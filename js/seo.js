/**
 * SEO & Structured Data (JSON-LD) Injector + Office Location Section Generator
 * Afaq Al-Injaz Real Estate
 */

(function () {
  'use strict';

  // 1. Dynamic Structured Data Injection
  function injectStructuredData() {
    const isEnglish = window.location.search.includes('lang=en') || document.documentElement.lang === 'en';

    // Organization Schema
    const orgSchema = {
      "@context": "https://schema.org",
      "@type": "RealEstateAgent",
      "name": isEnglish ? "Afaq Al-Injaz Real Estate" : "أفاق الإنجاز للخدمات العقارية",
      "image": "https://abonasr0907-beep.github.io/images/logo.png",
      "@id": "https://abonasr0907-beep.github.io/#organization",
      "url": "https://abonasr0907-beep.github.io/",
      "telephone": "+966500000000",
      "priceRange": "$$",
      "address": {
        "@type": "PostalAddress",
        "streetAddress": "حي الرحمانية / الخرج",
        "addressLocality": "الخرج",
        "addressRegion": "الرياض",
        "addressCountry": "SA"
      },
      "geo": {
        "@type": "GeoCoordinates",
        "latitude": 24.1500,
        "longitude": 47.3000
      },
      "license": "1100004208"
    };

    // WebSite Schema with SearchAction
    const websiteSchema = {
      "@context": "https://schema.org",
      "@type": "WebSite",
      "name": isEnglish ? "Afaq Al-Injaz Real Estate" : "أفاق الإنجاز العقارية",
      "url": "https://abonasr0907-beep.github.io/",
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://abonasr0907-beep.github.io/?q={search_term_string}",
        "query-input": "required name=search_term_string"
      }
    };

    // BreadcrumbList Schema
    const pathSegments = window.location.pathname.split('/').filter(Boolean);
    const breadcrumbItems = [
      {
        "@type": "ListItem",
        "position": 1,
        "name": isEnglish ? "Home" : "الرئيسية",
        "item": "https://abonasr0907-beep.github.io/"
      }
    ];

    if (pathSegments.length > 0) {
      const pageName = pathSegments[pathSegments.length - 1];
      breadcrumbItems.push({
        "@type": "ListItem",
        "position": 2,
        "name": pageName,
        "item": window.location.href
      });
    }

    const breadcrumbSchema = {
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": breadcrumbItems
    };

    // FAQPage Schema
    const faqSchema = {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        {
          "@type": "Question",
          "name": isEnglish ? "How can I list my property with Afaq Al-Injaz?" : "كيف يمكنني عرض عقاري عبر مكتب أفاق الإنجاز؟",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": isEnglish ? "You can easily submit your property details using our online 'List Your Property' form or directly contact our licensed real estate agents." : "يمكنك تقديم تفاصيل عقارك عبر صفحة 'اعرض عقارك' على الموقع أو من خلال التواصل المباشر معنا عبر الواتساب أو البوت."
          }
        },
        {
          "@type": "Question",
          "name": isEnglish ? "What real estate services does Afaq Al-Injaz offer in Al-Kharj?" : "ما هي الخدمات العقارية التي يقدمها مكتب أفاق الإنجاز بالخرج؟",
          "acceptedAnswer": {
            "@type": "Answer",
            "text": isEnglish ? "We provide real estate marketing, property valuation support, sales of land plots, farms, resthouses, and apartments in Al-Kharj under FAL license 1100004208." : "نقدم التسويق العقاري، البيع والتمليك للأراضي، المزارع، الاستراحات، والشقق بمدينة الخرج تحت ترخيص فال رقم 1100004208."
          }
        }
      ]
    };

    [orgSchema, websiteSchema, breadcrumbSchema, faqSchema].forEach(schema => {
      const script = document.createElement('script');
      script.type = 'application/ld+json';
      script.text = JSON.stringify(schema);
      document.head.appendChild(script);
    });
  }

  // 2. Feature 6: Office Location section ("🏢 موقع المكتب") injection
  function injectOfficeLocationSection() {
    // Inject at the end of body or main content container
    if (document.getElementById('office-location-section')) return;

    const officeSection = document.createElement('section');
    officeSection.id = 'office-location-section';
    officeSection.className = 'office-location-container';
    officeSection.style.cssText = 'margin: 40px auto; padding: 25px; background: rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.15); max-width: 1100px; color: #fff; text-align: center; box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);';

    const mapsUrl = 'https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent('مكتب آفاق الإنجاز العقاري الخرج');
    const phoneNum = (window.CONTACTS && window.CONTACTS.call1) ? window.CONTACTS.call1 : '+966500000000';

    officeSection.innerHTML = `
      <h3 style="font-size: 1.4rem; color: #c7d9b5; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px;">
        🏢 موقع المكتب الرئيسي
      </h3>
      <p style="color: #cbd5e1; margin-bottom: 20px; font-size: 0.95rem;">
        أفاق الإنجاز للخدمات العقارية - الخرج | ترخيص فال: 1100004208
      </p>
      <div style="display: flex; gap: 15px; justify-content: center; flex-wrap: wrap;">
        <a href="${mapsUrl}" target="_blank" rel="noopener noreferrer" class="btn-office-directions" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 22px; background: #c7d9b5; color: #14202b; font-weight: bold; border-radius: 12px; text-decoration: none; transition: transform 0.2s;">
          📍 اتجاهات خرائط جوجل
        </a>
        <a href="tel:${phoneNum}" class="btn-office-call" style="display: inline-flex; align-items: center; gap: 8px; padding: 12px 22px; background: rgba(255, 255, 255, 0.15); color: #fff; font-weight: bold; border-radius: 12px; text-decoration: none; border: 1px solid rgba(255, 255, 255, 0.2);">
          📞 اتصل بالمكتب
        </a>
      </div>
    `;

    const mainContainer = document.querySelector('main') || document.body;
    mainContainer.appendChild(officeSection);
  }

  document.addEventListener('DOMContentLoaded', function () {
    injectStructuredData();
    injectOfficeLocationSection();
  });
})();
