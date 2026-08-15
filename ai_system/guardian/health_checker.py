import os
import logging
from .monitor import SystemMonitor
from .error_detector import ErrorDetector
from .risk_analyzer import RiskAnalyzer

logger = logging.getLogger("afaq_guardian_health_checker")

class HealthChecker:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir
        self.monitor = SystemMonitor(root_dir)
        self.error_detector = ErrorDetector(root_dir)

    def run_full_health_check(self):
        report = {
            "status": "HEALTHY",
            "issues": []
        }

        # Check offers count
        offers_cnt = self.monitor.check_offers_count()
        if offers_cnt != 27:
            issue = {
                "type": "offers_count_drop" if offers_cnt < 27 else "offers_count_mismatch",
                "details": f"Offers count is {offers_cnt}, expected 27",
                "risk": RiskAnalyzer.analyze_issue("offers_count_drop", f"Count: {offers_cnt}")
            }
            report["status"] = "UNHEALTHY"
            report["issues"].append(issue)

        # Check syntax
        py_errs = self.error_detector.scan_python_syntax()
        if py_errs:
            report["status"] = "UNHEALTHY"
            report["issues"].append({
                "type": "syntax_error",
                "details": py_errs,
                "risk": RiskAnalyzer.analyze_issue("syntax_error", py_errs)
            })

        js_errs = self.error_detector.scan_js_syntax()
        if js_errs:
            report["status"] = "UNHEALTHY"
            report["issues"].append({
                "type": "syntax_error",
                "details": js_errs,
                "risk": RiskAnalyzer.analyze_issue("syntax_error", js_errs)
            })

        return report
