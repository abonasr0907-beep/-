import sys
from pathlib import Path

# Add repo root and bot directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
bot_dir = repo_root / "bot"
sys.path.insert(0, str(bot_dir))
sys.path.insert(0, str(repo_root))

from regression_guardian import run_regression_guardian


def test_regression_guardian_passes():
    report = run_regression_guardian()
    assert report["status"] == "PASSED", f"Regression Guardian failed: {report.get('failures')}"
    print(f"✅ Test Passed: Regression Guardian report status is {report['status']}")


if __name__ == "__main__":
    test_regression_guardian_passes()
