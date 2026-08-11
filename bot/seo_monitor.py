#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
نظام مراقبة SEO الأسبوعي الذكي — Phase 6.2 Automated Weekly SEO Intelligence System

يقوم هذا النظام بفحص الموقع أسبوعياً في المجالات التالية:
  - Google Search Console (عبر sitemap و robots.txt)
  - Sitemap.xml (التحقق من الصحة والروابط)
  - Robots.txt (التحقق من الإعدادات)
  - Indexed Pages (عدد الصفحات المفهرسة المتوقعة)
  - Crawl Errors (أخطاء الزحف — 404، 500، إلخ)
  - 404 Pages (الصفحات المفقودة)
  - Duplicate Content (المحتوى المكرر)
  - Canonical Issues (مشاكل الكنونيكال)
  - Schema Errors (أخطاء البيانات المنظمة JSON-LD)
  - Page Speed (سرعة الصفحة — حجم الملفات)
  - Mobile SEO (التوافق مع الجوال)
  - Keyword Performance (أداء الكلمات المفتاحية)

يقوم بإنشاء:
  - SEO Health Score (نقاط صحة SEO)
      Technical SEO: %
      Content SEO: %
      Indexing: %
      Keywords: %
  - تقرير أسبوعي: WEEKLY_SEO_REPORT.md
  - نظام اقتراحات: Problem → Analysis → Recommendation → Admin Approval → Apply

مهم: لا يقوم بالتعديل المباشر على أي صفحة.
مهم: ممنوع حذف صفحات مفهرسة.
مهم: ممنوع تغيير روابط بدون Redirect 301.
"""

import json
import os
import re
import time
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from html.parser import HTMLParser

logger = logging.getLogger("afaq_bot.seo_monitor")

# ============================================================
# المسارات
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
WEBSITE_DIR = BASE_DIR.parent  # مجلد الموقع (المجلد الأب لـ bot/)
REPORTS_DIR = DATA_DIR / "seo_reports"
SUGGESTIONS_FILE = DATA_DIR / "seo_suggestions.json"
SEO_HISTORY_FILE = DATA_DIR / "seo_history.json"
KEYWORDS_MASTER = WEBSITE_DIR / "SEO_KEYWORDS_MASTER.json"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# إعدادات الموقع
SITE_BASE_URL = "https://abonasr0907-beep.github.io/-/"

# قائمة الصفحات المعروفة في الموقع (للتحقق من الفهرسة والروابط)
KNOWN_PAGES = [
    "index.html", "farms.html", "resthouses.html", "lands.html",
    "services.html", "contact.html", "inquiry.html", "property.html",
    "list-property.html", "admin.html",
    "farms-riyadh/index.html", "farms-alkharj/index.html",
    "resthouses-riyadh/index.html", "resthouses-alkharj/index.html",
    "lands-riyadh/index.html", "lands-alkharj/index.html",
    "real-estate-riyadh/index.html", "real-estate-alkharj/index.html",
    "property-management-riyadh/index.html",
    "well-drilling-services/index.html", "well-location-services/index.html",
]

# الصفحات المفهرسة (لا يجب حذفها أبداً)
INDEXED_PAGES = [
    "index.html", "farms.html", "resthouses.html", "lands.html",
    "services.html", "contact.html", "inquiry.html", "property.html",
    "list-property.html",
    "farms-riyadh/index.html", "farms-alkharj/index.html",
    "resthouses-riyadh/index.html", "resthouses-alkharj/index.html",
    "lands-riyadh/index.html", "lands-alkharj/index.html",
    "real-estate-riyadh/index.html", "real-estate-alkharj/index.html",
    "property-management-riyadh/index.html",
    "well-drilling-services/index.html", "well-location-services/index.html",
]


# ============================================================
# أدوات مساعدة
# ============================================================
def _load_json(filepath, default=None):
    """تحميل ملف JSON مع قيمة افتراضية."""
    if default is None:
        default = {}
    try:
        if Path(filepath).exists():
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"seo_monitor: خطأ تحميل {filepath}: {e}")
    return default


def _save_json(filepath, data):
    """حفظ ملف JSON."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"seo_monitor: خطأ حفظ {filepath}: {e}")
        return False


