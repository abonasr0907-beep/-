import subprocess
import logging

logger = logging.getLogger("afaq_guardian_repair_engine")

class RepairEngine:
    def __init__(self, root_dir="."):
        self.root_dir = root_dir

    def create_fix_branch(self, branch_name):
        try:
            subprocess.run(["git", "checkout", "-b", branch_name], check=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create fix branch {branch_name}: {e}")
            return False

    def test_and_merge(self, branch_name):
        try:
            # Run test
            res = subprocess.run(["python3", "-m", "py_compile", "bot/bot.py"], capture_output=True)
            if res.returncode != 0:
                subprocess.run(["git", "checkout", "main"], check=False)
                subprocess.run(["git", "branch", "-D", branch_name], check=False)
                return False, "Test failed on fix branch"

            subprocess.run(["git", "checkout", "main"], check=True)
            subprocess.run(["git", "merge", "--no-ff", branch_name], check=True)
            subprocess.run(["git", "branch", "-d", branch_name], check=False)
            return True, "Merged successfully"
        except Exception as e:
            logger.error(f"Merge error: {e}")
            return False, str(e)
