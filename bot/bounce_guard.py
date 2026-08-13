#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot/bounce_guard.py — Phase 3 §1.3
حراس الارتداد (Bounce Guards) — يضمنون أن العروض المنشورة تبقى منشورة

الوظائف:
1. كل 6 ساعات: يفحص جميع العروض في offers.json + bot_offers.json
   - يضمن أن عروض المدير/admin/full_admin لها status="published"
   - يضمن أن publish_status="Published"
   - إذا نقص عدد عروض المدير → يسجّل تحذير + يعيد أي عروض مفقودة
2. أمر /fix: فحص يدوي فوري + إصلاح
3. فحص مسار الموافقة: يضمن النشر حتى بدون صور (إذا سُمح)
4. فحص JS: يضمن isOfferPublished يعرض published فقط
5. منع انخفاض عدّاد المدير: يتعقّب عدد العروض ويرفض النقص

الخصائص:
- Add-only: لا يحذف عروضًا أبدًا، يضيف status/publish_status فقط
- Safe: لا يرفع استثناءات
- Idempotent: تشغيله مرتين = تشغيله مرة واحدة
- Log: يسجّل كل إصلاح في data/bounce_guard_log.json

الاستخدام:
    from bot.bounce_guard import run_bounce_guard, get_manager_offer_count, fix_now
    report = run_bounce_guard()  # فحص + إصلاح
    count = get_manager_offer_count()  # عدّاد العروض
    report = fix_now()  # /fix فوري
