#!/usr/bin/env python3
"""
Phase 3 §3: Generate 6 hub pages for the hierarchical silo.
- categories.html, areas.html, guides.html, why-us.html, faq.html, compare.html
Each page has: SEO meta, OG/Twitter, canonical, BreadcrumbList Schema,
luxury CSS + silo CSS, updated nav hierarchy, stats bar, trust bar,
exclusives bar (featured=true), intra-silo links, footer.
"""
import json
import os

REPO = os.path.dirname(os.path.abspath(__file__))
# Read header and footer blocks
header_block = open('/tmp/header_block.html', encoding='utf-8').read()
footer_block = open('/tmp/footer_block.html', encoding='utf-8').read()

# ===== New nav hierarchy =====
# Original nav: الرئيسية, المزارع, الاستراحات, الأراضي السكنية, الخدمات, اعرض عقارك, تواصل معنا
# New nav adds: الأقسام (categories), المناطق (areas), لماذا نحن (why-us), الأسئلة (faq)
# We ADD links, don't remove existing ones (add-only protection)
NAV_ITEMS = [
    ("index.html", "home", "fa-home", "الرئيسية"),
    ("categories.html", "categories", "fa-th-large", "الأقسام"),
    ("farms.html", "farms", "fa-seedling", "المزارع"),
    ("resthouses.html", "resthouses", "fa-home", "الاستراحات"),
    ("lands.html", "lands", "fa-map", "الأراضي السكنية"),
    ("areas.html", "areas", "fa-map-marked-alt", "المناطق"),
    ("services.html", "services", "fa-tools", "الخدمات"),
    ("guides.html", "guides", "fa-book-open", "أدلة عقارية"),
    ("why-us.html", "why-us", "fa-award", "لماذا نحن"),
    ("faq.html", "faq", "fa-question-circle", "الأسئلة الشائعة"),
    ("compare.html", "compare", "fa-balance-scale", "مقارنة العقارات"),
    ("list-property.html", "list-property", "fa-plus-circle", "اعرض عقارك"),
    ("contact.html", "contact", "fa-phone", "تواصل معنا"),
]

def make_nav(active_page):
    """Generate nav with the correct active class."""
    items = []
    for href, key, icon, label in NAV_ITEMS:
        cls = ' class="active"' if active_page == key else ''
        items.append(f'                    <li><a href="{href}"{cls}><i class="fas {icon}"></i> {label}</a></li>')
    return '<ul class="nav-menu" id="nav-menu">\n' + '\n'.join(items) + '\n                </ul>'

def make_header(active_page):
    """Build header with updated nav."""
    nav = make_nav(active_page)
    # Replace the old nav in header_block with new nav
    import re
    # The old nav is between <ul class="nav-menu" id="nav-menu"> and </ul>
    new_header = re.sub(
        r'<ul class="nav-menu" id="nav-menu">.*?</ul>',
        nav,
        header_block,
        count=1,
        flags=re.DOTALL
    )
    return new_header

def make_head(title, desc, keywords, canonical_path, og_title=None, og_desc=None):
    """Build HTML head section with SEO meta."""
    base = "https://abonasr0907-beep.github.io/-/"
    og_title = og_title or title
    og_desc = og_desc or desc
    return f'''<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <meta name="keywords" content="{keywords}">
    <meta name="author" content="مكتب آفاق الإنجاز العقاري">
    <meta name="robots" content="index, follow">
    <meta name="language" content="Arabic">
    <meta name="geo.region" content="SA-12">
    <meta name="geo.placename" content="الخرج، الرياض">
    <meta name="geo.position" content="24.1554;47.3068">
    <meta name="ICBM" content="24.1554, 47.3068">

    <!-- Open Graph -->
    <meta property="og:title" content="{og_title}">
    <meta property="og:description" content="{og_desc}">
    <meta property="og:type" content="website">
    <meta property="og:locale" content="ar_SA">
    <meta property="og:image" content="images/logo.jpg">
    <meta property="og:site_name" content="مكتب آفاق الإنجاز العقاري">

    <!-- Twitter Card -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{og_title}">
    <meta name="twitter:description" content="{og_desc}">
    <meta name="twitter:image" content="images/logo.jpg">

    <!-- Canonical -->
    <link rel="canonical" href="{base}{canonical_path}">
    <link rel="manifest" href="site.webmanifest">

    <!-- Favicon -->
    <link rel="icon" type="image/jpeg" href="images/logo.jpg">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Reem+Kufi:wght@400;500;600;700&family=Amiri:wght@400;700&display=swap" rel="stylesheet">

    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">

    <!-- Styles -->
    <link rel="stylesheet" href="css/style.css">
    <link rel="stylesheet" href="css/luxury.css">
    <link rel="stylesheet" href="css/silo.css">
</head>
<body>'''

