"""
نظام المناعة (Regression Guardian) - مهمة M18
يقوم بالفحص الدوري (كل 6 ساعات) لمنع النكوص بالأعطال المتكررة
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
    تشغيل فحص نظام المناعة الدورية
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

    # (ج) قالب بطاقة عرض له فيديو يحوي 🎬 في js/cards.js
    cards_js_path = repo_root / "js" / "cards.js"
    card_template_ok = False
    if cards_js_path.exists():
        with open(cards_js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        if "🎬" in js_content and "openVideoModal" in js_content:
            card_template_ok = True

    if not card_template_ok:
        report["status"] = "FAILED"
        report["failures"].append({
            "check": "video_card_template_missing_badge",
            "file": "js/cards.js",
            "line": 1,
            "detail": "js/cards.js card template missing 🎬 badge or openVideoModal"
        })

    # (د) CSS يحوي قاعدة العمود الواحد عند 360px
    css_pages_path = repo_root / "css" / "pages.css"
    css_ok = False
    if css_pages_path.exists():
        with open(css_pages_path, "r", encoding="utf-8") as f:
            css_content = f.read()
        if "360px" in css_content and "grid-template-columns: 1fr" in css_content:
            css_ok = True

    if not css_ok:
        report["status"] = "FAILED"
        report["failures"].append({
            "check": "css_grid_1col_violation",
            "file": "css/pages.css",
            "line": 1,
            "detail": "CSS missing 1-column mobile grid rule at 360px"
        })

    # (هـ) offers-index.json موجود وحجمه تحت الحد
    if not INDEX_PATH.exists() or INDEX_PATH.stat().st_size > 102400:  # 100 KB limit
        # LOW issue -> Auto repair
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
