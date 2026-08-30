// js/seo-landing-pages.js (جديد)

const AREAS = ['الرحمانية', 'الهياثم', 'الدلم', 'الضبيعة', 'العفجة'];

function generateAreaLandingPage(area, allProperties = []) {
    const properties = allProperties.filter(p =>
        (p.area || p.location || '').toLowerCase().includes(area.toLowerCase())
    );

    const prices = properties.map(p => p.price || 0).filter(p => p > 0);
    const lowPrice = prices.length > 0 ? Math.min(...prices) : 0;
    const highPrice = prices.length > 0 ? Math.max(...prices) : 0;

    return `
        <!DOCTYPE html>
        <html lang="ar" dir="rtl">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>عقارات ${area} للبيع | آفاق الإنجاز</title>
            <meta name="description" content="اكتشف أفضل العقارات في ${area}. مزارع، استراحات، أراضي سكنية بأسعار مميزة. تواصل معنا الآن!">
            <link rel="canonical" href="https://abonasr0907-beep.github.io/areas/${area}.html">

            <!-- Open Graph -->
            <meta property="og:title" content="عقارات ${area} للبيع | آفاق الإنجاز">
            <meta property="og:description" content="أفضل العقارات في ${area} بأسعار تنافسية">
            <meta property="og:image" content="https://abonasr0907-beep.github.io/images/areas/${area}.jpg">
            <meta property="og:url" content="https://abonasr0907-beep.github.io/areas/${area}.html">

            <!-- Schema.org -->
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "RealEstateListing",
                "name": "عقارات ${area}",
                "description": "عقارات للبيع في ${area}",
                "url": "https://abonasr0907-beep.github.io/areas/${area}.html",
                "areaServed": {
                    "@type": "City",
                    "name": "${area}"
                },
                "offers": {
                    "@type": "AggregateOffer",
                    "lowPrice": "${lowPrice}",
                    "highPrice": "${highPrice}",
                    "priceCurrency": "SAR",
                    "offerCount": "${properties.length}"
                }
            }
            </script>
        </head>
        <body>
            <!-- المحتوى -->
        </body>
        </html>
    `;
}

// توليد الصفحات
function generateAllLandingPages(allProperties = []) {
    AREAS.forEach(area => {
        const html = generateAreaLandingPage(area, allProperties);
        // حفظ الملف: areas/${area}.html
        console.log(`Generated landing page for ${area}`);
    });
}