def make_breadcrumb(crumb_list, canonical_path):
    """Make visible breadcrumb + BreadcrumbList schema data."""
    base = "https://abonasr0907-beep.github.io/-/"
    html = '<div class="silo-breadcrumb">'
    schema_data = []
    for i, (name, url) in enumerate(crumb_list):
        schema_data.append({"name": name, "url": base + url if url else base + canonical_path})
        if i < len(crumb_list) - 1:
            html += f'<a href="{url}"><i class="fas fa-home"></i> {name}</a>' if i == 0 else f'<a href="{url}">{name}</a>'
            html += '<span class="sep"><i class="fas fa-chevron-left"></i></span>'
        else:
            html += f'<span class="current">{name}</span>'
    html += '</div>'
    html += f'\n    <script type="application/json" id="breadcrumb-schema-data">{json.dumps(schema_data, ensure_ascii=False)}</script>'
    return html

def make_stats_bar():
    return '<div class="silo-stats-bar" id="silo-stats-bar" data-stat="all"></div>'

def make_trust_bar():
    return '''<div class="silo-trust-bar">
        <div class="silo-trust-item"><i class="fas fa-medal"></i> خبرة 20 سنة في السوق العقاري</div>
        <div class="silo-trust-item"><i class="fas fa-handshake"></i> وسيط موثوق ومعتمد</div>
        <div class="silo-trust-item"><i class="fas fa-shield-alt"></i> صكوك إلكترونية موثقة</div>
        <div class="silo-trust-item"><i class="fas fa-users"></i> أكثر من 1000 عميل سعيد</div>
    </div>'''

def make_exclusives_bar():
    return '''<div class="silo-exclusives-bar" id="silo-exclusives-bar">
        <h2 class="silo-exclusives-title"><i class="fas fa-star"></i> عقارات حصرية — مميزة من آفاق الإنجاز</h2>
        <div class="silo-exclusives-scroll" id="silo-exclusives-scroll"></div>
    </div>'''

def make_silo_links(title, links):
    """Intra-silo links section."""
    html = f'<div class="silo-links-section"><h2>{title}</h2><ul class="silo-links-list">'
    for name, url, icon in links:
        html += f'<li><a href="{url}"><i class="fas {icon}"></i> {name}</a></li>'
    html += '</ul></div>'
    return html

def make_footer_scripts():
    return '''    <!-- Scripts -->
    <script src="js/main.js"></script>
    <script src="js/silo.js"></script>
</body>
</html>'''

# ===== Common intra-silo links (all hub pages link to each other) =====
SILO_LINKS = [
    ("الأقسام العقارية", "categories.html", "fa-th-large"),
    ("المناطق المغطاة", "areas.html", "fa-map-marked-alt"),
    ("الأدلة العقارية", "guides.html", "fa-book-open"),
    ("لماذا نحن", "why-us.html", "fa-award"),
    ("الأسئلة الشائعة", "faq.html", "fa-question-circle"),
    ("مقارنة العقارات", "compare.html", "fa-balance-scale"),
    ("المزارع", "farms.html", "fa-seedling"),
    ("الاستراحات", "resthouses.html", "fa-home"),
    ("الأراضي السكنية", "lands.html", "fa-map"),
    ("الخدمات", "services.html", "fa-tools"),
    ("اعرض عقارك", "list-property.html", "fa-plus-circle"),
    ("تواصل معنا", "contact.html", "fa-phone"),
]

