import os
import subprocess
import logging

logger = logging.getLogger("afaq_guardian_error_detector")

class ErrorDetector:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir

    def scan_python_syntax(self):
        errors = []
        py_files = ["bot/bot.py", "bot/normalizer.py", "bot/bounce_guard.py"]
        for py_file in py_files:
            path = os.path.join(self.root_dir, py_file)
            if os.path.exists(path):
                res = subprocess.run(["python3", "-m", "py_compile", path], capture_output=True, text=True)
                if res.returncode != 0:
                    errors.append({"file": py_file, "error": res.stderr})
        return errors

    def scan_js_syntax(self):
        errors = []
        js_files = ["js/main.js", "js/silo.js"]
        for js_file in js_files:
            path = os.path.join(self.root_dir, js_file)
            if os.path.exists(path):
                res = subprocess.run(["node", "--check", path], capture_output=True, text=True)
                if res.returncode != 0:
                    errors.append({"file": js_file, "error": res.stderr})
        return errors
