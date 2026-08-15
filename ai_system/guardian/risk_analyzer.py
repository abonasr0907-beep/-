import logging

logger = logging.getLogger("afaq_guardian_risk_analyzer")

class RiskAnalyzer:
    @staticmethod
    def analyze_issue(issue_type, details):
        if issue_type == "offers_count_drop":
            return {"severity": "HIGH", "recommendation": "Revert to last stable tag or backup."}
        elif issue_type == "bot_secrecy_leak":
            return {"severity": "LOW", "recommendation": "Auto fix public HTML/JS files immediately."}
        elif issue_type == "syntax_error":
            return {"severity": "HIGH", "recommendation": "Create fix branch, test, and merge/revert."}
        else:
            return {"severity": "MEDIUM", "recommendation": "Investigate and log issue."}
