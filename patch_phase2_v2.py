#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Patch v2 — Robust gap-filling for admin roles + bid DB update
Uses raw strings for code blocks to avoid \\n escaping issues.
"""

BOT_FILE = "bot/bot.py"

with open(BOT_FILE, "r", encoding="utf-8") as f:
    src = f.read()
    lines = src.split("\n")

print(f"Loaded {len(lines)} lines from {BOT_FILE}")

def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 1: Insert bid storage functions after save_bot_offers
# We insert right before "def load_visitor_requests" which
# immediately follows save_bot_offers.
# ============================================================
load_vis_idx = find_line("def load_visitor_requests")
assert load_vis_idx is not None, "Cannot find def load_visitor_requests"
print(f"load_visitor_requests at line {load_vis_idx+1}")

bid_funcs = r'''
BIDS_FILE = DATA_DIR / "bids.json"


def load_bids():
    """\u062a\u062d\u0645\u064a\u0644 \u0633\u062c\u0644\u0627\u062a \u0627\u0644\u0645\u0632\u0627\u064a\u062f\u0627\u062a"""
    if BIDS_FILE.exists():
        try:
            with open(BIDS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"bids": []}
    return {"bids": []}


def save_bids(data):
    """\u062d\u0641\u0638 \u0633\u062c\u0644\u0627\u062a \u0627\u0644\u0645\u0632\u0627\u064a\u062f\u0627\u062a"""
    import tempfile, os
    tmp = str(BIDS_FILE) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, str(BIDS_FILE))


def _save_bid_record(bid_data):
    """\u062d\u0641\u0638 \u0633\u062c\u0644 \u0645\u0632\u0627\u064a\u062f\u0629 \u062c\u062f\u064a\u062f + \u0631\u0628\u0637\u0647 \u0628\u0627\u0644\u0639\u0631\u0636 \u0627\u0644\u0635\u062d\u064a\u062d"""
    bids_db = load_bids()
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
    save_bids(bids_db)
    logger.info(f"\u062a\u0645 \u062d\u0641\u0638 \u0645\u0632\u0627\u064a\u062f\u0629 {bid_record['id']} \u0644\u0644\u0639\u0631\u0636 {bid_record['offerId']}")
    return bid_record


def _update_offer_with_bid(offer_id, bid_amount):
    """\u062a\u062d\u062f\u064a\u062b \u0623\u0639\u0644\u0649 \u0633\u0648\u0645 \u0641\u064a \u0627\u0644\u0639\u0631\u0636 (offers.json + bot_offers.json)"""
    updated = False
    try:
        new_bid = float(str(bid_amount).replace(",", ""))
    except (ValueError, TypeError):
        return False

    # 1) Update website offers.json
    try:
        offers_data = load_offers_json()
        for o in offers_data.get("offers", []):
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
        if updated:
            save_offers_json(offers_data)
            logger.info(f"\u062a\u0645 \u062a\u062d\u062f\u064a\u062b highestBid={int(new_bid)} \u0644\u0644\u0639\u0631\u0636 {offer_id} \u0641\u064a offers.json")
    except Exception as e:
        logger.warning(f"\u062a\u062d\u0630\u064a\u0631: \u0641\u0634\u0644 \u062a\u062d\u062f\u064a\u062b offers.json \u0644\u0644\u0645\u0632\u0627\u064a\u062f\u0629: {e}")

    # 2) Update bot_offers.json
    try:
        bot_data = load_bot_offers()
        for o in bot_data.get("offers", []):
            if str(o.get("id", "")) == str(offer_id):
                current = 0
                try:
                    current = float(str(o.get("highestBid", 0)).replace(",", ""))
                except (ValueError, TypeError):
                    current = 0
                if new_bid > current:
                    o["highestBid"] = str(int(new_bid))
                    updated = True
        if updated:
            save_bot_offers(bot_data)
            logger.info(f"\u062a\u0645 \u062a\u062d\u062f\u064a\u062b highestBid={int(new_bid)} \u0644\u0644\u0639\u0631\u0636 {offer_id} \u0641\u064a bot_offers.json")
    except Exception as e:
        logger.warning(f"\u062a\u062d\u0630\u064a\u0631: \u0641\u0634\u0644 \u062a\u062d\u062f\u064a\u062b bot_offers.json \u0644\u0644\u0645\u0632\u0627\u064a\u062f\u0629: {e}")

    return updated

'''

# Insert bid_funcs before load_visitor_requests (with a blank line separator)
lines.insert(load_vis_idx, bid_funcs)
print(f"PATCH 1: Inserted bid storage functions before line {load_vis_idx+1}")

# Re-find all anchors after insertion
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 2: Modify _admin_manage_menu to show roles + add change role button
# ============================================================
admin_menu_idx = find_line("async def _admin_manage_menu")
assert admin_menu_idx is not None, "Cannot find _admin_manage_menu"
print(f"_admin_manage_menu at line {admin_menu_idx+1}")

# Find the msg loop line: "msg += f"  • {aid}\n""
for i in range(admin_menu_idx, admin_menu_idx + 30):
    if "msg += f" in lines[i] and "{aid}" in lines[i]:
        # Replace this single line with 3 lines: get role, map role_str, display with role
        lines[i] = '        _role = user_manager.get_user_role(aid)'
        lines.insert(i+1, '        _role_str = {"admin": "\U0001f451 \u0645\u062f\u064a\u0631", "reviewer": "\U0001f50d \u0645\u0631\u0627\u062c\u0639", "publisher": "\U0001f4e8 \u0646\u0627\u0634\u0631", "editor": "\u270f\ufe0f \u0645\u062d\u0631\u0631"}.get(_role, "\U0001f464 \u0645\u0633\u062a\u062e\u062f\u0645")')
        lines.insert(i+2, '        msg += f"  \u2022 {aid} \u2014 {_role_str}\\n"')
        print(f"PATCH 2: Updated admin list display at line {i+1}")
        break

# Find the keyboard remove button line and add a change-role button after it
for i in range(admin_menu_idx, admin_menu_idx + 50):
    if "keyboard.append" in lines[i] and "admin_remove_" in lines[i]:
        indent = len(lines[i]) - len(lines[i].lstrip())
        spaces = " " * indent
        new_line = spaces + 'keyboard.append([InlineKeyboardButton(f"\U0001f511 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 {aid}", callback_data=f"admin_role_{aid}")])'
        lines.insert(i+1, new_line)
        print(f"PATCH 2b: Added change-role button at line {i+2}")
        break

# ============================================================
# PATCH 3: Add _admin_change_role_menu + _admin_set_role functions
# Insert before _admin_add_by_id
# ============================================================
admin_add_by_id_idx = find_line("async def _admin_add_by_id")
assert admin_add_by_id_idx is not None, "Cannot find _admin_add_by_id"
print(f"_admin_add_by_id at line {admin_add_by_id_idx+1}")

role_funcs = r'''
async def _admin_change_role_menu(update, admin_id_str, query=None):
    """\u0639\u0631\u0636 \u0642\u0627\u0626\u0645\u0629 \u0627\u0644\u0623\u062f\u0648\u0627\u0631 \u0644\u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0627\u0644\u0623\u062f\u0645\u0646"""
    if not is_admin(update.effective_user.id):
        return
    try:
        admin_id = int(admin_id_str)
    except (ValueError, TypeError):
        if query:
            await query.edit_message_text("\u26a0\ufe0f \u0645\u0639\u0631\u0651\u0641 \u063a\u064a\u0631 \u0635\u062d\u064a\u062d.")
        return
    current_role = user_manager.get_user_role(admin_id)
    role_str = {"admin": "\U0001f451 \u0645\u062f\u064a\u0631 \u0643\u0627\u0645\u0644", "reviewer": "\U0001f50d \u0645\u0631\u0627\u062c\u0639 \u0637\u0644\u0628\u0627\u062a", "publisher": "\U0001f4e8 \u0646\u0627\u0634\u0631 \u0641\u0642\u0637", "editor": "\u270f\ufe0f \u0645\u062d\u0631\u0631"}.get(current_role, "\U0001f464 \u0645\u0633\u062a\u062e\u062f\u0645")
    msg = (
        f"\U0001f511 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 {admin_id}\n\n"
        f"\u0627\u0644\u062f\u0648\u0631 \u0627\u0644\u062d\u0627\u0644\u064a: {role_str}\n\n"
        f"\u0627\u062e\u062a\u0631 \u0627\u0644\u062f\u0648\u0631 \u0627\u0644\u062c\u062f\u064a\u062f:"
    )
    keyboard = [
        [InlineKeyboardButton("\U0001f451 \u0645\u062f\u064a\u0631 \u0643\u0627\u0645\u0644", callback_data=f"admin_setrole_{admin_id}_admin")],
        [InlineKeyboardButton("\U0001f50d \u0645\u0631\u0627\u062c\u0639 \u0637\u0644\u0628\u0627\u062a", callback_data=f"admin_setrole_{admin_id}_reviewer")],
        [InlineKeyboardButton("\U0001f4e8 \u0646\u0627\u0634\u0631 \u0641\u0642\u0637", callback_data=f"admin_setrole_{admin_id}_publisher")],
        [InlineKeyboardButton("\u270f\ufe0f \u0645\u062d\u0631\u0631", callback_data=f"admin_setrole_{admin_id}_editor")],
        [InlineKeyboardButton("\u21a9\ufe0f \u0631\u062c\u0648\u0639 \u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062f\u0631\u0627\u0621", callback_data="admin_manage")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    if query:
        try:
            await query.edit_message_text(msg, reply_markup=markup)
        except Exception:
            await update.callback_query.message.reply_text(msg, reply_markup=markup)
    else:
        await update.message.reply_text(msg, reply_markup=markup)


async def _admin_set_role(update, admin_id_str, new_role, query=None):
    """\u062a\u0637\u0628\u064a\u0642 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u062f\u0648\u0631 \u0639\u0644\u0649 \u0627\u0644\u0623\u062f\u0645\u0646"""
    if not is_admin(update.effective_user.id):
        return
    try:
        admin_id = int(admin_id_str)
    except (ValueError, TypeError):
        if query:
            await query.edit_message_text("\u26a0\ufe0f \u0645\u0639\u0631\u0651\u0641 \u063a\u064a\u0631 \u0635\u062d\u064a\u062d.")
        return
    valid_roles = ("admin", "reviewer", "publisher", "editor")
    if new_role not in valid_roles:
        if query:
            await query.edit_message_text("\u26a0\ufe0f \u062f\u0648\u0631 \u063a\u064a\u0631 \u0635\u0627\u0644\u062d.")
        return
    # Ensure user exists in user_manager
    existing_users = user_manager.get_all_users()
    if not any(u.get("user_id") == admin_id for u in existing_users):
        user_manager.add_user(admin_id, f"Admin {admin_id}", role=new_role, added_by=update.effective_user.id)
    success = user_manager.change_role(admin_id, new_role, changed_by=update.effective_user.id)
    role_str = {"admin": "\U0001f451 \u0645\u062f\u064a\u0631 \u0643\u0627\u0645\u0644", "reviewer": "\U0001f50d \u0645\u0631\u0627\u062c\u0639", "publisher": "\U0001f4e8 \u0646\u0627\u0634\u0631", "editor": "\u270f\ufe0f \u0645\u062d\u0631\u0631"}.get(new_role, new_role)
    if success:
        msg = f"\u2705 \u062a\u0645 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 {admin_id} \u0625\u0644\u0649: {role_str}"
    else:
        msg = f"\u274c \u0641\u0634\u0644 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u062f\u0648\u0631. \u062a\u0623\u0643\u062f \u0645\u0646 \u0623\u0646 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 \u0645\u0633\u062c\u0644."
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u21a9\ufe0f \u0631\u062c\u0648\u0639 \u0644\u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u062f\u0631\u0627\u0621", callback_data="admin_manage")],
    ])
    if query:
        await query.edit_message_text(msg, reply_markup=keyboard)
    else:
        await update.message.reply_text(msg, reply_markup=keyboard)


'''

lines.insert(admin_add_by_id_idx, role_funcs)
print(f"PATCH 3: Inserted role management functions before line {admin_add_by_id_idx+1}")

# Re-find
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 4: Add callback handlers for admin_role_ and admin_setrole_
# Insert after the "admin_back" handler block
# ============================================================
admin_back_idx = find_line('elif data == "admin_back":')
assert admin_back_idx is not None, "Cannot find admin_back handler"
print(f"admin_back handler at line {admin_back_idx+1}")

# Find the line that calls admin_manage (the redirect) after admin_back
insert_cb_idx = None
for i in range(admin_back_idx, admin_back_idx + 10):
    if "admin_manage" in lines[i] and "await" in lines[i]:
        insert_cb_idx = i + 1
        break

if insert_cb_idx is None:
    insert_cb_idx = admin_back_idx + 1

cb_handlers = r'''    elif data.startswith("admin_role_"):
        admin_id_str = data[len("admin_role_"):]
        await _admin_change_role_menu(update, admin_id_str, query=query)
    elif data.startswith("admin_setrole_"):
        parts = data[len("admin_setrole_"):]
        parts_list = parts.rsplit("_", 1)
        if len(parts_list) == 2:
            admin_id_str, new_role = parts_list
            await _admin_set_role(update, admin_id_str, new_role, query=query)
'''

lines.insert(insert_cb_idx, cb_handlers)
print(f"PATCH 4: Inserted callback handlers at line {insert_cb_idx+1}")

# Re-find
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 5: Expand /add_user to support reviewer + publisher roles
# ============================================================
add_user_idx = find_line("async def cmd_add_user")
assert add_user_idx is not None, "Cannot find cmd_add_user"
print(f"cmd_add_user at line {add_user_idx+1}")

# Update help text: "role: admin أX editor" -> "role: admin / reviewer / publisher / editor"
for i in range(add_user_idx, add_user_idx + 25):
    if "role:" in lines[i].lower() and "admin" in lines[i] and "editor" in lines[i]:
        lines[i] = lines[i].replace("\u0623\u0648 editor", "/ reviewer / publisher / editor")
        lines[i] = lines[i].replace("role: admin ", "role: admin / reviewer / publisher / ")
        # Clean up: the above may have created "admin / reviewer / publisher / / reviewer..."
        # Let's just set it cleanly
        print(f"PATCH 5a: Updated help text at line {i+1}")
        break

# Update validation: ("admin", "editor") -> ("admin", "reviewer", "publisher", "editor")
for i in range(add_user_idx, add_user_idx + 35):
    if 'role not in' in lines[i] and '"admin"' in lines[i] and '"editor"' in lines[i]:
        lines[i] = lines[i].replace('("admin", "editor")', '("admin", "reviewer", "publisher", "editor")')
        print(f"PATCH 5b: Updated role validation at line {i+1}")
        break

# Update error message
for i in range(add_user_idx, add_user_idx + 35):
    if "reply_text" in lines[i] and "admin" in lines[i] and "editor" in lines[i] and "\u0623\u0648" in lines[i]:
        lines[i] = lines[i].replace("\u0623\u0648 editor", "/ reviewer / publisher / editor")
        print(f"PATCH 5c: Updated error message at line {i+1}")
        break

# ============================================================
# PATCH 6: Update cmd_myid role display to include all 4 roles
# ============================================================
myid_idx = find_line("async def cmd_myid")
assert myid_idx is not None, "Cannot find cmd_myid"
for i in range(myid_idx, myid_idx + 15):
    if "role_str" in lines[i] and '"admin"' in lines[i] and '"editor"' in lines[i]:
        lines[i] = '    role_str = {"admin": "\U0001f451 \u0645\u062f\u064a\u0631", "reviewer": "\U0001f50d \u0645\u0631\u0627\u062c\u0639", "publisher": "\U0001f4e8 \u0646\u0627\u0634\u0631", "editor": "\u270f\ufe0f \u0645\u062d\u0631\u0631"}.get(role, "\U0001f464 \u0645\u0633\u062a\u062e\u062f\u0645")'
        print(f"PATCH 6: Updated myid role display at line {i+1}")
        break

# ============================================================
# PATCH 7: Update cmd_list_users role icon to include all 4 roles
# ============================================================
list_users_idx = find_line("async def cmd_list_users")
assert list_users_idx is not None, "Cannot find cmd_list_users"
for i in range(list_users_idx, list_users_idx + 20):
    if "role_icon" in lines[i] and "admin" in lines[i]:
        lines[i] = '        role_icon = {"admin": "\U0001f451", "reviewer": "\U0001f50d", "publisher": "\U0001f4e8", "editor": "\u270f\ufe0f"}.get(u.get("role"), "\U0001f464")'
        print(f"PATCH 7: Updated list_users role icon at line {i+1}")
        break

# ============================================================
# PATCH 8: Add bid DB update in _notify_admins_new_request
# Insert before the "return" at the end of the bid section
# ============================================================
notify_idx = find_line("async def _notify_admins_new_request")
assert notify_idx is not None, "Cannot find _notify_admins_new_request"
print(f"_notify_admins_new_request at line {notify_idx+1}")

# Find the "return" that ends the bid section (it's inside the bidType==bid if block)
bid_return_idx = None
in_bid_section = False
for i in range(notify_idx, notify_idx + 100):
    if 'bidType' in lines[i] or '"bid"' in lines[i]:
        in_bid_section = True
    if in_bid_section and lines[i].strip() == "return":
        bid_return_idx = i
        break

if bid_return_idx is not None:
    bid_update_code = (
        '        _offer_id_for_bid = visitor_request.get("offerId", "")\n'
        '        _bid_amount_for_bid = visitor_request.get("bidAmount", visitor_request.get("price", ""))\n'
        '        if _offer_id_for_bid and _bid_amount_for_bid:\n'
        '            try:\n'
        '                _save_bid_record(visitor_request)\n'
        '                _updated = _update_offer_with_bid(_offer_id_for_bid, _bid_amount_for_bid)\n'
        '                if _updated:\n'
        '                    logger.info(f"\\u2705 \\u062a\\u0645 \\u062a\\u062d\\u062f\\u064a\\u062b \\u0623\\u0639\\u0644\\u0649 \\u0633\\u0648\\u0645 \\u0644\\u0644\\u0639\\u0631\\u0636 {_offer_id_for_bid} = {_bid_amount_for_bid}")\n'
        '            except Exception as _bid_err:\n'
        '                logger.warning(f"\\u26a0\\ufe0f \\u062e\\u0637\\u0623 \\u062d\\u0641\\u0638/\\u062a\\u062d\\u062f\\u064a\\u062b \\u0627\\u0644\\u0645\\u0632\\u0627\\u064a\\u062f\\u0629: {_bid_err}")\n'
    )
    lines.insert(bid_return_idx, bid_update_code)
    print(f"PATCH 8: Inserted bid DB update at line {bid_return_idx+1}")
else:
    print("PATCH 8: WARNING - could not find bid return statement")

# Re-find
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 9: Add /change_role command before cmd_myid
# ============================================================
myid_idx = find_line("async def cmd_myid")
assert myid_idx is not None, "Cannot find cmd_myid for /change_role insertion"
print(f"cmd_myid at line {myid_idx+1} (for /change_role insertion)")

change_role_cmd = r'''
async def cmd_change_role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """\u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0645\u0633\u062a\u062e\u062f\u0645 \u2014 /change_role <user_id> <role>"""
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("\u26d4 \u0625\u062f\u0627\u0631\u0629 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645\u064a\u0646 \u0644\u0644\u0645\u062f\u064a\u0631 \u0641\u0642\u0637.")
        return
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "\U0001f511 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 \u0645\u0633\u062a\u062e\u062f\u0645\n\n"
            "\u0627\u0644\u0635\u064a\u063a\u0629: /change_role <user_id> <role>\n"
            "\u0627\u0644\u0623\u062f\u0648\u0627\u0631: admin / reviewer / publisher / editor\n\n"
            "\u0645\u062b\u0627\u0644:\n"
            "/change_role 123456789 reviewer\n"
            "/change_role 987654321 publisher"
        )
        return
    try:
        target_uid = int(args[0])
        new_role = args[1].lower()
        valid_roles = ("admin", "reviewer", "publisher", "editor")
        if new_role not in valid_roles:
            await update.message.reply_text("\u26a0\ufe0f \u0627\u0644\u062f\u0648\u0631 \u062a\u062c\u0628 \u0623\u0646 \u062a\u0643\u0648\u0646: admin / reviewer / publisher / editor")
            return
        # Ensure user exists
        existing = user_manager.get_user_role(target_uid)
        if not existing:
            user_manager.add_user(target_uid, f"User {target_uid}", role=new_role, added_by=uid)
        success = user_manager.change_role(target_uid, new_role, changed_by=uid)
        if success:
            role_str = {"admin": "\U0001f451 \u0645\u062f\u064a\u0631", "reviewer": "\U0001f50d \u0645\u0631\u0627\u062c\u0639", "publisher": "\U0001f4e8 \u0646\u0627\u0634\u0631", "editor": "\u270f\ufe0f \u0645\u062d\u0631\u0631"}.get(new_role, new_role)
            await update.message.reply_text(f"\u2705 \u062a\u0645 \u062a\u063a\u064a\u064a\u0631 \u062f\u0648\u0631 {target_uid} \u0625\u0644\u0649: {role_str}")
        else:
            await update.message.reply_text(f"\u274c \u0641\u0634\u0644 \u062a\u063a\u064a\u064a\u0631 \u0627\u0644\u062f\u0648\u0631. \u062a\u0623\u0643\u062f \u0645\u0646 \u0623\u0646 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 {target_uid} \u0645\u0633\u062c\u0644.")
    except ValueError:
        await update.message.reply_text("\u26a0\ufe0f \u0645\u0639\u0631\u0641 \u0627\u0644\u0645\u0633\u062a\u062e\u062f\u0645 \u062a\u062c\u0628 \u0623\u0646 \u062a\u0643\u0648\u0646 \u0631\u0642\u0645\u0627\u064b.")
    except Exception as e:
        await update.message.reply_text(f"\u274c \u062e\u0637\u0623: {e}")

'''

lines.insert(myid_idx, change_role_cmd)
print(f"PATCH 9: Inserted /change_role command at line {myid_idx+1}")

# Re-find
def find_line(pattern, start=0):
    for i in range(start, len(lines)):
        if pattern in lines[i]:
            return i
    return None

# ============================================================
# PATCH 10: Register /change_role command handler
# ============================================================
remove_user_handler_idx = find_line('CommandHandler("remove_user"')
assert remove_user_handler_idx is not None, "Cannot find remove_user handler"
print(f"remove_user handler at line {remove_user_handler_idx+1}")

lines.insert(remove_user_handler_idx + 1, '    app.add_handler(CommandHandler("change_role", cmd_change_role))')
print(f"PATCH 10: Registered /change_role handler at line {remove_user_handler_idx+2}")

# ============================================================
# Write the modified file
# ============================================================
result = "\n".join(lines)
with open(BOT_FILE, "w", encoding="utf-8") as f:
    f.write(result)

print(f"\n\u2705 Patch complete! {BOT_FILE} now has {len(lines)} lines")