# ===== Generate categories.html =====
def gen_categories():
    title = "تصنيفات العقارات | مزارع واستراحات وأراضي سكنية | مكتب آفاق الإنجاز العقاري"
    desc = "تصفح جميع تصنيفات العقارات في مكتب آفاق الإنجاز العقاري: مزارع للبيع، استراحات للإيجار، أراضي سكنية، ومشاريع زراعية في الخرج والرياض. خبرة 20 سنة في السوق العقاري."
    keywords = "تصنيفات عقارات, مزارع للبيع, استراحات للإيجار, أراضي سكنية, عقارات الخرج, عقارات الرياض, آفاق الإنجاز العقاري"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("الأقسام", "categories.html"),
    ], "categories.html")
    
    cards = [
        ("fa-seedling", "المزارع", "مزارع للبيع في الخرج والرياض بمخططات الرحمانية والهياثم والدلم. مشاريع زراعية بآبار مياه وأشجار نخيل.", "farms.html", "category", "مزرعة"),
        ("fa-home", "الاستراحات", "استراحات للبيع وللإيجار في الخرج والرياض. استراحات فاخرة بمسبح وحدائق وجلسات خارجية.", "resthouses.html", "category", "استراحة"),
        ("fa-map", "الأراضي السكنية", "أراضي سكنية للبيع في الخرج والرياض بمخططات معتمدة وصكوك إلكترونية. أراضي جاهزة للبناء.", "lands.html", "category", "أرض سكنية"),
    ]
    
    cards_html = '<div class="silo-hub-grid">'
    for icon, h3, p, url, count_type, count_val in cards:
        cards_html += f'''<a href="{url}" class="silo-hub-card" data-hub-count="{count_type}" data-hub-value="{count_val}">
            <div class="silo-hub-card-icon"><i class="fas {icon}"></i></div>
            <div class="silo-hub-card-body">
                <h3>{h3}</h3>
                <p>{p}</p>
                <div class="silo-hub-card-count">— عقار متاح</div>
                <span class="silo-hub-card-link">تصفح الآن</span>
            </div>
        </a>'''
    cards_html += '</div>'
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>تصنيفات العقارات</h1>
        <p>استكشف مجموعتنا الكاملة من العقارات في الخرج والرياض — مزارع واستراحات وأراضي سكنية بمختلف المساحات والأسعار. خبرة 20 سنة في خدمة عملائنا.</p>
    </div>
    {breadcrumb}
    {make_stats_bar()}
    {make_trust_bar()}
    {make_exclusives_bar()}
    {cards_html}
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>'''
    
    html = make_head(title, desc, keywords, "categories.html") + "\n" + make_header("categories") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'categories.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ categories.html created")

# ===== Generate areas.html =====
def gen_areas():
    title = "مناطق العمل | الخرج والرياض | مكتب آفاق الإنجاز العقاري"
    desc = "مناطق تغطيتها مكتب آفاق الإنجاز العقاري: الرحمانية، الهياثم، الدلم، الضبيعة، العفجة في الخرج والرياض. عقارات في جميع المخططات المعتمدة."
    keywords = "مناطق عقارية, الرحمانية, الهياثم, الدلم, الضبيعة, العفجة, الخرج, الرياض, مخططات معتمدة, آفاق الإنجاز"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("المناطق", "areas.html"),
    ], "areas.html")
    
    areas = [
        ("الرحمانية", "مخطط الرحمانية في الخرج — مزارع وأراضي زراعية بآبار مياه", "fa-seedling"),
        ("الهياثم", "مخطط الهياثم في الخرج — استراحات وأراضي سكنية", "fa-home"),
        ("الدلم", "محافظة الدلم — مزارع واستراحات وأراضي متنوعة", "fa-map"),
        ("الضبيعة", "مخطط الضبيعة — أراضي سكنية ومزارع", "fa-tree"),
        ("العفجة", "مخطط العفجة — استراحات ومزارع للبيع", "fa-water"),
    ]
    
    cards_html = '<div class="silo-hub-grid">'
    for name, desc_short, icon in areas:
        cards_html += f'''<a href="farms.html" class="silo-hub-card" data-hub-count="area" data-hub-value="{name}">
            <div class="silo-hub-card-icon"><i class="fas {icon}"></i></div>
            <div class="silo-hub-card-body">
                <h3>{name}</h3>
                <p>{desc_short}</p>
                <div class="silo-hub-card-count">— عقار متاح</div>
                <span class="silo-hub-card-link">تصفح العقارات</span>
            </div>
        </a>'''
    cards_html += '</div>'
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>مناطق العمل</h1>
        <p>نغطي جميع المخططات المعتمدة في الخرج والرياض. تصفح العقارات المتاحة في كل منطقة واعثر على عقارك المثالي.</p>
    </div>
    {breadcrumb}
    {make_stats_bar()}
    {make_trust_bar()}
    {make_exclusives_bar()}
    {cards_html}
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>'''
    
    html = make_head(title, desc, keywords, "areas.html") + "\n" + make_header("areas") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'areas.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ areas.html created")