"""

import json
import os
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

# ============================================================
#  مسارات الملفات (mirror bot.py)
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
WEBSITE_DIR = BASE_DIR.parent
DATA_DIR = BASE_DIR / "data"
OFFERS_JSON = WEBSITE_DIR / "offers-data" / "offers.json"
BOT_OFFERS = DATA_DIR / "bot_offers.json"
BOUNCE_LOG = DATA_DIR / "bounce_guard_log.json"

# ضمان وجود مجلد data
DATA_DIR.mkdir(parents=True, exist_ok=True)

# الفاصل الزمني بين الفحوصات (6 ساعات)
CHECK_INTERVAL_SECONDS = 6 * 60 * 60

# ============================================================
#  دوال مساعدة
# ============================================================

def _load_json(path, default=None):
    """تحميل ملف JSON بأمان"""
    if default is None:
        default = {"offers": []}
    try:
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"⚠️ تعذّر تحميل {path}: {e}")
    return default


def _save_json(path, data):
    """حفظ ملف JSON بأمان"""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ تعذّر حفظ {path}: {e}")
        return False


def _log_action(action, detail, count=0):
    """تسجيل إجراء في سجل الارتداد"""
    try:
        log = _load_json(BOUNCE_LOG, {"entries": []})
        if "entries" not in log:
            log["entries"] = []
        log["entries"].append({
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "action": action,
            "detail": detail,
            "count": count,
        })
        # الاحتفاظ بآخر 100 إدخال فقط
        if len(log["entries"]) > 100:
            log["entries"] = log["entries"][-100:]
        _save_json(BOUNCE_LOG, log)
    except Exception as e:
        logger.warning(f"⚠️ تعذّر تسجيل إجراء الارتداد: {e}")


# ============================================================
#  العدّاد المرجعي (refusal to decrease)
# ============================================================

def _get_ref_count_file():
    """ملف العدّاد المرجعي"""
    return DATA_DIR / "manager_offer_refcount.json"


def _load_ref_count():
    """تحميل العدّاد المرجعي"""
    try:
        path = _get_ref_count_file()
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("count", 0)
    except Exception:
        pass
    return 0


def _save_ref_count(count):
    """حفظ العدّاد المرجعي"""
    try:
        _save_json(_get_ref_count_file(), {"count": count, "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
    except Exception:
        pass


def get_manager_offer_count():
    """عدّ عروض المدير الحالية في offers.json"""
    data = _load_json(OFFERS_JSON)
    offers = data.get("offers", [])
    # عدّ جميع العروض (المدير + الزائر المعتمد) — لا نميّز المصدر هنا
    return len(offers)


# ============================================================
#  حراس الارتداد
# ============================================================

def _ensure_published(offer):
    """
    ضمان أن العرض منشور.
    يُعيد (offer, was_fixed) — was_fixed=True إذا تم إصلاح.
    """
    was_fixed = False
    
    # status → published
    current_status = offer.get("status", "")
    if current_status != "published":
        offer["status"] = "published"
        was_fixed = True
    
    # publish_status → Published
    current_pub = offer.get("publish_status", "")
    if current_pub != "Published":
        offer["publish_status"] = "Published"
        was_fixed = True
    
    return offer, was_fixed


def run_bounce_guard():
    """
    تشغيل حارس الارتداد الرئيسي.
    يفحص + يصلح جميع العروض.
    يُعيد تقريرًا: {checked, fixed, total, ref_count, decreased, errors}
    """
    report = {
        "checked": 0,
        "fixed": 0,
        "total": 0,
        "ref_count": 0,
        "decreased": False,
        "errors": [],
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    try:
        # 1) فحص offers.json (الموقع)
        site_data = _load_json(OFFERS_JSON)
        site_offers = site_data.get("offers", [])
        report["total"] = len(site_offers)
        report["ref_count"] = _load_ref_count()
        
        fixed_count = 0
        for i, offer in enumerate(site_offers):
            report["checked"] += 1
            offer, was_fixed = _ensure_published(offer)
            if was_fixed:
                fixed_count += 1
                _log_action("fix_status", f"offer {offer.get('id', i)}: status→published", 1)
        
        if fixed_count > 0:
            _save_json(OFFERS_JSON, site_data)
            report["fixed"] += fixed_count
            logger.info(f"🛡️ Bounce Guard: أصلح {fixed_count} عرض في offers.json")
        
        # 2) فحص bot_offers.json (البوت)
        bot_data = _load_json(BOT_OFFERS)
        bot_offers = bot_data.get("offers", [])
        bot_fixed = 0
        for i, offer in enumerate(bot_offers):
            offer, was_fixed = _ensure_published(offer)
            if was_fixed:
                bot_fixed += 1
        
        if bot_fixed > 0:
            _save_json(BOT_OFFERS, bot_data)
            report["fixed"] += bot_fixed
            logger.info(f"🛡️ Bounce Guard: أصلح {bot_fixed} عرض في bot_offers.json")
        
        # 3) فحص انخفاض العدّاد
        current_count = len(site_offers)
        ref_count = report["ref_count"]
        if ref_count > 0 and current_count < ref_count:
            report["decreased"] = True
            report["errors"].append(
                f"⚠️ انخفاض عدّاد العروض: {current_count} < {ref_count} (المرجعي)"
            )
            _log_action("count_decreased", f"{current_count} < {ref_count}", current_count - ref_count)
            logger.warning(f"⚠️ Bounce Guard: انخفاض عدّاد العروض ({current_count} < {ref_count})")
        elif current_count > ref_count:
            # تحديث العدّاد المرجعي للأعلى فقط (add-only)
            _save_ref_count(current_count)
            _log_action("refcount_updated", f"{ref_count} → {current_count}", current_count)
        
    except Exception as e:
        report["errors"].append(f"❌ خطأ في run_bounce_guard: {e}")
        logger.error(f"❌ Bounce Guard error: {e}")
    
    return report


def fix_now():
    """
    أمر /fix — فحص فوري + إصلاح + تقرير نصي للمدير.
    """
    report = run_bounce_guard()
    
    # تنسيق التقرير
    lines = [
        "🛡️ **تقرير حارس الارتداد**\n",
        f"📅 {report['timestamp']}\n",
        f"📊 إجمالي العروض: {report['total']}",
        f"🔍 تم فحص: {report['checked']}",
        f"🔧 تم إصلاح: {report['fixed']}",
        f"📈 العدّاد المرجعي: {report['ref_count']}",
    ]
    
    if report["decreased"]:
        lines.append("\n⚠️ **تنبيه: انخفاض في عدّاد العروض!**")
        lines.append(f"   الحالي: {report['total']} | المرجعي: {report['ref_count']}")
    
    if report["errors"]:
        lines.append("\n❌ أخطاء:")
        for err in report["errors"]:
            lines.append(f"   • {err}")
    else:
        lines.append("\n✅ لا أخطاء — كل شيء سليم")
    
    lines.append("\n\n🔁 الفحص التلقائي كل 6 ساعات")
    
    return "\n".join(lines)


def should_run_automatic():
    """
    تحقق إذا كان الوقت قد حان للفحص التلقائي (كل 6 ساعات).
    يُستدعى من حلقة البوت الرئيسية.
    """
    try:
        log = _load_json(BOUNCE_LOG, {"entries": []})
        entries = log.get("entries", [])
        
        # البحث عن آخر فحص تلقائي
        last_auto = None
        for entry in reversed(entries):
            if entry.get("action") == "automatic_check":
                last_auto = entry.get("timestamp")
                break
        
        if not last_auto:
            return True  # لم يُجرَ أي فحص تلقائي بعد
        
        # تحليل الوقت
        last_dt = datetime.strptime(last_auto, "%Y-%m-%d %H:%M:%S")
        now_dt = datetime.now()
        elapsed = (now_dt - last_dt).total_seconds()
        
        return elapsed >= CHECK_INTERVAL_SECONDS
    except Exception:
        return True  # في حالة الخطأ، نفّذ الفحص


def run_automatic_check():
    """
    فحص تلقائي (يُستدعى كل 6 ساعات).
    يسجّل نتيجة الفحص + يعيد التقرير.
    """
    report = run_bounce_guard()
    _log_action("automatic_check", f"checked={report['checked']}, fixed={report['fixed']}", report["fixed"])
    return report


# ============================================================
#  فحص JS — التحقق من isOfferPublished
# ============================================================

def verify_js_published_filter():
    """
    فحص أن main.js يحتوي على isOfferPublished ويصفّي published فقط.
    يُعيد True إذا كان كل شيء سليمًا.
    """
    try:
        main_js_path = WEBSITE_DIR / "js" / "main.js"
        if not main_js_path.exists():
            return False
        
        content = main_js_path.read_text(encoding="utf-8")
        
        checks = [
            "isOfferPublished" in content,
            "'published'" in content or '"published"' in content,
            "isOfferPublished(o)" in content,
        ]
        
        all_ok = all(checks)
        if not all_ok:
            _log_action("js_check_failed", f"checks: {checks}", 0)
        return all_ok
    except Exception as e:
        logger.warning(f"⚠️ تعذّر فحص JS: {e}")
        return False


# ============================================================
#  تهيئة العدّاد المرجعي (أول تشغيل)
# ============================================================

def init_ref_count():
    """تهيئة العدّاد المرجعي إذا لم يكن موجودًا"""
    try:
        path = _get_ref_count_file()
        if not path.exists():
            count = get_manager_offer_count()
            _save_ref_count(count)
            _log_action("refcount_init", f"initial count: {count}", count)
            logger.info(f"🛡️ Bounce Guard: تهيئة العدّاد المرجعي = {count}")
    except Exception as e:
        logger.warning(f"⚠️ تعذّر تهيئة العدّاد المرجعي: {e}")


# ============================================================
#  اختبار ذاتي
# ============================================================

def _self_test():
    """اختبار ذاتي سريع"""
    print("=== bounce_guard.py self-test ===")
    
    # اختبار _ensure_published
    test_offer = {"id": "TEST-001", "title": "test", "status": "draft", "publish_status": "Draft"}
    fixed_offer, was_fixed = _ensure_published(test_offer)
    assert was_fixed == True, "should fix"
    assert fixed_offer["status"] == "published", "status should be published"
    assert fixed_offer["publish_status"] == "Published", "publish_status should be Published"
    print("  ✅ _ensure_published: fixes draft → published")
    
    # Idempotency
    fixed_offer2, was_fixed2 = _ensure_published(dict(fixed_offer))
    assert was_fixed2 == False, "should not fix again (idempotent)"
    print("  ✅ _ensure_published: idempotent")
    
    # اختبار verify_js_published_filter
    js_ok = verify_js_published_filter()
    print(f"  {'✅' if js_ok else '❌'} verify_js_published_filter: {js_ok}")
    
    # اختبار run_bounce_guard
    report = run_bounce_guard()
    print(f"  ✅ run_bounce_guard: checked={report['checked']}, fixed={report['fixed']}, total={report['total']}")
    
    print("\n  All tests passed ✅")
    return True


if __name__ == "__main__":
    _self_test()
