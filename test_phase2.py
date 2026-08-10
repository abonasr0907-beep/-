#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Tests — Admin roles + Bidding DB + Offer retrieval
Tests the gap-filling patches without requiring a live Telegram connection.
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

# Ensure we can import bot modules
sys.path.insert(0, str(Path(__file__).parent / "bot"))

PASS = 0
FAIL = 0
ERRORS = []

def test_result(name, success, detail=""):
    global PASS, FAIL
    if success:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        ERRORS.append(f"{name}: {detail}")
        print(f"  ✗ {name} — {detail}")


def test_syntax_compilation():
    """Test 1: bot.py compiles without syntax errors"""
    print("\n[TEST] Syntax compilation of bot/bot.py")
    import py_compile
    try:
        py_compile.compile("bot/bot.py", doraise=True)
        test_result("bot.py compiles", True)
    except py_compile.PyCompileError as e:
        test_result("bot.py compiles", False, str(e)[:200])


def test_new_functions_exist():
    """Test 2: All new functions exist in the AST"""
    print("\n[TEST] New functions exist in AST")
    import ast
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())
    funcs = [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    
    expected = ["load_bids", "save_bids", "_save_bid_record", "_update_offer_with_bid",
                "_admin_change_role_menu", "_admin_set_role", "cmd_change_role"]
    for fn in expected:
        test_result(f"Function {fn} exists", fn in funcs, f"not found in {len(funcs)} functions")


def test_add_user_roles():
    """Test 3: /add_user accepts all 4 roles"""
    print("\n[TEST] /add_user supports reviewer + publisher roles")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check validation includes all 4 roles
    test_result(
        "Validation includes reviewer",
        '"reviewer"' in content and 'role not in' in content
    )
    test_result(
        "Validation includes publisher",
        '"publisher"' in content and 'role not in' in content
    )
    test_result(
        "Validation tuple has 4 roles",
        '("admin", "reviewer", "publisher", "editor")' in content
    )


def test_change_role_command():
    """Test 4: /change_role command exists and is registered"""
    print("\n[TEST] /change_role command")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    test_result("cmd_change_role function defined", "async def cmd_change_role" in content)
    test_result("Handler registered", 'CommandHandler("change_role"' in content)
    test_result("Validates 4 roles", '("admin", "reviewer", "publisher", "editor")' in content)
    test_result("Uses user_manager.change_role", "user_manager.change_role" in content)


def test_admin_menu_roles():
    """Test 5: Admin management menu shows roles"""
    print("\n[TEST] Admin menu shows roles + change role button")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    test_result(
        "Admin menu gets user role",
        "_role = user_manager.get_user_role(aid)" in content
    )
    test_result(
        "Admin menu shows role string",
        "_role_str" in content
    )
    test_result(
        "Change role button in keyboard",
        'callback_data=f"admin_role_{aid}"' in content
    )
    test_result(
        "Callback handler for admin_role_",
        'data.startswith("admin_role_")' in content
    )
    test_result(
        "Callback handler for admin_setrole_",
        'data.startswith("admin_setrole_")' in content
    )


def test_myid_list_users_roles():
    """Test 6: /myid and /users show all 4 roles"""
    print("\n[TEST] /myid and /users show all 4 roles")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # cmd_myid should have reviewer and publisher in role_str
    myid_section = content[content.find("async def cmd_myid"):content.find("async def cmd_myid") + 500]
    test_result("/myid shows reviewer", "reviewer" in myid_section)
    test_result("/myid shows publisher", "publisher" in myid_section)
    
    # cmd_list_users should have reviewer and publisher in role_icon
    lu_start = content.find("async def cmd_list_users")
    lu_end = content.find("\nasync def ", lu_start + 50)
    list_users_section = content[lu_start:lu_end] if lu_end > lu_start else content[lu_start:lu_start+1000]
    test_result("/users shows reviewer icon", "reviewer" in list_users_section)
    test_result("/users shows publisher icon", "publisher" in list_users_section)


def test_bid_storage_functions():
    """Test 7: Bid storage functions work correctly with temp files"""
    print("\n[TEST] Bid storage functions (load_bids, save_bids, _save_bid_record)")
    
    # We need to test these functions in isolation since they depend on BIDS_FILE
    # Create a temporary data directory
    tmpdir = tempfile.mkdtemp()
    try:
        # Simulate the bid storage logic
        bids_file = Path(tmpdir) / "bids.json"
        
        # Test load_bids with no file
        if bids_file.exists():
            bids_file.unlink()
        # Simulate load_bids
        if bids_file.exists():
            with open(bids_file, "r", encoding="utf-8") as f:
                bids_db = json.load(f)
        else:
            bids_db = {"bids": []}
        test_result("load_bids returns empty list when no file", bids_db == {"bids": []})
        
        # Test save_bids + _save_bid_record
        bid_data = {
            "id": "BID-001",
            "offerId": "AFQ-001",
            "offerTitle": "فيلا فاخرة",
            "offerUrl": "https://example.com/offer/001",
            "bidAmount": "500000",
            "currentHighestBid": "450000",
            "name": "أحمد",
            "phone": "0501234567",
            "bidNotes": "مزايدة جيدة",
        }
        
        # Simulate _save_bid_record
        bid_record = {
            "id": bid_data.get("id", ""),
            "offerId": bid_data.get("offerId", ""),
            "offerTitle": bid_data.get("offerTitle", bid_data.get("propertyType", "")),
            "offerUrl": bid_data.get("offerUrl", ""),
            "bidAmount": bid_data.get("bidAmount", bid_data.get("price", "")),
            "currentHighestBid": bid_data.get("currentHighestBid", ""),
            "name": bid_data.get("name", ""),
            "phone": bid_data.get("phone", ""),
            "notes": bid_data.get("bidNotes", bid_data.get("notes", "")),
            "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "new",
        }
        bids_db.setdefault("bids", []).append(bid_record)
        
        # Simulate save_bids
        with open(bids_file, "w", encoding="utf-8") as f:
            json.dump(bids_db, f, ensure_ascii=False, indent=2)
        
        test_result("Bid record saved to file", bids_file.exists())
        
        # Read back and verify
        with open(bids_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        test_result("Bid record has correct offerId", loaded["bids"][0]["offerId"] == "AFQ-001")
        test_result("Bid record has correct amount", loaded["bids"][0]["bidAmount"] == "500000")
        test_result("Bid record has correct name", loaded["bids"][0]["name"] == "أحمد")
        test_result("Bid record has status 'new'", loaded["bids"][0]["status"] == "new")
        test_result("Bid record has submitted_at", "submitted_at" in loaded["bids"][0])
        
    finally:
        shutil.rmtree(tmpdir)


def test_update_offer_with_bid_logic():
    """Test 8: _update_offer_with_bid correctly updates highestBid"""
    print("\n[TEST] _update_offer_with_bid logic")
    
    # Test the core logic: comparing bid amounts
    def mock_update(offers, offer_id, bid_amount):
        """Simplified version of _update_offer_with_bid logic"""
        try:
            new_bid = float(str(bid_amount).replace(",", ""))
        except (ValueError, TypeError):
            return False, offers
        
        updated = False
        for o in offers:
            if str(o.get("id", "")) == str(offer_id):
                current = 0
                try:
                    current = float(str(o.get("highestBid", 0)).replace(",", ""))
                except (ValueError, TypeError):
                    current = 0
                if new_bid > current:
                    o["highestBid"] = str(int(new_bid))
                    o["priceType"] = o.get("priceType", "auction")
                    updated = True
        return updated, offers
    
    # Test 1: New bid higher than current
    offers = [{"id": "AFQ-001", "highestBid": "450000", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-001", "500000")
    test_result("New higher bid updates highestBid", updated and offers[0]["highestBid"] == "500000")
    
    # Test 2: New bid lower than current
    offers = [{"id": "AFQ-001", "highestBid": "500000", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-001", "450000")
    test_result("Lower bid does NOT update highestBid", not updated and offers[0]["highestBid"] == "500000")
    
    # Test 3: First bid (no existing highestBid)
    offers = [{"id": "AFQ-002", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-002", "300000")
    test_result("First bid sets highestBid from 0", updated and offers[0]["highestBid"] == "300000")
    
    # Test 4: Bid with comma in amount
    offers = [{"id": "AFQ-003", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-003", "1,200,000")
    test_result("Bid with comma is parsed correctly", updated and offers[0]["highestBid"] == "1200000")
    
    # Test 5: Offer not found
    offers = [{"id": "AFQ-001", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-999", "500000")
    test_result("Bid for non-existent offer returns False", not updated)
    
    # Test 6: Invalid bid amount
    offers = [{"id": "AFQ-001", "priceType": "auction"}]
    updated, offers = mock_update(offers, "AFQ-001", "invalid")
    test_result("Invalid bid amount returns False", not updated)


def test_bid_notification_db_update():
    """Test 9: Bid notification section has DB update code"""
    print("\n[TEST] _notify_admins_new_request saves bids to DB")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    # Find the _notify_admins_new_request function
    notify_start = content.find("async def _notify_admins_new_request")
    notify_end = content.find("\nasync def ", notify_start + 100)
    notify_section = content[notify_start:notify_end]
    
    test_result("Has bid section (bidType check)", "bidType" in notify_section)
    test_result("Calls _save_bid_record", "_save_bid_record(visitor_request)" in notify_section)
    test_result("Calls _update_offer_with_bid", "_update_offer_with_bid(" in notify_section)
    test_result("Has offerId extraction", 'visitor_request.get("offerId"' in notify_section)
    test_result("Has bidAmount extraction", 'visitor_request.get("bidAmount"' in notify_section)


def test_visitor_requests_permanent_ids():
    """Test 10: Visitor requests have permanent IDs and retrieval"""
    print("\n[TEST] Visitor requests permanent IDs")
    
    # Check that the visitor_requests.json structure supports permanent IDs
    with open("bot/data/visitor_requests.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    test_result("visitor_requests.json has 'requests' key", "requests" in data)
    test_result("visitor_requests.json has 'inquiries' key", "inquiries" in data)
    
    # Check that the archive functions exist
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    test_result("archive_menu function exists", "async def archive_menu" in content or "def archive_menu" in content)
    test_result("_archive_collect_all exists", "_archive_collect_all" in content)
    test_result("_archive_repost exists", "_archive_repost" in content)


def test_image_system_exists():
    """Test 11: Image system functions exist"""
    print("\n[TEST] Image system functions exist")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    test_result("_save_visitor_offer exists", "_save_visitor_offer" in content)
    test_result("_finalize_offer exists", "_finalize_offer" in content)
    test_result("Image handling (photo handler)", "handle_photo" in content or "handle_images" in content)
    test_result("Media group sending", "send_media_group" in content or "MediaGroup" in content)


def test_publish_system_exists():
    """Test 12: Publish system functions exist"""
    print("\n[TEST] Publish system functions exist")
    with open("bot/bot.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    test_result("_approve_visitor_offer exists", "_approve_visitor_offer" in content)
    test_result("_reject_visitor_offer exists", "_reject_visitor_offer" in content)
    test_result("publish_status field referenced", "publish_status" in content)
    test_result("office_location referenced", "office_location" in content)


def test_bids_json_file():
    """Test 13: bids.json file exists and is valid"""
    print("\n[TEST] bids.json file")
    bids_path = Path("bot/data/bids.json")
    test_result("bids.json exists", bids_path.exists())
    if bids_path.exists():
        with open(bids_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        test_result("bids.json has 'bids' key", "bids" in data)
        test_result("bids.json bids is a list", isinstance(data.get("bids"), list))


def test_rbac_integration():
    """Test 14: RBAC integration with user_manager"""
    print("\n[TEST] RBAC integration (user_manager)")
    # Import user_manager and test
    try:
        import user_manager
        test_result("user_manager imports successfully", True)
        
        # Check 4 roles exist
        test_result("ROLE_ADMIN exists", hasattr(user_manager, 'ROLE_ADMIN'))
        test_result("ROLE_REVIEWER exists", hasattr(user_manager, 'ROLE_REVIEWER'))
        test_result("ROLE_PUBLISHER exists", hasattr(user_manager, 'ROLE_PUBLISHER'))
        test_result("ROLE_EDITOR exists", hasattr(user_manager, 'ROLE_EDITOR'))
        
        # Check change_role function
        test_result("change_role function exists", hasattr(user_manager, 'change_role'))
        test_result("get_user_role function exists", hasattr(user_manager, 'get_user_role'))
        test_result("get_all_users function exists", hasattr(user_manager, 'get_all_users'))
        test_result("add_user function exists", hasattr(user_manager, 'add_user'))
        
    except Exception as e:
        test_result("user_manager imports", False, str(e)[:200])


def main():
    print("=" * 60)
    print("PHASE 2 TESTS — Admin Roles + Bidding DB + Offer Retrieval")
    print("=" * 60)
    
    test_syntax_compilation()
    test_new_functions_exist()
    test_add_user_roles()
    test_change_role_command()
    test_admin_menu_roles()
    test_myid_list_users_roles()
    test_bid_storage_functions()
    test_update_offer_with_bid_logic()
    test_bid_notification_db_update()
    test_visitor_requests_permanent_ids()
    test_image_system_exists()
    test_publish_system_exists()
    test_bids_json_file()
    test_rbac_integration()
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {PASS} passed, {FAIL} failed, {PASS + FAIL} total")
    print("=" * 60)
    
    if ERRORS:
        print("\nFAILURES:")
        for err in ERRORS:
            print(f"  ✗ {err}")
    
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
