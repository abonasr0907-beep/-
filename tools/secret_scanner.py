#!/usr/bin/env python3
"""
حارس الأسرار الدوري - Secret Scanner (M22-CORE)
يفحص مستودع الكود بشكل دوري للبحث عن المفاتيح والتوكنات المكتوبة بشكل صريح.
يرسل تنبيهاً فورياً للمالك عند اكتشاف أي سر حساس.
"""

import os
import re
import sys
import json
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OWNER_ID = "7746757675"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# أنماط الأسرار الحساسة
PATTERNS = {
    "Telegram Bot Token": r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b",
    "GitHub Token": r"\b(ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{82})\b",
    "AWS Access Key": r"\bAKIA[0-9A-Z]{16}\b",
    "Generic Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----"
}

# المجلدات المقتطعة من الفحص
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".pytest_cache", "archive"}
EXCLUDE_FILES = {"secret_scanner.py"}


def send_owner_alert(matches: list):
    """إرسال تنبيه خفي وعاجل لمحادثة المالك فقط"""
    if not matches or not BOT_TOKEN:
        return

    text = "🚨 *حارس الأسرار: تنبيه أمني عاجل!*\n\n"
    text += "تم اكتشاف أنماط أسرار أو توكنات مكشوفة داخل مستودع الكود:\n\n"
    for m in matches[:5]:
        text += f"• *الملف:* `{m['file']}`\n  *النوع:* {m['pattern_name']}\n  *السطر:* {m['line']}\n\n"

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": OWNER_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        print(f"⚠️ فشل إرسال تنبيه حارس الأسرار: {e}")


def scan_repo() -> list:
    """فحص جميع الملفات في المستودع"""
    findings = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file in EXCLUDE_FILES or file.endswith((".png", ".jpg", ".jpeg", ".webp", ".pdf", ".zip", ".pyc")):
                continue
            filepath = Path(root) / file
            rel_path = filepath.relative_to(REPO_ROOT)
            try:
                with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                    for line_num, line in enumerate(f, 1):
                        for name, pattern in PATTERNS.items():
                            if re.search(pattern, line):
                                findings.append({
                                    "file": str(rel_path),
                                    "line": line_num,
                                    "pattern_name": name
                                })
            except Exception:
                pass
    return findings


if __name__ == "__main__":
    findings = scan_repo()
    if findings:
        print(f"🚨 Secret Scanner found {len(findings)} potential leaks!")
        for f in findings:
            print(f"  [{f['pattern_name']}] {f['file']}:{f['line']}")
        send_owner_alert(findings)
        sys.exit(1)
    else:
        print("✅ Secret Scanner clean! No exposed tokens found.")
        sys.exit(0)
