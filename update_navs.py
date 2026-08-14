#!/usr/bin/env python3
"""
Phase 3 §3: Update navigation menus in ALL existing pages to reflect
the new hierarchical silo. ADDS new links — does NOT remove existing ones.
Also adds silo.css and silo.js to each page.
"""
import os
import re

REPO = os.path.dirname(os.path.abspath(__file__))

# New nav items (same as generate_hubs.py)
NAV_ITEMS = [
    ("index.html", "home", "fa-home", "الرئيسية"),
    ("categories.html", "categories", "fa-th-large", "الأقسام"),
    ("farms.html", "farms", "fa-seedling", "المزارع"),
    ("resthouses.html", "resthouses", "resthouses", "الاستراحات"),
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

# Map filename → active key
FILE_ACTIVE = {
    'index.html': 'home',
    'farms.html': 'farms',
    'resthouses.html': 'resthouses',
    'lands.html': 'lands',
    'services.html': 'services',
    'contact.html': 'contact',
    'inquiry.html': 'contact',  # inquiry is part of contact flow
    'list-property.html': 'list-property',
    'property.html': None,  # property page is detail, no active
    '404.html': None,
    'admin.html': None,
}

def make_nav(active_key):
    items = []
    for href, key, icon, label in NAV_ITEMS:
        cls = ' class="active"' if active_key == key else ''
        items.append(f'                    <li><a href="{href}"{cls}><i class="fas {icon}"></i> {label}</a></li>')
    return '<ul class="nav-menu" id="nav-menu">\n' + '\n'.join(items) + '\n                </ul>'

# Pages to update (all that have nav-menu)
PAGES = ['index.html', 'farms.html', 'resthouses.html', 'lands.html', 'services.html', 
         'contact.html', 'inquiry.html', 'list-property.html', 'property.html']

def update_page(filepath, active_key):
    content = open(filepath, encoding='utf-8').read()
    
    # 1. Replace nav menu (if exists)
    nav_pattern = r'<ul class="nav-menu" id="nav-menu">.*?</ul>'
    new_nav = make_nav(active_key)
    new_content, nav_count = re.subn(nav_pattern, lambda m: new_nav, content, count=1, flags=re.DOTALL)
    if nav_count == 0:
        print(f"  ⚠️ {filepath}: no nav-menu found")
        return False
    content = new_content
    
    # 2. Add silo.css after luxury.css (if not already present)
    if 'css/silo.css' not in content:
        content = content.replace(
            '<link rel="stylesheet" href="css/luxury.css">',
            '<link rel="stylesheet" href="css/luxury.css">\n    <link rel="stylesheet" href="css/silo.css">',
            1
        )
    
    # 3. Add silo.js before </body> (if not already present)
    if 'js/silo.js' not in content:
        # Find the last script tag before </body> or just add before </body>
        content = content.replace(
            '</body>',
            '    <script src="js/silo.js"></script>\n</body>',
            1
        )
    
    # 4. Add favorites counter badge to header buttons (if not present)
    if 'fav-counter-badge' not in content:
        # Add badge to the WhatsApp button in header
        content = content.replace(
            'class="contact-icon-btn btn-whatsapp"',
            'class="contact-icon-btn btn-whatsapp" style="position:relative;"',
            1
        )
        # Actually, better to add a dedicated favorites link in header buttons
        # Let's add it after the phone button
        old_phone = 'class="contact-icon-btn btn-phone"'
        if old_phone in content:
            fav_link = '''<a href="#" onclick="document.getElementById('luxury-compare-drawer'); return false;" class="contact-icon-btn" id="header-fav-link" title="المفضلة" style="position:relative; color:#C4A956;">
                    <i class="fas fa-heart"></i>
                    <span class="fav-counter-badge"></span>
                </a>'''
            # Insert before the menu toggle button
            content = content.replace(
                '<button class="btn-menu-toggle"',
                fav_link + '\n                <button class="btn-menu-toggle"',
                1
            )
    
    open(filepath, 'w', encoding='utf-8').write(content)
    return True

# Run updates
print("Updating navigation in existing pages...")
for page in PAGES:
    filepath = os.path.join(REPO, page)
    if not os.path.exists(filepath):
        print(f"  ⚠️ {page}: file not found")
        continue
    active = FILE_ACTIVE.get(page)
    if update_page(filepath, active):
        print(f"  ✅ {page}: nav updated, silo.css + silo.js added, fav badge added")
    else:
        print(f"  ❌ {page}: update failed")

print("\nDone!")
