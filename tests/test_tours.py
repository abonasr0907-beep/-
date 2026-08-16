import sys
from pathlib import Path

# Add repo root and bot directory to sys.path
repo_root = Path(__file__).resolve().parent.parent
bot_dir = repo_root / "bot"
sys.path.insert(0, str(bot_dir))
sys.path.insert(0, str(repo_root))

from config import read_offers_live
from bot import get_tours_raw_list


def test_tours_list_length_equals_offers_count():
    offers_data = read_offers_live()
    raw_offers = offers_data.get("offers", [])
    tours = get_tours_raw_list()
    assert len(tours) == len(raw_offers), f"Tours count {len(tours)} != offers count {len(raw_offers)}"
    print(f"✅ Test Passed: tours list length ({len(tours)}) == offers count ({len(raw_offers)})")


if __name__ == "__main__":
    test_tours_list_length_equals_offers_count()
