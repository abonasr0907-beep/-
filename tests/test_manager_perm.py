import sys
import json
from pathlib import Path

# Add repo root and bot directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
bot_dir = repo_root / "bot"
sys.path.insert(0, str(bot_dir))
sys.path.insert(0, str(repo_root))

from config import is_manager, is_owner, OWNER_ID, MANAGERS_PATH


def test_permanent_manager_permissions():
    # 1. OWNER_ID check
    assert is_owner(OWNER_ID) is True, f"OWNER_ID {OWNER_ID} must be owner"
    assert is_manager(OWNER_ID) is True, f"OWNER_ID {OWNER_ID} must be manager"

    # 2. Add test manager to data/managers.json
    test_manager_id = 999888777
    original_data = {}
    if MANAGERS_PATH.exists():
        with open(MANAGERS_PATH, "r", encoding="utf-8") as f:
            original_data = json.load(f)

    managers_list = list(original_data.get("managers", []))
    test_entry = {
        "id": str(test_manager_id),
        "telegram_id": str(test_manager_id),
        "role": "manager",
        "name": "تست مدير",
        "status": "active"
    }
    updated_list = [m for m in managers_list if str(m.get("id")) != str(test_manager_id)]
    updated_list.append(test_entry)

    with open(MANAGERS_PATH, "w", encoding="utf-8") as f:
        json.dump({"managers": updated_list}, f, ensure_ascii=False, indent=2)

    try:
        # First publish check
        res1 = is_manager(test_manager_id)
        assert res1 is True, f"First is_manager check failed for {test_manager_id}"

        # Second consecutive publish check (must NOT be consumed)
        res2 = is_manager(test_manager_id)
        assert res2 is True, f"Second consecutive is_manager check failed (consumed) for {test_manager_id}"

        print(f"✅ Test Passed: manager {test_manager_id} has permanent permissions for consecutive actions")

    finally:
        # Restore original data
        with open(MANAGERS_PATH, "w", encoding="utf-8") as f:
            json.dump(original_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    test_permanent_manager_permissions()