# ===== Generate guides.html =====
def gen_guides():
    title = "أدلة عقارية شاملة | دليل شراء المزارع والاستراحات | مكتب آفاق الإنجاز"
    desc = "أدلة عقارية شاملة من مكتب آفاق الإنجاز: دليل شراء المزارع، دليل الاستراحات، دليل الأراضي السكنية، دليل الاستثمار العقاري في الخرج والرياض."
    keywords = "أدلة عقارية, دليل شراء مزرعة, دليل شراء استراحة, دليل الأراضي, الاستثمار العقاري, الخرج, الرياض, آفاق الإنجاز"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("الأدلة العقارية", "guides.html"),
    ], "guides.html")
    
    guides = [
        ("دليل شراء المزارع", "دليل شامل لشراء المزارع في الخرج والرياض — كيف تختار المزرعة المناسبة، ما هي الآبار والصكوك المطلوبة، وكيف تقيّم السعر العادل.", "fa-seedling", "guides/farms-guide.html"),
        ("دليل الاستراحات", "كل ما تحتاج معرفته عن شراء الاستراحات في الخرج والرياض — الموقع، المساحة، المرافق، وكيف تحقق أفضل صفقة.", "fa-home", "guides/resthouses-guide.html"),
        ("دليل الأراضي السكنية", "دليل شراء الأراضي السكنية — المخططات المعتمدة، الصكوك الإلكترونية، رخص البناء، والتقسيم.", "fa-map", "guides/lands-guide.html"),
        ("دليل الاستثمار العقاري", "كيف تستثمر في العقارات بالخرج والرياض — العائد المتوقع، المناطق الواعدة، واستراتيجيات الاستثمار.", "fa-chart-line", "guides/investment-guide.html"),
    ]
    
    cards_html = '<div class="silo-hub-grid">'
    for h3, p, icon, url in guides:
        cards_html += f'''<a href="{url}" class="silo-hub-card">
            <div class="silo-hub-card-icon"><i class="fas {icon}"></i></div>
            <div class="silo-hub-card-body">
                <h3>{h3}</h3>
                <p>{p}</p>
                <span class="silo-hub-card-link">اقرأ الدليل</span>
            </div>
        </a>'''
    cards_html += '</div>'
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>الأدلة العقارية</h1>
        <p>أدلة شاملة تساعدك على اتخاذ القرار العقاري الصحيح. تعلم كيف تشتري وتستثمر في العقارات بالخرج والرياض بخبرة 20 سنة.</p>
    </div>
    {breadcrumb}
    {make_trust_bar()}
    {cards_html}
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>'''
    
    html = make_head(title, desc, keywords, "guides.html") + "\n" + make_header("guides") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'guides.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ guides.html created")

# ===== Generate why-us.html =====
def gen_why_us():
    title = "لماذا نحن | مزايا مكتب آفاق الإنجاز العقاري | خبرة 20 سنة"
    desc = "لماذا تختار مكتب آفاق الإنجاز العقاري؟ خبرة 20 سنة، صكوك إلكترونية موثقة، فريق متخصص، خدمة ما بعد البيع، مقاولات وحفر آبار وإدارة أملاك في الخرج والرياض."
    keywords = "لماذا آفاق الإنجاز, مزايا مكتب عقاري, أفضل مكتب عقاري في الخرج, أفضل مكتب عقاري في الرياض, صكوك إلكترونية, خبرة عقارية"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("لماذا نحن", "why-us.html"),
    ], "why-us.html")
    
    features = [
        ("fa-medal", "خبرة 20 سنة", "خبرة طويلة في السوق العقاري بالخرج والرياض نضعها في خدمتك لاتخاذ أفضل قرار."),
        ("fa-shield-alt", "صكوك إلكترونية موثقة", "جميع عقاراتنا بصكوك إلكترونية موثقة من وزارة العدل — أمان كامل في كل صفقة."),
        ("fa-users", "فريق متخصص", "فريق من الخبراء في المزارع والاستراحات والأراضي السكنية لمساعدتك في كل خطوة."),
        ("fa-tools", "خدمة ما بعد البيع", "نقدم خدمات مقاولات وحفر آبار وإدارة أملاك وتشطيبات — خدمة متكاملة."),
        ("fa-handshake", "وسيط موثوق", "سمعة طيبة وثقة عملائنا — أكثر من 1000 عميل سعيد بخدماتنا."),
        ("fa-map-marked-alt", "تغطية شاملة", "نغطي جميع المخططات المعتمدة في الخرج والرياض — الرحمانية، الهياثم، الدلم، وأكثر."),
        ("fa-file-alt", "خدمات قانونية", "نساعدك في إجراءات التحويل والتوثيق والترهين — راحة بال كاملة."),
        ("fa-broadcast-tower", "تسويق عقاري", "نسوّق عقارك عبر منصات متعددة وروبوت واتساب للوصول لأكبر شريحة من المشترين."),
    ]
    
    cards_html = '<div class="silo-hub-grid">'
    for icon, h3, p in features:
        cards_html += f'''<div class="silo-hub-card">
            <div class="silo-hub-card-icon"><i class="fas {icon}"></i></div>
            <div class="silo-hub-card-body">
                <h3>{h3}</h3>
                <p>{p}</p>
            </div>
        </div>'''
    cards_html += '</div>'
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>لماذا تختار آفاق الإنجاز؟</h1>
        <p>نقدم لك أكثر من مجرد وساطة عقارية — نقدم خبرة وأمان وخدمة متكاملة من أول استشارة حتى ما بعد البيع.</p>
    </div>
    {breadcrumb}
    {make_stats_bar()}
    {make_trust_bar()}
    {cards_html}
    <div style="text-align:center; margin: 40px 0;">
        <a href="https://wa.me/966545888931" target="_blank" class="luxury-cta-whatsapp" style="display:inline-flex; align-items:center; gap:10px; padding:14px 32px; background: #25D366; color: #fff; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 1.1rem;">
            <i class="fab fa-whatsapp"></i> تواصل معنا الآن
        </a>
    </div>
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>'''
    
    html = make_head(title, desc, keywords, "why-us.html") + "\n" + make_header("why-us") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'why-us.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ why-us.html created")

