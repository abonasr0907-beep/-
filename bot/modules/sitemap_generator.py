# bot/modules/sitemap_generator.py (جديد)

from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom.minidom import parseString
from bot.database import load_properties

def generate_sitemap(output_path='sitemap.xml'):
    urlset = Element('urlset')
    urlset.set('xmlns', 'http://www.sitemaps.org/schemas/sitemap/0.9')

    # الصفحة الرئيسية
    add_url(urlset, 'https://abonasr0907-beep.github.io/', '1.0', 'daily')

    # صفحات العقارات
    properties = load_properties()
    for prop in properties:
        add_url(urlset, f"https://abonasr0907-beep.github.io/?p={prop['id']}", '0.8', 'weekly')

    # صفحات المناطق
    areas = ['الرحمانية', 'الهياثم', 'الدلم', 'الضبيعة', 'العفجة']
    for area in areas:
        add_url(urlset, f"https://abonasr0907-beep.github.io/areas/{area}.html", '0.7', 'weekly')

    # صفحات المدونة
    add_url(urlset, 'https://abonasr0907-beep.github.io/blog.html', '0.6', 'weekly')

    # تنسيق XML
    xml_str = tostring(urlset, encoding='unicode')
    dom = parseString(xml_str)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(dom.toprettyxml())

    print("✅ Sitemap generated successfully!")
    return output_path

def add_url(urlset, loc, priority, changefreq):
    url = SubElement(urlset, 'url')
    SubElement(url, 'loc').text = loc
    SubElement(url, 'lastmod').text = datetime.now().strftime('%Y-%m-%d')
    SubElement(url, 'changefreq').text = changefreq
    SubElement(url, 'priority').text = priority
