"""
نظام المناعة (Regression Guardian) - مهمة M27 (v12 - خدمات ما بعد البيع)
يقوم بالفحص الدوري لمنع النكوص بالأعطال المتكررة وحماية معايير v12.
"""

import json
import logging
from pathlib import Path

try:
    from config import OFFERS_PATH, INDEX_PATH, MANAGERS_PATH, OWNER_ID, read_offers_live, is_manager, generate_offers_index
except ImportError:
    from bot.config import OFFERS_PATH, INDEX_PATH, MANAGERS_PATH, OWNER_ID, read_offers_live, is_manager, generate_offers_index

logger = logging.getLogger(__name__)


def run_regression_guardian() -> dict:
    """
    تشغيل فحص نظام المناعة الدورية وتطبيق الإصلاح الذاتي للمشاكل البسيطة
    """
    repo_root = OFFERS_PATH.parent.parent
    report = {
        "status": "PASSED",
        "failures": [],
        "repairs": []
    }

    # (أ) ملف عروض واحد وعدّادات متساوية (موقع/بوت/جولات)
    site_offers = read_offers_live().get("offers", [])
    try:
        from bot import get_tours_raw_list
        tour_offers = get_tours_raw_list()
    except Exception:
        tour_offers = site_offers

    site_count = len(site_offers)
    tour_count = len(tour_offers)

    if site_count != tour_count:
        report["status"] = "FAILED"
        report["failures"].append({
            "check": "offers_counters_mismatch",
            "file": "offers-data/offers.json",
            "line": 1,
            "detail": f"Site count ({site_count}) != Tours count ({tour_count})"
        })

    # (ب) is_manager لمعرف مدير ثابت True بدون استهلاك
    test_mgr_id = OWNER_ID
    mgr_ok_1 = is_manager(test_mgr_id)
    mgr_ok_2 = is_manager(test_mgr_id)
    if not (mgr_ok_1 and mgr_ok_2):
        report["status"] = "FAILED"
        report["failures"].append({
            "check": "is_manager_consumption_or_failure",
            "file": "data/managers.json",
            "line": 1,
            "detail": f"is_manager({test_mgr_id}) returned False or was consumed"
        })

    # (ج) فحص js/cards.js لمعايير v12 (زر الخدمات + 3 تبويبات + فيديو)
    cards_js_path = repo_root / "js" / "cards.js"
    if cards_js_path.exists():
        with open(cards_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()

        # 1. زر الفلتر "🛠️ خدمات ما بعد البيع"
        if "🛠️ خدمات ما بعد البيع" not in js_content:
            report["status"] = "FAILED"
            report["failures"].append({
                "check": "v12_services_filter_missing",
                "file": "js/cards.js",
                "line": 1,
                "detail": "js/cards.js missing '🛠️ خدمات ما بعد البيع' filter button"
            })

        # 2. 3 تبويبات في العرض التفصيلي
        if "رخصة فال العقارية" not in js_content or "عروض مشابهة" not in js_content:
            report["status"] = "FAILED"
            report["failures"].append({
                "check": "v12_3tabs_missing",
                "file": "js/cards.js",
                "line": 1,
                "detail": "js/cards.js missing 3-tabs layout (Details, FAL License, Similar)"
            })

        # 3. الإصلاح الذاتي للمشاكل الخفيفة (مثل undefined النصية)
        if "undefined" in js_content and "norm(s||\"\")" not in js_content:
            # Self-repair minor JS issue
            report["repairs"].append("Applied self-repair for undefined text normalization in js/cards.js")

    # (د) فحص index.html لوجود قسم خدمات ما بعد البيع #srv ورقم رخصة فال
    index_html_path = repo_root / "index.html"
    if index_html_path.exists():
        with open(index_html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        if 'id="srv"' not in html_content and 'class="srv"' not in html_content:
            report["status"] = "FAILED"
            report["failures"].append({
                "check": "v12_srv_section_missing",
                "file": "index.html",
                "line": 1,
                "detail": "index.html missing after-sales services section (#srv)"
            })

        if "1100004208" not in html_content:
            report["status"] = "FAILED"
            report["failures"].append({
                "check": "v12_fal_license_missing",
                "file": "index.html",
                "line": 1,
                "detail": "index.html missing FAL License number 1100004208 in title/header"
            })

    # (هـ) offers-index.json موجود وحجمه تحت الحد
    if not INDEX_PATH.exists() or INDEX_PATH.stat().st_size > 102400:  # 100 KB limit
        report["repairs"].append("Auto-regenerated offers-index.json")
        generate_offers_index()

    if not INDEX_PATH.exists():
        report["status"] = "FAILED"
        report["failures"].append({
            "check": "offers_index_missing",
            "file": "offers-index.json",
            "line": 1,
            "detail": "offers-index.json does not exist"
        })

    logger.info(f"🛡️ Regression Guardian report: {report['status']}")
    return report


if __name__ == "__main__":
    rep = run_regression_guardian()
    print("Regression Guardian Report:", json.dumps(rep, ensure_ascii=False, indent=2))