# ===== Generate faq.html =====
def gen_faq():
    title = "الأسئلة الشائعة | عقارات الخرج والرياض | مكتب آفاق الإنجاز"
    desc = "أسئلة شائعة عن شراء العقارات في الخرج والرياض: كيف أشتري مزرعة؟ ما هي الصكوك الإلكترونية؟ كيف أحفر بئراً؟ أسعار المزارع والاستراحات."
    keywords = "أسئلة عقارية, أسئلة شائعة, شراء مزرعة, صكوك إلكترونية, حفر آبار, أسعار العقارات, الخرج, الرياض, آفاق الإنجاز"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("الأسئلة الشائعة", "faq.html"),
    ], "faq.html")
    
    faqs = [
        ("كيف أشتري مزرعة في الخرج؟", "يمكنك تصفح مزارعنا المتاحة في صفحة المزارع، ثم التواصل معنا عبر واتساب أو الهاتف لمعاينة المزرعة. نساعدك في جميع إجراءات التحويل والتوثيق."),
        ("ما هي الصكوك الإلكترونية؟", "الصكوك الإلكترونية هي وثائق ملكية رقمية صادرة من وزارة العدل عبر منصة ناجز. جميع عقاراتنا موثقة بصكوك إلكترونية لضمان أمان الصفقة."),
        ("هل تقدمون خدمات حفر الآبار؟", "نعم، نقدم خدمات حفر آبار ارتوازية وزراعية كجزء من خدماتنا المتكاملة. تواصل معنا لمعرفة التفاصيل والأسعار."),
        ("ما هي مناطق تغطيتكم؟", "نغطي جميع المخططات المعتمدة في الخرج والرياض: الرحمانية، الهياثم، الدلم، الضبيعة، العفجة، وغيرها."),
        ("هل تقدمون خدمات إدارة الأملاك؟", "نعم، نقدم خدمات إدارة الأملاك العقارية للملاك الذين يرغبون في تأجير أو إدارة عقاراتهم بكفاءة."),
        ("كيف أعرض عقاري لديكم؟", "يمكنك عرض عقارك عبر صفحة 'اعرض عقارك' وملء النموذج، أو التواصل معنا مباشرة عبر واتساب. سنتواصل معك لاستكمال الإجراءات."),
        ("هل العقارات جاهزة للمعاينة؟", "نعم، جميع العقارات المعروضة متاحة للمعاينة. تواصل معنا لتحديد موعد معاينة مناسب لك."),
        ("ما هي خدمات المقاولات التي تقدمونها؟", "نقدم خدمات مقاولات عامة وتشطيبات وإقامة استراحات ومباني. تواصل معنا لمعرفة المزيد عن خدماتنا."),
    ]
    
    faq_html = '<div class="silo-hub-grid" style="grid-template-columns: 1fr;">'
    faq_schema = []
    for q, a in faqs:
        faq_schema.append({"question": q, "answer": a})
        faq_html += f'''<details style="background:#fff; border:1px solid #e5e0d5; border-radius:12px; padding:16px 20px; margin-bottom:12px;">
            <summary style="font-family:'Reem Kufi',sans-serif; font-size:1.1rem; color:#0D1B1B; cursor:pointer; font-weight:600;">{q}</summary>
            <p style="color:#6b6356; line-height:1.7; margin-top:12px; padding-top:12px; border-top:1px solid #f0ede5;">{a}</p>
        </details>'''
    faq_html += '</div>'
    
    # FAQPage Schema
    faq_schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq_schema]
    }, ensure_ascii=False)
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>الأسئلة الشائعة</h1>
        <p>إجابات على أكثر الأسئلة شيوعاً عن العقارات في الخرج والرياض. لم تجد إجابتك؟ تواصل معنا مباشرة.</p>
    </div>
    {breadcrumb}
    {faq_html}
    <div style="text-align:center; margin: 40px 0;">
        <a href="https://wa.me/966545888931" target="_blank" class="luxury-cta-whatsapp" style="display:inline-flex; align-items:center; gap:10px; padding:14px 32px; background: #25D366; color: #fff; border-radius: 12px; text-decoration: none; font-weight: 700; font-size: 1.1rem;">
            <i class="fab fa-whatsapp"></i> لديك سؤال آخر؟ اسألنا
        </a>
    </div>
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>
<script type="application/ld+json">{faq_schema_json}</script>'''
    
    html = make_head(title, desc, keywords, "faq.html") + "\n" + make_header("faq") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'faq.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ faq.html created")

# ===== Generate compare.html =====
def gen_compare():
    title = "مقارنة العقارات | قارن بين العقارات في الخرج والرياض | آفاق الإنجاز"
    desc = "قارن بين العقارات المتاحة في الخرج والرياض — السعر، المساحة، المنطقة، المميزات. أضف العقارات للمقارنة واتخذ القرار الأفضل."
    keywords = "مقارنة عقارات, قارن مزارع, قارن استراحات, قارن أراضي, مقارنة عقارية, الخرج, الرياض, آفاق الإنجاز"
    
    breadcrumb = make_breadcrumb([
        ("الرئيسية", "index.html"),
        ("مقارنة العقارات", "compare.html"),
    ], "compare.html")
    
    content = f'''<div class="silo-hub-page">
    <div class="silo-hub-header">
        <h1>مقارنة العقارات</h1>
        <p>أضف العقارات التي تهمك للمقارنة من صفحات العقارات الفردية، ثم عد إلى هنا لمقارنتها جنباً إلى جنب.</p>
    </div>
    {breadcrumb}
    <div id="compare-container" style="min-height: 300px;">
        <div id="compare-empty" style="text-align:center; padding: 60px 20px; background:#f8f6f0; border-radius:12px;">
            <i class="fas fa-balance-scale" style="font-size:3rem; color:#C4A956; margin-bottom:16px;"></i>
            <h3 style="color:#0D1B1B; margin:0 0 8px;">لا توجد عقارات للمقارنة</h3>
            <p style="color:#6b6356;">تصفح العقارات وأضفها للمقارنة بالضغط على زر "أضف للمقارنة"</p>
            <a href="farms.html" class="silo-hub-card-link" style="display:inline-block; margin-top:16px; padding:12px 24px;">تصفح العقارات</a>
        </div>
        <div id="compare-table-container" style="display:none;"></div>
    </div>
    {make_silo_links("روابط ذات صلة", SILO_LINKS)}
</div>'''
    
    html = make_head(title, desc, keywords, "compare.html") + "\n" + make_header("compare") + "\n" + content + "\n" + footer_block + "\n" + make_footer_scripts()
    with open(os.path.join(REPO, 'compare.html'), 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ compare.html created")

# ===== Run all =====
if __name__ == '__main__':
    gen_categories()
    gen_areas()
    gen_guides()
    gen_why_us()
    gen_faq()
    gen_compare()
    print("\n🎉 All 6 hub pages generated!")