def _fetch_url(url, timeout=15):
    """جلب محتوى رابط مع مهلة زمنية."""
    try:
        headers = {
            "User-Agent": "AfaqSEO-Monitor/1.0 (+https://abonasr0907-beep.github.io/-/)"
        }
        r = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        return r
    except requests.exceptions.Timeout:
        logger.warning(f"seo_monitor: مهلة في جلب {url}")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.warning(f"seo_monitor: خطأ اتصال {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"seo_monitor: خطأ جلب {url}: {e}")
        return None


def _read_file_content(filepath):
    """قراءة محتوى ملف محلي."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.warning(f"seo_monitor: خطأ قراءة {filepath}: {e}")
        return None


# ============================================================
# HTML Parser لاستخراج عناصر SEO
# ============================================================
class SEOHTMLAnalyzer(HTMLParser):
    """محلل HTML لاستخراج عناصر SEO من الصفحة."""

    def __init__(self):
        super().__init__()
        self.title = None
        self.meta_description = None
        self.meta_keywords = None
        self.canonical = None
        self.og_title = None
        self.og_description = None
        self.h1_tags = []
        self.h2_tags = []
        self.h3_tags = []
        self.alt_texts = []
        self.schema_blocks = []
        self.robot_meta = None
        self.viewport = None
        self._in_title = False
        self._in_h1 = False
        self._in_h2 = False
        self._in_h3 = False
        self._in_schema = False
        self._schema_content = ""
        self._title_content = ""
        self._h1_content = ""
        self._h2_content = ""
        self._h3_content = ""
        self.lang = None
        self.dir = None

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "html":
            self.lang = attrs_dict.get("lang")
            self.dir = attrs_dict.get("dir")
        elif tag == "title":
            self._in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta_description = content
            elif name == "keywords":
                self.meta_keywords = content
            elif name == "robots":
                self.robot_meta = content
            elif name == "viewport":
                self.viewport = content
            elif prop == "og:title":
                self.og_title = content
            elif prop == "og:description":
                self.og_description = content
        elif tag == "link":
            if attrs_dict.get("rel", "").lower() == "canonical":
                self.canonical = attrs_dict.get("href")
        elif tag == "h1":
            self._in_h1 = True
            self._h1_content = ""
        elif tag == "h2":
            self._in_h2 = True
            self._h2_content = ""
        elif tag == "h3":
            self._in_h3 = True
            self._h3_content = ""
        elif tag == "img":
            alt = attrs_dict.get("alt", "")
            if alt:
                self.alt_texts.append(alt)
        elif tag == "script":
            script_type = attrs_dict.get("type", "")
            if "ld+json" in script_type:
                self._in_schema = True
                self._schema_content = ""

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
            self.title = self._title_content.strip()
            self._title_content = ""
        elif tag == "h1":
            self._in_h1 = False
            self.h1_tags.append(self._h1_content.strip())
            self._h1_content = ""
        elif tag == "h2":
            self._in_h2 = False
            self.h2_tags.append(self._h2_content.strip())
            self._h2_content = ""
        elif tag == "h3":
            self._in_h3 = False
            self.h3_tags.append(self._h3_content.strip())
            self._h3_content = ""
        elif tag == "script":
            if self._in_schema:
                self._in_schema = False
                self.schema_blocks.append(self._schema_content.strip())
                self._schema_content = ""

    def handle_data(self, data):
        if self._in_title:
            self._title_content += data
        elif self._in_h1:
            self._h1_content += data
        elif self._in_h2:
            self._h2_content += data
        elif self._in_h3:
            self._h3_content += data
        elif self._in_schema:
            self._schema_content += data


def analyze_html(html_content):
    """تحليل محتوى HTML واستخراج عناصر SEO."""
    analyzer = SEOHTMLAnalyzer()
    try:
        analyzer.feed(html_content)
    except Exception as e:
        logger.warning(f"seo_monitor: خطأ تحليل HTML: {e}")
    return analyzer


# ============================================================
# الفحوصات الفردية — كل فحص يعيد dict بالنتائج
# ============================================================

def check_sitemap():
    """
    فحص Sitemap.xml
    - التحقق من وجود الملف
    - التحقق من صحة XML
    - عد الروابط
    - التحقق من آخر تحديث
    """
    result = {
        "name": "Sitemap.xml",
        "category": "Indexing",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    sitemap_path = WEBSITE_DIR / "sitemap.xml"
    content = _read_file_content(sitemap_path)

    if not content:
        result["status"] = "critical"
        result["issues"].append("ملف sitemap.xml غير موجود أو فارغ")
        result["score"] = 0
        return result

    result["details"]["file_exists"] = True
    result["details"]["file_size"] = len(content)

    # التحقق من صحة XML الأساسية
    import xml.dom.minidom
    try:
        dom = xml.dom.minidom.parseString(content)
        urls = dom.getElementsByTagName("url")
        url_count = len(urls)
        result["details"]["url_count"] = url_count

        # استخراج الروابط
        locs = []
        for url in urls:
            loc_elems = url.getElementsByTagName("loc")
            for loc in loc_elems:
                locs.append(loc.firstChild.nodeValue if loc.firstChild else "")

        result["details"]["urls"] = locs[:50]  # أول 50 رابط

        # التحقق من وجود روابط
        if url_count == 0:
            result["status"] = "critical"
            result["issues"].append("لا توجد روابط في sitemap.xml")
            result["score"] = 0
        elif url_count < 10:
            result["status"] = "warning"
            result["issues"].append(f"عدد الروابط قليل: {url_count} (المتوقع 19+)")
            result["score"] = 60
        else:
            result["status"] = "ok"
            result["score"] = 100

        # التحقق من آخر تحديث (lastmod)
        lastmods = dom.getElementsByTagName("lastmod")
        if lastmods:
            latest = max(l.firstChild.nodeValue for l in lastmods if l.firstChild)
            result["details"]["latest_lastmod"] = latest
            # التحقق من حداثة التحديث
            try:
                latest_date = datetime.strptime(latest[:10], "%Y-%m-%d")
                days_old = (datetime.now() - latest_date).days
                result["details"]["days_since_update"] = days_old
                if days_old > 30:
                    result["status"] = "warning" if result["status"] == "ok" else result["status"]
                    result["issues"].append(f"sitemap.xml لم يُحدّث منذ {days_old} يوم")
                    result["score"] = min(result["score"], 70)
            except Exception:
                pass
        else:
            result["issues"].append("لا توجد حقول lastmod في sitemap.xml")
            result["score"] = min(result["score"], 80)

    except Exception as e:
        result["status"] = "critical"
        result["issues"].append(f"خطأ في تحليل XML: {e}")
        result["score"] = 0

    # فحص sitemap عبر الويب
    sitemap_url = SITE_BASE_URL + "sitemap.xml"
    r = _fetch_url(sitemap_url, timeout=10)
    if r:
        result["details"]["accessible_online"] = (r.status_code == 200)
        if r.status_code != 200:
            result["status"] = "warning"
            result["issues"].append(f"sitemap.xml غير قابل للوصول عبر الويب (HTTP {r.status_code})")
            result["score"] = min(result["score"], 50)
    else:
        result["details"]["accessible_online"] = False
        result["issues"].append("تعذر الوصول إلى sitemap.xml عبر الويب")

    return result


def check_robots_txt():
    """
    فحص Robots.txt
    - التحقق من وجود الملف
    - التحقق من Allow للصفحات المهمة
    - التحقق من Disallow للأقسام الحساسة
    - التحقق من وجود رابط Sitemap
    """
    result = {
        "name": "Robots.txt",
        "category": "Indexing",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    robots_path = WEBSITE_DIR / "robots.txt"
    content = _read_file_content(robots_path)

    if not content:
        result["status"] = "critical"
        result["issues"].append("ملف robots.txt غير موجود")
        result["score"] = 0
        return result

    result["details"]["file_exists"] = True
    content_lower = content.lower()

    # التحقق من Allow: /
    if "allow: /" in content_lower or "allow:/" in content_lower.replace(" ", ""):
        result["details"]["allows_root"] = True
    else:
        result["issues"].append("robots.txt لا يسمح بالوصول للجذر (Allow: /)")
        result["score"] = max(result["score"], 0)

    # التحقق من Disallow للأقسام الحساسة
    sensitive_dirs = ["/bot/", "/docs/", "/admin.html"]
    for d in sensitive_dirs:
        if f"disallow: {d}" in content_lower or f"disallow:{d}" in content_lower.replace(" ", ""):
            result["details"][f"disallows_{d.replace('/', '_')}"] = True
        else:
            result["issues"].append(f"robots.txt لا يمنع الوصول لـ {d}")

    # التحقق من رابط Sitemap
    if "sitemap:" in content_lower:
        result["details"]["has_sitemap_ref"] = True
        # استخراج رابط sitemap
        for line in content.split("\n"):
            if line.strip().lower().startswith("sitemap:"):
                result["details"]["sitemap_url"] = line.split(":", 1)[1].strip()
                break
    else:
        result["issues"].append("robots.txt لا يحتوي على رابط Sitemap")

    # التحقق عبر الويب
    robots_url = SITE_BASE_URL + "robots.txt"
    r = _fetch_url(robots_url, timeout=10)
    if r:
        result["details"]["accessible_online"] = (r.status_code == 200)
        if r.status_code != 200:
            result["issues"].append(f"robots.txt غير قابل للوصول عبر الويب (HTTP {r.status_code})")

    # حساب النقاط
    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif len(result["issues"]) <= 2:
        result["status"] = "warning"
        result["score"] = 70
    else:
        result["status"] = "warning"
        result["score"] = 50

    return result


def check_indexed_pages():
    """
    فحص الصفحات المفهرسة
    - التحقق من وجود جميع الصفحات المعروفة
    - مقارنة مع sitemap.xml
    - التحقق من قابلية الوصول
    """
    result = {
        "name": "Indexed Pages",
        "category": "Indexing",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    found_pages = []
    missing_pages = []
    accessible_count = 0

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        exists = filepath.exists()
        result["details"][page] = {"exists_locally": exists}

        if exists:
            found_pages.append(page)
            # فحص قابلية الوصول عبر الويب (بشكل محدود لتوفير الوقت)
            if page.endswith("index.html"):
                web_path = page.replace("index.html", "")
            else:
                web_path = page
            url = SITE_BASE_URL + web_path
            r = _fetch_url(url, timeout=8)
            if r and r.status_code == 200:
                accessible_count += 1
                result["details"][page]["accessible"] = True
            else:
                result["details"][page]["accessible"] = False
                if r:
                    result["details"][page]["http_status"] = r.status_code
        else:
            missing_pages.append(page)

    result["details"]["total_known_pages"] = len(KNOWN_PAGES)
    result["details"]["found_locally"] = len(found_pages)
    result["details"]["missing_locally"] = len(missing_pages)
    result["details"]["accessible_online"] = accessible_count

    if missing_pages:
        result["status"] = "critical"
        result["issues"].append(f"صفحات مفقودة محلياً: {', '.join(missing_pages[:5])}")
        result["score"] = int((len(found_pages) / len(KNOWN_PAGES)) * 100)
    elif accessible_count < len(found_pages) * 0.8:
        result["status"] = "warning"
        result["issues"].append(f"بعض الصفحات غير متاحة عبر الويب: {accessible_count}/{len(found_pages)} متاحة")
        result["score"] = 70
    else:
        result["status"] = "ok"
        result["score"] = 100
        result["details"]["all_accessible"] = True

    return result


def check_crawl_errors():
    """
    فحص أخطاء الزحف
    - فحص صفحات 404 معروفة
    - فحص رموز HTTP للأخطاء
    - التحقق من صفحة 404 المخصصة
    """
    result = {
        "name": "Crawl Errors",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    # التحقق من وجود صفحة 404 مخصصة
    custom_404 = WEBSITE_DIR / "404.html"
    if custom_404.exists():
        result["details"]["custom_404_exists"] = True
        content = _read_file_content(custom_404)
        if content and ("redirect" in content.lower() or "window.location" in content.lower()):
            result["details"]["404_has_redirect"] = True
        else:
            result["issues"].append("صفحة 404 لا تحتوي على إعادة توجيه")
    else:
        result["status"] = "warning"
        result["issues"].append("لا توجد صفحة 404 مخصصة")
        result["score"] = 60

    # فحص روابط معطوبة محتملة (صفحات مرتبطة ولكن غير موجودة)
    broken_links = []
    for page in KNOWN_PAGES[:5]:  # فحص أول 5 صفحات لتوفير الوقت
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        # استخراج الروابط الداخلية
        links = re.findall(r'href=["\']([^"\']+)["\']', content)
        for link in links:
            # تجاهل الروابط الخارجية والمراسي والـ JS
            if link.startswith("http") or link.startswith("#") or link.startswith("javascript:") or link.startswith("mailto:") or link.startswith("tel:"):
                continue
            # تحويل المسار النسبي
            link_clean = link.split("#")[0].split("?")[0]
            if not link_clean or link_clean == "/":
                continue
            # تحديد المسار الكامل
            if page.endswith("index.html"):
                base = str((WEBSITE_DIR / page).parent)
            else:
                base = str(WEBSITE_DIR)
            full_path = Path(base) / link_clean.replace("../", "")
            # التحقق من الوجود (تقريبي)
            if not full_path.exists() and not link_clean.endswith(".css") and not link_clean.endswith(".js"):
                # محاولة أخرى: قد يكون المسار من جذر الموقع
                root_path = WEBSITE_DIR / link_clean.lstrip("/")
                if not root_path.exists():
                    broken_links.append(f"{page} → {link}")

    result["details"]["broken_links_found"] = len(broken_links)
    if broken_links:
        result["details"]["broken_links"] = broken_links[:10]
        result["issues"].append(f"روابط معطوبة محتملة: {len(broken_links)} رابط")
        result["status"] = "warning"
        result["score"] = 60
    else:
        result["details"]["broken_links"] = []
        if not result["issues"]:
            result["status"] = "ok"
            result["score"] = 100
        else:
            result["score"] = 80

    return result


def check_404_pages():
    """
    فحص صفحات 404
    - التحقق من أن جميع الصفحات في sitemap تعمل
    - فحص صفحات غير موجودة ترجع 404
    """
    result = {
        "name": "404 Pages",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    # فحص أن صفحة غير موجودة ترجع 404 (أو تتم إعادة توجيهها)
    test_url = SITE_BASE_URL + "this-page-does-not-exist-test-12345"
    r = _fetch_url(test_url, timeout=8)
    if r:
        if r.status_code == 404:
            result["details"]["404_returns_proper_status"] = True
            result["score"] = 100
            result["status"] = "ok"
        elif r.status_code == 200 and "404" in r.text[:2000]:
            # GitHub Pages يرجع 200 مع صفحة 404.html المخصصة
            result["details"]["custom_404_served"] = True
            result["score"] = 90
            result["status"] = "ok"
            result["issues"].append("صفحات 404 تُخدم عبر 404.html المخصص (GitHub Pages)")
        else:
            result["details"]["404_status"] = r.status_code
            result["status"] = "warning"
            result["issues"].append(f"صفحة غير موجودة ترجع HTTP {r.status_code} بدلاً من 404")
            result["score"] = 60
    else:
        result["status"] = "warning"
        result["issues"].append("تعذر فحص صفحة 404 عبر الويب")
        result["score"] = 70

    return result


def check_duplicate_content():
    """
    فحص المحتوى المكرر
    - مقارنة عناوين الصفحات (يجب أن تكون فريدة)
    - مقارنة وصف الميتا (يجب أن يكون فريداً)
    - مقارنة محتوى H1 (يجب أن يكون فريداً)
    """
    result = {
        "name": "Duplicate Content",
        "category": "Content",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    titles = {}
    descriptions = {}
    h1s = {}
    duplicate_titles = []
    duplicate_descs = []
    duplicate_h1s = []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        # العنوان
        if analyzer.title:
            if analyzer.title in titles:
                duplicate_titles.append((page, titles[analyzer.title]))
            else:
                titles[analyzer.title] = page

        # الوصف
        if analyzer.meta_description:
            if analyzer.meta_description in descriptions:
                duplicate_descs.append((page, descriptions[analyzer.meta_description]))
            else:
                descriptions[analyzer.meta_description] = page

        # H1
        for h1 in analyzer.h1_tags:
            if h1 in h1s:
                duplicate_h1s.append((page, h1s[h1], h1))
            else:
                h1s[h1] = page

    result["details"]["total_titles"] = len(titles)
    result["details"]["total_descriptions"] = len(descriptions)
    result["details"]["duplicate_titles"] = len(duplicate_titles)
    result["details"]["duplicate_descriptions"] = len(duplicate_descs)
    result["details"]["duplicate_h1s"] = len(duplicate_h1s)

    if duplicate_titles:
        result["issues"].append(f"عناوين مكررة: {len(duplicate_titles)}")
        for p1, p2 in duplicate_titles[:3]:
            result["issues"].append(f"  '{p1}' مكرر مع '{p2}'")

    if duplicate_descs:
        result["issues"].append(f"أوصاف ميتا مكررة: {len(duplicate_descs)}")

    if duplicate_h1s:
        result["issues"].append(f"علامات H1 مكررة: {len(duplicate_h1s)}")
        for p1, p2, h1 in duplicate_h1s[:3]:
            result["issues"].append(f"  H1 '{h1[:40]}' مكرر في '{p1}' و '{p2}'")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif len(result["issues"]) <= 2:
        result["status"] = "warning"
        result["score"] = 75
    else:
        result["status"] = "warning"
        result["score"] = 50

    return result


def check_canonical_issues():
    """
    فحص مشاكل الكنونيكال
    - التحقق من وجود وسم canonical في كل صفحة
    - التحقق من صحة رابط الكنونيكال
    """
    result = {
        "name": "Canonical Issues",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    pages_with_canonical = 0
    pages_without_canonical = []
    invalid_canonicals = []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        if analyzer.canonical:
            pages_with_canonical += 1
            # التحقق من صحة الرابط
            if not analyzer.canonical.startswith("http"):
                invalid_canonicals.append((page, analyzer.canonical))
        else:
            pages_without_canonical.append(page)

    result["details"]["pages_with_canonical"] = pages_with_canonical
    result["details"]["pages_without_canonical"] = len(pages_without_canonical)
    result["details"]["invalid_canonicals"] = len(invalid_canonicals)

    if pages_without_canonical:
        result["issues"].append(f"صفحات بدون وسم canonical: {len(pages_without_canonical)}")
        if len(pages_without_canonical) <= 5:
            result["issues"].append(f"  الصفحات: {', '.join(pages_without_canonical[:5])}")

    if invalid_canonicals:
        result["issues"].append(f"روابط canonical غير صالحة: {len(invalid_canonicals)}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif pages_without_canonical and not invalid_canonicals:
        result["status"] = "warning"
        result["score"] = 70
    else:
        result["status"] = "warning"
        result["score"] = 50

    return result


def check_schema_errors():
    """
    فحص أخطاء البيانات المنظمة (Schema.org / JSON-LD)
    - التحقق من وجود JSON-LD في كل صفحة
    - التحقق من صحة JSON
    - التحقق من وجود الحقول المطلوبة
    """
    result = {
        "name": "Schema Errors",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    pages_with_schema = 0
    pages_without_schema = []
    schema_errors = []
    schema_types_found = set()

    required_fields = {
        "RealEstateAgent": ["name", "url", "telephone"],
        "CollectionPage": ["name", "url"],
        "Service": ["name", "provider"],
        "FAQPage": ["mainEntity"],
        "BreadcrumbList": ["itemListElement"],
        "Product": ["name"],
    }

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        if not analyzer.schema_blocks:
            pages_without_schema.append(page)
            continue

        pages_with_schema += 1
        for i, block in enumerate(analyzer.schema_blocks):
            try:
                data = json.loads(block)
                schema_type = data.get("@type", "unknown")
                schema_types_found.add(schema_type)

                # التحقق من الحقول المطلوبة
                if schema_type in required_fields:
                    for field in required_fields[schema_type]:
                        if field not in data:
                            schema_errors.append(f"{page} block#{i}: {schema_type} يفتقد الحقل '{field}'")
            except json.JSONDecodeError as e:
                schema_errors.append(f"{page} block#{i}: خطأ JSON — {e}")

    result["details"]["pages_with_schema"] = pages_with_schema
    result["details"]["pages_without_schema"] = len(pages_without_schema)
    result["details"]["schema_errors"] = len(schema_errors)
    result["details"]["schema_types_found"] = list(schema_types_found)

    if pages_without_schema:
        result["issues"].append(f"صفحات بدون بيانات منظمة: {len(pages_without_schema)}")
        if len(pages_without_schema) <= 5:
            result["issues"].append(f"  الصفحات: {', '.join(pages_without_schema[:5])}")

    if schema_errors:
        result["issues"].append(f"أخطاء في البيانات المنظمة: {len(schema_errors)}")
        for err in schema_errors[:5]:
            result["issues"].append(f"  {err}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif not schema_errors and pages_without_schema:
        result["status"] = "warning"
        result["score"] = 75
    elif schema_errors:
        result["status"] = "warning"
        result["score"] = 50
    else:
        result["status"] = "ok"
        result["score"] = 90

    return result


def check_page_speed():
    """
    فحص سرعة الصفحة
    - حجم ملفات HTML
    - عدد الصور وحجمها
    - وجود CSS/JS مضمّن (inline)
    - حجم الصفحة الإجمالي
    """
    result = {
        "name": "Page Speed",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    page_sizes = {}
    large_pages = []
    total_inline_css = 0
    total_inline_js = 0

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue

        size_kb = len(content.encode("utf-8")) / 1024
        page_sizes[page] = round(size_kb, 1)

        # الصفحات الكبيرة (> 100KB)
        if size_kb > 100:
            large_pages.append((page, round(size_kb, 1)))

        # CSS مضمّن
        inline_css = len(re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL))
        if inline_css:
            css_content = "".join(re.findall(r'<style[^>]*>(.*?)</style>', content, re.DOTALL))
            total_inline_css += len(css_content)

        # JS مضمّن
        inline_js = len(re.findall(r'<script[^>]*>(?!.*src=)(.*?)</script>', content, re.DOTALL))

    result["details"]["page_sizes_kb"] = page_sizes
    result["details"]["large_pages"] = len(large_pages)
    result["details"]["avg_page_size_kb"] = round(sum(page_sizes.values()) / max(len(page_sizes), 1), 1)
    result["details"]["total_inline_css_bytes"] = total_inline_css

    if large_pages:
        result["issues"].append(f"صفحات كبيرة (>100KB): {len(large_pages)}")
        for p, s in large_pages[:3]:
            result["issues"].append(f"  {p}: {s}KB")

    if total_inline_css > 50000:
        result["issues"].append(f"CSS مضمّن كبير: {total_inline_css / 1024:.0f}KB — يُنصح بنقله لملف خارجي")

    avg_size = result["details"]["avg_page_size_kb"]
    if not result["issues"]:
        if avg_size < 50:
            result["status"] = "ok"
            result["score"] = 100
        elif avg_size < 100:
            result["status"] = "ok"
            result["score"] = 85
        else:
            result["status"] = "warning"
            result["score"] = 70
    else:
        result["status"] = "warning"
        result["score"] = 60

    return result


def check_mobile_seo():
    """
    فحص التوافق مع الجوال (Mobile SEO)
    - التحقق من وجود viewport meta tag
    - التحقق من lang="ar" و dir="rtl"
    - التحقق من وجود CSS responsive
    """
    result = {
        "name": "Mobile SEO",
        "category": "Technical",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    pages_with_viewport = 0
    pages_with_rtl = 0
    pages_with_lang = 0
    pages_without_viewport = []
    pages_without_rtl = []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        if analyzer.viewport:
            pages_with_viewport += 1
            if "width=device-width" not in analyzer.viewport:
                result["issues"].append(f"{page}: viewport لا يحتوي على width=device-width")
        else:
            pages_without_viewport.append(page)

        if analyzer.dir == "rtl":
            pages_with_rtl += 1
        else:
            pages_without_rtl.append(page)

        if analyzer.lang:
            pages_with_lang += 1

    result["details"]["pages_with_viewport"] = pages_with_viewport
    result["details"]["pages_without_viewport"] = len(pages_without_viewport)
    result["details"]["pages_with_rtl"] = pages_with_rtl
    result["details"]["pages_with_lang"] = pages_with_lang

    if pages_without_viewport:
        result["issues"].append(f"صفحات بدون viewport meta: {len(pages_without_viewport)}")
        if len(pages_without_viewport) <= 5:
            result["issues"].append(f"  الصفحات: {', '.join(pages_without_viewport[:5])}")

    if pages_without_rtl:
        result["issues"].append(f"صفحات بدون dir='rtl': {len(pages_without_rtl)}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif pages_without_viewport:
        result["status"] = "warning"
        result["score"] = 60
    else:
        result["status"] = "ok"
        result["score"] = 85

    return result


def check_keyword_performance():
    """
    فحص أداء الكلمات المفتاحية
    - التحقق من وجود SEO_KEYWORDS_MASTER.json
    - التحقق من وجود كل كلمة في الصفحة المستهدفة
    - حساب نسبة التغطية
    - تحديد الكلمات الصاعدة (بناء على التاريخ)
    """
    result = {
        "name": "Keyword Performance",
        "category": "Keywords",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    # تحميل ملف الكلمات المفتاحية
    master = _load_json(KEYWORDS_MASTER)
    if not master or "keywords" not in master:
        result["status"] = "warning"
        result["issues"].append("ملف SEO_KEYWORDS_MASTER.json غير موجود أو فارغ")
        result["score"] = 50
        return result

    keywords = master["keywords"]
    page_map = master.get("page_keyword_map", {})

    result["details"]["total_keywords"] = len(keywords)
    result["details"]["total_page_mappings"] = len(page_map)

    # التحقق من وجود كل كلمة في صفحتها المستهدفة
    found_count = 0
    missing_keywords = []
    keyword_locations = {}

    for kw_entry in keywords:
        keyword = kw_entry["keyword"]
        target_page = kw_entry["target_page"]
        filepath = WEBSITE_DIR / target_page

        content = _read_file_content(filepath)
        if content and keyword in content:
            found_count += 1
            keyword_locations[keyword] = target_page
        else:
            missing_keywords.append(keyword)

    coverage = round((found_count / max(len(keywords), 1)) * 100, 1)
    result["details"]["keywords_found"] = found_count
    result["details"]["keywords_missing"] = len(missing_keywords)
    result["details"]["coverage_percent"] = coverage

    if missing_keywords:
        result["issues"].append(f"كلمات مفتاحية غير موجودة في صفحاتها: {len(missing_keywords)}")
        for kw in missing_keywords[:5]:
            result["issues"].append(f"  '{kw}'")

    # تحليل توزيع الكلمات حسب النوع
    type_distribution = {}
    for kw_entry in keywords:
        kw_type = kw_entry.get("type", "unknown")
        type_distribution[kw_type] = type_distribution.get(kw_type, 0) + 1
    result["details"]["type_distribution"] = type_distribution

    # تحديد الكلمات الصاعدة (بناء على التاريخ)
    history = _load_json(SEO_HISTORY_FILE, {"reports": []})
    rising_keywords = []
    if history.get("reports"):
        # مقارنة التغطية الحالية بالسابقة
        last_report = history["reports"][-1] if history["reports"] else None
        if last_report and "keyword_performance" in last_report:
            prev_coverage = last_report["keyword_performance"].get("coverage_percent", 0)
            if coverage > prev_coverage:
                result["details"]["trend"] = "improving"
                result["details"]["prev_coverage"] = prev_coverage
            elif coverage < prev_coverage:
                result["details"]["trend"] = "declining"
                result["issues"].append(f"انخفضت تغطية الكلمات من {prev_coverage}% إلى {coverage}%")
            else:
                result["details"]["trend"] = "stable"
    else:
        result["details"]["trend"] = "baseline"

    # الكلمات الصاعدة (الكلمات الموجودة في صفحات متعددة)
    multi_page_keywords = []
    for kw_entry in keywords:
        keyword = kw_entry["keyword"]
        pages_with_kw = 0
        for page_content_file in KNOWN_PAGES[:10]:
            content = _read_file_content(WEBSITE_DIR / page_content_file)
            if content and keyword in content:
                pages_with_kw += 1
        if pages_with_kw > 3:
            multi_page_keywords.append((keyword, pages_with_kw))

    result["details"]["rising_keywords"] = [(kw, count) for kw, count in sorted(multi_page_keywords, key=lambda x: x[1], reverse=True)[:10]]

    if coverage >= 95:
        result["status"] = "ok"
        result["score"] = 100
    elif coverage >= 80:
        result["status"] = "ok"
        result["score"] = 85
    elif coverage >= 60:
        result["status"] = "warning"
        result["score"] = 65
    else:
        result["status"] = "critical"
        result["score"] = 40

    return result


def check_meta_tags_completeness():
    """
    فحص اكتمال وسوم الميتا
    - Title (50-60 حرف)
    - Meta Description (150-160 حرف)
    - OG tags
    - Twitter Card tags
    - Keywords meta
    """
    result = {
        "name": "Meta Tags Completeness",
        "category": "Content",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    missing_titles = []
    missing_descs = []
    missing_og = []
    missing_keywords_meta = []
    short_titles = []
    short_descs = []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        if not analyzer.title:
            missing_titles.append(page)
        elif len(analyzer.title) < 30:
            short_titles.append((page, len(analyzer.title)))

        if not analyzer.meta_description:
            missing_descs.append(page)
        elif len(analyzer.meta_description) < 100:
            short_descs.append((page, len(analyzer.meta_description)))

        if not analyzer.og_title:
            missing_og.append(page)

        if not analyzer.meta_keywords:
            missing_keywords_meta.append(page)

    result["details"]["missing_titles"] = len(missing_titles)
    result["details"]["missing_descriptions"] = len(missing_descs)
    result["details"]["missing_og_tags"] = len(missing_og)
    result["details"]["missing_keywords_meta"] = len(missing_keywords_meta)
    result["details"]["short_titles"] = len(short_titles)
    result["details"]["short_descriptions"] = len(short_descs)

    if missing_titles:
        result["issues"].append(f"صفحات بدون title: {len(missing_titles)}")
    if missing_descs:
        result["issues"].append(f"صفحات بدون meta description: {len(missing_descs)}")
    if missing_og:
        result["issues"].append(f"صفحات بدون OG tags: {len(missing_og)}")
    if missing_keywords_meta:
        result["issues"].append(f"صفحات بدون keywords meta: {len(missing_keywords_meta)}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif len(result["issues"]) <= 1:
        result["status"] = "ok"
        result["score"] = 85
    else:
        result["status"] = "warning"
        result["score"] = 60

    return result


def check_image_alt_tags():
    """
    فحص وسوم ALT للصور
    - التحقق من وجود ALT لكل صورة
    - التحقق من أن ALT يحتوي على كلمات مفتاحية
    """
    result = {
        "name": "Image ALT Tags",
        "category": "Content",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    total_images = 0
    images_with_alt = 0
    images_without_alt = 0
    images_with_keyword_alt = 0

    # تحميل الكلمات المفتاحية للتحقق
    master = _load_json(KEYWORDS_MASTER)
    all_keywords = [k["keyword"] for k in master.get("keywords", [])] if master else []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue

        # إيجاد جميع وسوم img
        img_tags = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
        for img in img_tags:
            total_images += 1
            alt_match = re.search(r'alt=["\']([^"\']*)["\']', img, re.IGNORECASE)
            if alt_match:
                alt_text = alt_match.group(1)
                if alt_text.strip():
                    images_with_alt += 1
                    # التحقق من وجود كلمة مفتاحية في ALT
                    for kw in all_keywords:
                        if kw in alt_text:
                            images_with_keyword_alt += 1
                            break
                else:
                    images_without_alt += 1
            else:
                images_without_alt += 1

    result["details"]["total_images"] = total_images
    result["details"]["images_with_alt"] = images_with_alt
    result["details"]["images_without_alt"] = images_without_alt
    result["details"]["images_with_keyword_alt"] = images_with_keyword_alt

    if total_images > 0:
        alt_coverage = round((images_with_alt / total_images) * 100, 1)
        result["details"]["alt_coverage_percent"] = alt_coverage
    else:
        alt_coverage = 0

    if images_without_alt > 0:
        result["issues"].append(f"صور بدون ALT: {images_without_alt}/{total_images}")

    if total_images > 0 and images_with_keyword_alt < total_images * 0.5:
        result["issues"].append(f"معظم وسوم ALT لا تحتوي على كلمات مفتاحية: {images_with_keyword_alt}/{total_images}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    elif alt_coverage >= 80:
        result["status"] = "ok"
        result["score"] = 80
    else:
        result["status"] = "warning"
        result["score"] = 55

    return result


def check_heading_structure():
    """
    فحص هيكل العناوين
    - كل صفحة يجب أن تحتوي على H1 واحد
    - H2 و H3 يجب أن تتبع ترتيباً منطقياً
    - لا يجب أن توجد عناوين H1 متعددة
    """
    result = {
        "name": "Heading Structure",
        "category": "Content",
        "status": "unknown",
        "score": 0,
        "details": {},
        "issues": [],
    }

    pages_without_h1 = []
    pages_with_multiple_h1 = []

    for page in KNOWN_PAGES:
        filepath = WEBSITE_DIR / page
        content = _read_file_content(filepath)
        if not content:
            continue
        analyzer = analyze_html(content)

        h1_count = len(analyzer.h1_tags)
        if h1_count == 0:
            pages_without_h1.append(page)
        elif h1_count > 1:
            pages_with_multiple_h1.append((page, h1_count))

    result["details"]["pages_without_h1"] = len(pages_without_h1)
    result["details"]["pages_with_multiple_h1"] = len(pages_with_multiple_h1)

    if pages_without_h1:
        result["issues"].append(f"صفحات بدون H1: {len(pages_without_h1)}")
        if len(pages_without_h1) <= 5:
            result["issues"].append(f"  الصفحات: {', '.join(pages_without_h1[:5])}")

    if pages_with_multiple_h1:
        result["issues"].append(f"صفحات بعناوين H1 متعددة: {len(pages_with_multiple_h1)}")

    if not result["issues"]:
        result["status"] = "ok"
        result["score"] = 100
    else:
        result["status"] = "warning"
        result["score"] = 65

    return result


# ============================================================
# حساب نقاط صحة SEO (SEO Health Score)
# ============================================================
def calculate_health_score(checks):
    """
    حساب نقاط صحة SEO مقسمة على 4 فئات:
      - Technical SEO: %
      - Content SEO: %
      - Indexing: %
      - Keywords: %
    """
    categories = {
        "Technical": [],
        "Content": [],
        "Indexing": [],
        "Keywords": [],
    }

    for check in checks:
        cat = check.get("category", "Technical")
        score = check.get("score", 0)
        categories.setdefault(cat, []).append(score)

    health = {}
    for cat, scores in categories.items():
        if scores:
            health[cat] = round(sum(scores) / len(scores))
        else:
            health[cat] = 0

    # النتيجة الإجمالية
    health["Overall"] = round(sum(health.values()) / max(len(health), 1))

    return health


# ============================================================
# نظام الاقتراحات (Suggestion System)
# ============================================================
def generate_suggestions(checks, health_score):
    """
    توليد اقتراحات بناء على نتائج الفحص.
    النظام: Problem → Analysis → Recommendation → Admin Approval → Apply
    
    مهم: لا يقوم بالتعديل المباشر. يولد اقتراحات فقط.
    مهم: ممنوع حذف صفحات مفهرسة.
    مهم: ممنوع تغيير روابط بدون Redirect 301.
    """
    suggestions = []
    suggestion_id = 1

    for check in checks:
        if check["status"] in ("critical", "warning"):
            for issue in check.get("issues", []):
                suggestion = {
                    "id": f"SEO-{suggestion_id:03d}",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "check_name": check["name"],
                    "category": check["category"],
                    "problem": issue,
                    "analysis": _analyze_issue(check, issue),
                    "recommendation": _recommend_fix(check, issue),
                    "severity": check["status"],
                    "approval_status": "pending",  # pending | approved | rejected | applied
                    "approved_by": None,
                    "approved_date": None,
                    "applied_date": None,
                    "safety_note": _safety_note(check, issue),
                }
                suggestions.append(suggestion)
                suggestion_id += 1

    # اقتراحات تحسين بناء على النقاط
    if health_score.get("Technical", 100) < 80:
        suggestions.append({
            "id": f"SEO-{suggestion_id:03d}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "check_name": "Overall Technical",
            "category": "Technical",
            "problem": f"درجة Technical SEO منخفضة: {health_score.get('Technical', 0)}%",
            "analysis": "البنية التقنية للموقع تحتاج تحسين في عدة مجالات",
            "recommendation": "مراجعة الفحوصات التقنية وتطبيق الإصلاحات المقترحة بالترتيب حسب الأولوية",
            "severity": "warning",
            "approval_status": "pending",
            "approved_by": None,
            "approved_date": None,
            "applied_date": None,
            "safety_note": "تطبيق الإصلاحات التقنية آمن ولا يؤثر على الصفحات المفهرسة",
        })
        suggestion_id += 1

    if health_score.get("Content", 100) < 80:
        suggestions.append({
            "id": f"SEO-{suggestion_id:03d}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "check_name": "Overall Content",
            "category": "Content",
            "problem": f"درجة Content SEO منخفضة: {health_score.get('Content', 0)}%",
            "analysis": "محتوى الصفحات يحتاج تحسين في العناوين أو الأوصاف أو الصور",
            "recommendation": "تحسين وسوم الميتا والصور والعناوين في الصفحات المحددة",
            "severity": "warning",
            "approval_status": "pending",
            "approved_by": None,
            "approved_date": None,
            "applied_date": None,
            "safety_note": "تحسين المحتوى لا يتطلب حذف أو تغيير روابط",
        })
        suggestion_id += 1

    if health_score.get("Indexing", 100) < 80:
        suggestions.append({
            "id": f"SEO-{suggestion_id:03d}",
            "date": datetime.now().strftime("%Y-%m-%d"),
            "check_name": "Overall Indexing",
            "category": "Indexing",
            "problem": f"درجة Indexing منخفضة: {health_score.get('Indexing', 0)}%",
            "analysis": "هناك مشاكل في فهرسة الصفحات أو sitemap أو robots.txt",
            "recommendation": "إصلاح مشاكل الفهرسة وتحديث sitemap.xml و robots.txt",
            "severity": "warning",
            "approval_status": "pending",
            "approved_by": None,
            "approved_date": None,
            "applied_date": None,
            "safety_note": "⚠️ ممنوع حذف صفحات مفهرسة. ممنوع تغيير روابط بدون Redirect 301.",
        })
        suggestion_id += 1

    return suggestions


def _analyze_issue(check, issue):
    """تحليل المشكلة وإنشاء وصف تفصيلي."""
    name = check["name"]
    analyses = {
        "Sitemap.xml": "ملف sitemap.xml مهم لفهرسة الصفحات في محركات البحث. المشاكل فيه تؤخر الفهرسة.",
        "Robots.txt": "ملف robots.txt يتحكم في وصول محركات البحث. الإعدادات الخاطئة قد تمنع الفهرسة.",
        "Indexed Pages": "الصفحات المفقودة لا تظهر في نتائج البحث. كل صفحة مفقودة تعني فقدان زيارات محتملة.",
        "Crawl Errors": "أخطاء الزحف تستهلك ميزانية الزحف وتؤثر سلباً على ترتيب الموقع.",
        "404 Pages": "صفحات 404 السيئة تؤثر على تجربة المستخدم وثقة محركات البحث.",
        "Duplicate Content": "المحتوى المكرر يجعل محركات البحث لا تعرف أي صفحة تفضل، مما يضعف الترتيب.",
        "Canonical Issues": "بدون وسم canonical، قد تفهرس محركات البحث نسخاً مكررة من نفس الصفحة.",
        "Schema Errors": "البيانات المنظمة الخاطئة تمنع ظهور النتائج الغنية (Rich Snippets) في البحث.",
        "Page Speed": "بطء الصفحات يزيد معدل الارتداد ويؤثر على ترتيب Google (خاصة على الجوال).",
        "Mobile SEO": "عدم التوافق مع الجوال يخفض الترتيب لأن Google تعتمد Mobile-First Indexing.",
        "Keyword Performance": "الكلمات المفتاحية المفقودة تعني عدم الظهور في عمليات بحث محتملة.",
        "Meta Tags Completeness": "نقص وسوم الميتا يضعف ظهور الموقع في نتائج البحث ويرفع معدل الارتداد.",
        "Image ALT Tags": "صور بدون ALT لا تظهر في البحث عن الصور وتضعف إمكانية الوصول.",
        "Heading Structure": "هيكل العناوين الخاطئ يربك محركات البحث ويضعف فهم محتوى الصفحة.",
    }
    return analyses.get(name, f"المشكلة في فحص '{name}' تحتاج مراجعة وتحليل تفصيلي.")


def _recommend_fix(check, issue):
    """توليد توصية إصلاح بناء على نوع المشكلة."""
    name = check["name"]
    recommendations = {
        "Sitemap.xml": "تحديث ملف sitemap.xml والتأكد من وجود جميع الصفحات وإضافة lastmod محدث. إعادة إرساله إلى Google Search Console.",
        "Robots.txt": "تصحيح إعدادات robots.txt: التأكد من Allow: / و Disallow للأقسام الحساسة وإضافة رابط Sitemap.",
        "Indexed Pages": "التأكد من وجود جميع الصفحات محلياً ونشرها. فحص Google Search Console للصفحات غير المفهرسة.",
        "Crawl Errors": "إصلاح الروابط المعطوبة. ⚠️ استخدام Redirect 301 لأي رابط يتم تغييره (لا تستخدم 302).",
        "404 Pages": "التأكد من أن صفحة 404 المخصصة تعمل وتعيد التوجيه للصفحة المناسبة.",
        "Duplicate Content": "تخصيص عناوين وأوصاف فريدة لكل صفحة. إضافة وسم canonical إذا لزم الأمر.",
        "Canonical Issues": "إضافة وسم <link rel='canonical' href='URL'> لكل صفحة تحدد الرابط الأساسي.",
        "Schema Errors": "إصلاح أخطاء JSON-LD: إضافة الحقول المطلوبة والتأكد من صحة JSON. اختبار عبر Rich Results Test.",
        "Page Speed": "تقليل حجم الصفحات: نقل CSS المضمّن لملف خارجي، ضغط الصور، تقليل JavaScript.",
        "Mobile SEO": "إضافة <meta name='viewport' content='width=device-width, initial-scale=1.0'> لكل صفحة ناقصة.",
        "Keyword Performance": "إضافة الكلمات المفقودة إلى صفحاتها المستهدفة في Title و Meta Description و H2 و Content.",
        "Meta Tags Completeness": "إضافة title و meta description و OG tags و keywords meta للصفحات الناقصة.",
        "Image ALT Tags": "إضافة alt وصفية تحتوي على كلمات مفتاحية لكل صورة ناقصة.",
        "Heading Structure": "التأكد من وجود H1 واحد فقط في كل صفحة وترتيب منطقي للعناوين.",
    }
    return recommendations.get(name, f"مراجعة فحص '{name}' وتطبيق الإصلاح المناسب بناء على المشكلة المحددة.")


def _safety_note(check, issue):
    """ملاحظة أمان لكل اقتراح."""
    name = check["name"]
    if name in ("Crawl Errors", "404 Pages", "Indexed Pages"):
        return "⚠️ ممنوع حذف صفحات مفهرسة. ممنوع تغيير روابط بدون Redirect 301. التغييرات تتطلب موافقة الأدمن."
    elif name in ("Schema Errors", "Meta Tags Completeness", "Image ALT Tags", "Heading Structure"):
        return "✅ آمن: تحسين الوسوم لا يؤثر على الروابط أو الصفحات المفهرسة. يتطلب موافقة الأدمن قبل التطبيق."
    elif name in ("Duplicate Content", "Canonical Issues"):
        return "⚠️ إضافة canonical آمنة. لا تغيّر روابط موجودة. يتطلب موافقة الأدمن."
    elif name == "Page Speed":
        return "✅ آمن: تحسين السرعة لا يؤثر على المحتوى أو الروابط. يتطلب موافقة الأدمن."
    elif name == "Keyword Performance":
        return "✅ آمن: إضافة كلمات مفتاحية للمحتوى لا يتطلب حذف أو تغيير روابط. يتطلب موافقة الأدمن."
    else:
        return "⚠️ يتطلب موافقة الأدمن قبل التطبيق. لا تقم بتعديلات مباشرة."


def save_suggestions(suggestions):
    """حفظ الاقتراحات في ملف JSON لمراجعة الأدمن."""
    existing = _load_json(SUGGESTIONS_FILE, {"suggestions": [], "history": []})

    # دمج الاقتراحات الجديدة مع الموجودة (تحديث الحالة للمشاكل المستمرة)
    new_ids = {s["id"] for s in suggestions}
    old_pending = [s for s in existing.get("suggestions", []) if s.get("approval_status") == "pending"]

    # نقل الاقتراحات القديمة المعلقة إلى التاريخ إذا لم تعد موجودة
    for old_s in old_pending:
        if old_s["id"] not in new_ids:
            old_s["resolution"] = "resolved_auto"
            old_s["resolved_date"] = datetime.now().strftime("%Y-%m-%d")
            existing.setdefault("history", []).append(old_s)

    existing["suggestions"] = suggestions
    existing["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    _save_json(SUGGESTIONS_FILE, existing)
    return SUGGESTIONS_FILE


def approve_suggestion(suggestion_id, admin_id):
    """موافقة الأدمن على اقتراح (Admin Approval)."""
    data = _load_json(SUGGESTIONS_FILE, {"suggestions": []})
    for s in data.get("suggestions", []):
        if s["id"] == suggestion_id:
            s["approval_status"] = "approved"
            s["approved_by"] = admin_id
            s["approved_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            _save_json(SUGGESTIONS_FILE, data)
            return True, f"تمت الموافقة على الاقتراح {suggestion_id}"
    return False, f"الاقتراح {suggestion_id} غير موجود"


def reject_suggestion(suggestion_id, admin_id, reason=""):
    """رفض اقتراح من قبل الأدمن."""
    data = _load_json(SUGGESTIONS_FILE, {"suggestions": []})
    for s in data.get("suggestions", []):
        if s["id"] == suggestion_id:
            s["approval_status"] = "rejected"
            s["approved_by"] = admin_id
            s["approved_date"] = datetime.now().strftime("%Y-%m-%d %H:%M")
            s["rejection_reason"] = reason
            _save_json(SUGGESTIONS_FILE, data)
            return True, f"تم رفض الاقتراح {suggestion_id}"
    return False, f"الاقتراح {suggestion_id} غير موجود"


def get_pending_suggestions():
    """الحصول على الاقتراحات المعلقة."""
    data = _load_json(SUGGESTIONS_FILE, {"suggestions": []})
    return [s for s in data.get("suggestions", []) if s.get("approval_status") == "pending"]


# ============================================================
# توليد التقرير الأسبوعي
# ============================================================
def generate_weekly_report(checks, health_score, suggestions):
    """
    توليد تقرير أسبوعي بصيغة Markdown.
    يحتوي على:
      - حالة الموقع
      - المشاكل الموجودة
      - التحسينات المقترحة
      - الكلمات الصاعدة
      - الصفحات التي تحتاج تحديث
    """
    today = datetime.now().strftime("%Y-%m-%d")
    report_num = _get_report_number()

    lines = []
    lines.append(f"# تقرير SEO الأسبوعي #{report_num}")
    lines.append(f"# Weekly SEO Report #{report_num}")
    lines.append("")
    lines.append(f"**التاريخ:** {today}")
    lines.append(f"**الموقع:** {SITE_BASE_URL}")
    lines.append(f"**المكتب:** مكتب آفاق الإنجاز العقاري")
    lines.append(f"**نظام المراقبة:** Phase 6.2 — Automated Weekly SEO Intelligence")
    lines.append("")
    lines.append("---")
    lines.append("")

    # ============================================================
    # 1. حالة الموقع (Site Status)
    # ============================================================
    lines.append("## 1. حالة الموقع | Site Status")
    lines.append("")
    overall = health_score.get("Overall", 0)
    if overall >= 85:
        status_emoji = "🟢 ممتاز"
    elif overall >= 70:
        status_emoji = "🟡 جيد"
    elif overall >= 50:
        status_emoji = "🟠 يحتاج تحسين"
    else:
        status_emoji = "🔴 حرج"

    lines.append(f"**الحالة العامة:** {status_emoji} ({overall}%)")
    lines.append("")
    lines.append("### SEO Health Score | نقاط صحة SEO")
    lines.append("")
    lines.append("| الفئة | النسبة | الشريط |")
    lines.append("|---|---|---|")

    for cat in ["Technical", "Content", "Indexing", "Keywords"]:
        score = health_score.get(cat, 0)
        bar = "█" * (score // 5) + "░" * (20 - score // 5)
        lines.append(f"| {cat} SEO | {score}% | `{bar}` |")

    lines.append(f"| **الإجمالي** | **{overall}%** | `{'█' * (overall // 5)}{'░' * (20 - overall // 5)}` |")
    lines.append("")

    # ملخص الفحوصات
    lines.append("### ملخص الفحوصات | Checks Summary")
    lines.append("")
    lines.append("| الفحص | الفئة | الحالة | النسبة |")
    lines.append("|---|---|---|---|")
    for check in checks:
        status_map = {"ok": "✅ سليم", "warning": "⚠️ تحذير", "critical": "🔴 حرج", "unknown": "❓ غير معروف"}
        status_text = status_map.get(check["status"], check["status"])
        lines.append(f"| {check['name']} | {check['category']} | {status_text} | {check['score']}% |")
    lines.append("")

    # ============================================================
    # 2. المشاكل الموجودة (Problems Found)
    # ============================================================
    lines.append("## 2. المشاكل الموجودة | Problems Found")
    lines.append("")

    problems = []
    critical_problems = []
    for check in checks:
        if check["status"] == "critical":
            critical_problems.append(check)
        if check.get("issues"):
            problems.append(check)

    if critical_problems:
        lines.append("### 🔴 مشاكل حرجة | Critical Issues")
        lines.append("")
        for check in critical_problems:
            lines.append(f"**{check['name']}:**")
            for issue in check["issues"]:
                lines.append(f"- {issue}")
            lines.append("")

    warnings = [c for c in problems if c["status"] == "warning"]
    if warnings:
        lines.append("### ⚠️ تحذيرات | Warnings")
        lines.append("")
        for check in warnings:
            lines.append(f"**{check['name']}:**")
            for issue in check["issues"][:3]:  # أول 3 مشاكل فقط
                lines.append(f"- {issue}")
            if len(check["issues"]) > 3:
                lines.append(f"- ... و {len(check['issues']) - 3} مشاكل أخرى")
            lines.append("")

    if not problems:
        lines.append("✅ **لا توجد مشاكل مكتشفة هذا الأسبوع. الموقع في حالة ممتازة.**")
        lines.append("")

    # ============================================================
    # 3. التحسينات المقترحة (Suggested Improvements)
    # ============================================================
    lines.append("## 3. التحسينات المقترحة | Suggested Improvements")
    lines.append("")
    lines.append("> ⚠️ **مهم:** هذه اقتراحات فقط. لا يتم تطبيق أي تعديل بدون موافقة الأدمن.")
    lines.append("> **نظام الاقتراح:** Problem → Analysis → Recommendation → Admin Approval → Apply")
    lines.append("")

    pending_suggestions = [s for s in suggestions if s.get("approval_status") == "pending"]
    if pending_suggestions:
        lines.append(f"**عدد الاقتراحات المعلقة:** {len(pending_suggestions)}")
        lines.append("")
        for s in pending_suggestions[:15]:  # أول 15 اقتراح
            severity_emoji = "🔴" if s["severity"] == "critical" else "⚠️"
            lines.append(f"### {severity_emoji} {s['id']} — {s['check_name']}")
            lines.append("")
            lines.append(f"**المشكلة:** {s['problem']}")
            lines.append(f"**التحليل:** {s['analysis']}")
            lines.append(f"**التوصية:** {s['recommendation']}")
            lines.append(f"**ملاحظة الأمان:** {s['safety_note']}")
            lines.append(f"**الحالة:** 🟡 بانتظار موافقة الأدمن")
            lines.append("")
    else:
        lines.append("✅ **لا توجد اقتراحات معلقة. جميع الفحوصات سليمة.**")
        lines.append("")

    # ============================================================
    # 4. الكلمات الصاعدة (Rising Keywords)
    # ============================================================
    lines.append("## 4. الكلمات الصاعدة | Rising Keywords")
    lines.append("")

    kw_check = None
    for check in checks:
        if check["name"] == "Keyword Performance":
            kw_check = check
            break

    if kw_check:
        details = kw_check.get("details", {})
        coverage = details.get("coverage_percent", 0)
        trend = details.get("trend", "baseline")
        trend_emoji = {"improving": "📈 تتحسن", "declining": "📉 تتراجع", "stable": "➡️ مستقر", "baseline": "📊 خط أساس"}.get(trend, trend)

        lines.append(f"**تغطية الكلمات:** {coverage}%")
        lines.append(f"**الاتجاه:** {trend_emoji}")
        lines.append("")

        rising = details.get("rising_keywords", [])
        if rising:
            lines.append("### الكلمات الأكثر انتشاراً في الصفحات")
            lines.append("")
            lines.append("| الكلمة المفتاحية | عدد الصفحات |")
            lines.append("|---|---|")
            for kw, count in rising[:10]:
                lines.append(f"| {kw} | {count} |")
            lines.append("")
        else:
            lines.append("لا توجد بيانات كافية عن الكلمات الصاعدة هذا الأسبوع.")
            lines.append("")

        # توزيع الكلمات حسب النوع
        type_dist = details.get("type_distribution", {})
        if type_dist:
            lines.append("### توزيع الكلمات حسب النوع")
            lines.append("")
            lines.append("| النوع | العدد |")
            lines.append("|---|---|")
            for kw_type, count in sorted(type_dist.items()):
                lines.append(f"| {kw_type} | {count} |")
            lines.append("")
    else:
        lines.append("تعذر الحصول على بيانات أداء الكلمات المفتاحية.")
        lines.append("")

    # ============================================================
    # 5. الصفحات التي تحتاج تحديث (Pages Needing Updates)
    # ============================================================
    lines.append("## 5. الصفحات التي تحتاج تحديث | Pages Needing Updates")
    lines.append("")

    pages_needing_update = set()

    # صفحات بدون title
    for check in checks:
        if check["name"] == "Meta Tags Completeness":
            for issue in check.get("issues", []):
                # استخراج أسماء الصفحات من المشاكل
                pass

    # صفحات بمشاكل في الـ schema
    for check in checks:
        if check["name"] == "Schema Errors":
            for issue in check.get("issues", []):
                if "block#" in issue:
                    page = issue.split(":")[0].strip()
                    pages_needing_update.add(page)

    # صفحات بدون canonical
    for check in checks:
        if check["name"] == "Canonical Issues":
            for issue in check.get("issues", []):
                if "الصفحات:" in issue:
                    pages = issue.split("الصفحات:")[1].strip().rstrip(".")
                    for p in pages.split(","):
                        p = p.strip()
                        if p:
                            pages_needing_update.add(p)

    # صفحات كبيرة
    for check in checks:
        if check["name"] == "Page Speed":
            for issue in check.get("issues", []):
                if "KB" in issue and ":" in issue:
                    parts = issue.split(":")
                    if len(parts) >= 2:
                        page = parts[0].strip().lstrip("- ").strip()
                        if page.endswith(".html") or "/index.html" in page:
                            pages_needing_update.add(page)

    if pages_needing_update:
        lines.append("| الصفحة | السبب |")
        lines.append("|---|---|")
        for page in sorted(pages_needing_update):
            reasons = []
            for check in checks:
                for issue in check.get("issues", []):
                    if page in issue:
                        reasons.append(check["name"])
            reason_text = ", ".join(set(reasons)) if reasons else "مراجعة عامة"
            lines.append(f"| `{page}` | {reason_text} |")
        lines.append("")
    else:
        lines.append("✅ **جميع الصفحات في حالة جيدة ولا تحتاج تحديثات عاجلة.**")
        lines.append("")

    # ============================================================
    # 6. قواعد الحماية (Safety Rules)
    # ============================================================
    lines.append("## 6. قواعد الحماية | Safety Rules")
    lines.append("")
    lines.append("نظام المراقبة يلتزم بالقواعد التالية:")
    lines.append("")
    lines.append("- 🚫 **ممنوع حذف صفحات مفهرسة** — Indexed pages must not be deleted")
    lines.append("- 🚫 **ممنوع تغيير روابط بدون Redirect 301** — No link changes without 301 redirect")
    lines.append("- ✅ **لا تعديل مباشر** — No direct edits without admin approval")
    lines.append("- ✅ **نظام الاقتراح** — Problem → Analysis → Recommendation → Admin Approval → Apply")
    lines.append("- ✅ **الحفاظ على GitHub, Railway, Telegram, Webhook, Backup System**")
    lines.append("")

    # ============================================================
    # 7. التوصيات النهائية (Final Recommendations)
    # ============================================================
    lines.append("## 7. التوصيات النهائية | Final Recommendations")
    lines.append("")

    if overall >= 85:
        lines.append("🏆 **الموقع في حالة ممتازة.** حافظ على المراقبة الأسبوعية وطبّق التحسينات الطفيفة إن وجدت.")
    elif overall >= 70:
        lines.append("📊 **الموقع في حالة جيدة.** ركّز على إصلاح التحذيرات لرفع النتيجة إلى الممتاز.")
    elif overall >= 50:
        lines.append("⚠️ **الموقع يحتاج تحسينات.** ابدأ بالمشاكل الحرجة أولاً ثم انتقل للتحذيرات.")
    else:
        lines.append("🔴 **الموقع في حالة حرجة.** يجب إصلاح المشاكل الحرجة فوراً قبل أي تحسينات أخرى.")

    lines.append("")
    lines.append("### الخطوات التالية المقترحة:")
    lines.append("")
    lines.append("1. مراجعة الاقتراحات المعلقة في ملف `seo_suggestions.json`")
    lines.append("2. الموافقة على الاقتراحات المناسبة (Admin Approval)")
    lines.append("3. تطبيق الإصلاحات الموصى بها (Apply)")
    lines.append("4. إعادة الفحص بعد التطبيق للتأكد من التحسن")
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(f"*تم إنشاء هذا التقرير تلقائياً بواسطة نظام المراقبة الأسبوعي — Phase 6.2*")
    lines.append(f"*تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M')}*")
    lines.append("")

    return "\n".join(lines)


def _get_report_number():
    """الحصول على رقم التقرير التسلسلي."""
    history = _load_json(SEO_HISTORY_FILE, {"reports": [], "counter": 0})
    counter = history.get("counter", 0) + 1
    return counter


def save_report(report_text, checks, health_score):
    """حفظ التقرير في ملف وحفظ نسخة في التاريخ."""
    today = datetime.now().strftime("%Y-%m-%d")
    report_num = _get_report_number()

    # حفظ التقرير المؤرخ
    dated_filename = REPORTS_DIR / f"WEEKLY_SEO_REPORT_{today}_#{report_num}.md"
    with open(dated_filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    # حفظ نسخة بالاسم القياسي (يُحدث كل أسبوع)
    latest_filename = WEBSITE_DIR / "WEEKLY_SEO_REPORT.md"
    with open(latest_filename, "w", encoding="utf-8") as f:
        f.write(report_text)

    # حفظ في التاريخ
    history = _load_json(SEO_HISTORY_FILE, {"reports": [], "counter": 0})
    history["counter"] = report_num
    history["reports"].append({
        "number": report_num,
        "date": today,
        "health_score": health_score,
        "check_statuses": {c["name"]: c["status"] for c in checks},
        "check_scores": {c["name"]: c["score"] for c in checks},
        "report_file": str(dated_filename.name),
    })
    # الاحتفاظ بآخر 52 تقرير (سنة كاملة)
    if len(history["reports"]) > 52:
        history["reports"] = history["reports"][-52:]
    _save_json(SEO_HISTORY_FILE, history)

    return dated_filename, latest_filename


# ============================================================
# الفحص الشامل — الدالة الرئيسية
# ============================================================
def run_full_seo_audit():
    """
    تشغيل فحص SEO شامل وجمع جميع النتائج.
    هذه الدالة الرئيسية التي تُستدعى أسبوعياً.
    """
    logger.info("seo_monitor: بدء الفحص الشامل لـ SEO...")

    checks = []

    # ترتيب الفحوصات
    check_functions = [
        ("Indexing", check_sitemap),
        ("Indexing", check_robots_txt),
        ("Indexing", check_indexed_pages),
        ("Technical", check_crawl_errors),
        ("Technical", check_404_pages),
        ("Content", check_duplicate_content),
        ("Technical", check_canonical_issues),
        ("Technical", check_schema_errors),
        ("Technical", check_page_speed),
        ("Technical", check_mobile_seo),
        ("Keywords", check_keyword_performance),
        ("Content", check_meta_tags_completeness),
        ("Content", check_image_alt_tags),
        ("Content", check_heading_structure),
    ]

    for category, func in check_functions:
        try:
            logger.info(f"seo_monitor: تشغيل {func.__name__}...")
            result = func()
            checks.append(result)
        except Exception as e:
            logger.error(f"seo_monitor: خطأ في {func.__name__}: {e}")
            checks.append({
                "name": func.__name__.replace("check_", "").replace("_", " ").title(),
                "category": category,
                "status": "critical",
                "score": 0,
                "details": {},
                "issues": [f"خطأ في تشغيل الفحص: {e}"],
            })

    # حساب نقاط الصحة
    health_score = calculate_health_score(checks)
    logger.info(f"seo_monitor: Health Score = {health_score}")

    # توليد الاقتراحات
    suggestions = generate_suggestions(checks, health_score)
    save_suggestions(suggestions)
    logger.info(f"seo_monitor: تم توليد {len(suggestions)} اقتراح")

    # توليد التقرير
    report_text = generate_weekly_report(checks, health_score, suggestions)
    dated_file, latest_file = save_report(report_text, checks, health_score)
    logger.info(f"seo_monitor: تم حفظ التقرير في {dated_file}")

    return {
        "checks": checks,
        "health_score": health_score,
        "suggestions": suggestions,
        "report_text": report_text,
        "dated_report_file": str(dated_file),
        "latest_report_file": str(latest_file),
        "report_number": _get_report_number() - 1,
    }


def get_seo_summary_for_telegram(audit_result=None):
    """
    توليد ملخص مختصر للتقرير لإرساله عبر Telegram.
    إذا تم تمرير audit_result، يستخدمه بدلاً من تشغيل فحص جديد.
    """
    try:
        result = audit_result if audit_result is not None else run_full_seo_audit()
        h = result["health_score"]
        checks = result["checks"]

        # عدد المشاكل
        critical = sum(1 for c in checks if c["status"] == "critical")
        warnings = sum(1 for c in checks if c["status"] == "warning")
        ok = sum(1 for c in checks if c["status"] == "ok")

        # حالة الموقع
        overall = h.get("Overall", 0)
        if overall >= 85:
            status = "🟢 ممتاز"
        elif overall >= 70:
            status = "🟡 جيد"
        elif overall >= 50:
            status = "🟠 يحتاج تحسين"
        else:
            status = "🔴 حرج"

        msg = (
            f"📊 تقرير SEO الأسبوعي #{result['report_number']}\n"
            f"📅 {datetime.now().strftime('%Y-%m-%d')}\n"
            f"━━━━━━━━━━━━━━━━━━\n\n"
            f"🏥 الحالة العامة: {status} ({overall}%)\n\n"
            f"📈 نقاط صحة SEO:\n"
            f"   🔧 Technical: {h.get('Technical', 0)}%\n"
            f"   📝 Content: {h.get('Content', 0)}%\n"
            f"   🔍 Indexing: {h.get('Indexing', 0)}%\n"
            f"   🎯 Keywords: {h.get('Keywords', 0)}%\n\n"
            f"📋 ملخص الفحوصات:\n"
            f"   ✅ سليم: {ok}\n"
            f"   ⚠️ تحذير: {warnings}\n"
            f"   🔴 حرج: {critical}\n\n"
            f"💡 اقتراحات معلقة: {len(result['suggestions'])}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📄 التقرير الكامل: WEEKLY_SEO_REPORT.md\n"
            f"🔐 لا تعديلات بدون موافقة الأدمن\n"
            f"🚫 ممنوع حذف صفحات مفهرسة\n"
            f"🚫 ممنوع تغيير روابط بدون 301"
        )
        return msg
    except Exception as e:
        logger.error(f"seo_monitor: خطأ في توليد ملخص Telegram: {e}")
        return f"❌ خطأ في توليد تقرير SEO: {e}"


# ============================================================
# تشغيل مباشر للاختبار
# ============================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s — %(name)s — %(levelname)s — %(message)s")
    print("=" * 60)
    print("Phase 6.2 — Weekly SEO Intelligence System")
    print("تشغيل فحص SEO شامل...")
    print("=" * 60)
    result = run_full_seo_audit()
    print(f"\n{'=' * 60}")
    print(f"Health Score: {result['health_score']}")
    print(f"Checks: {len(result['checks'])}")
    print(f"Suggestions: {len(result['suggestions'])}")
    print(f"Report: {result['latest_report_file']}")
    print(f"{'=' * 60}")
    print("\n--- Telegram Summary ---")
    msg = get_seo_summary_for_telegram(result)
    print(msg)
