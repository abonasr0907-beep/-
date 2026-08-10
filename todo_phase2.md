# Phase 2 — Task Tracker (Gap-Filling Only)

## Analysis Complete — Existing vs Gaps

### EXISTING (no rebuild needed):
- [x] Visitor requests/offers: stable IDs, archive retrieval, repost without delete (Phase 1)
- [x] Image system: upload, save, link to request, media group sending (Phase 1)
- [x] Publish system: approve/reject, office location, publish_status pipeline (Phase 1)
- [x] Bidding UI on website: priceType toggle, bid modal, sendBid(), WhatsApp (existing)
- [x] Basic admin: add_admin/remove_admin, /add_user, /list_users, /remove_user (existing)
- [x] RBAC in user_manager.py: 4 roles + 8 permission functions (Phase 1)

### GAPS TO FILL (Phase 2 work):
- [x] G1: /add_user only supports admin/editor → add reviewer + publisher roles
- [x] G2: _admin_manage_menu shows numeric IDs only → show role + permissions per admin
- [x] G3: /add_user and admin menu don't link to user_manager RBAC → integrated
- [x] G4: Add /change_role command + inline button to change admin role
- [x] G5: Bids sent to bot but highestBid NOT updated in offer DB → added _update_offer_with_bid()
- [x] G6: Bids not saved to a bids collection → bids.json + _save_bid_record() created
- [x] G7: Bot bid notifications enhanced with offer link (existing) + now saves to DB
- [x] G8: Tests for all gaps above (PENDING)
- [ ] G9: Push to GitHub + Final report

### PATCHES APPLIED (all verified syntactically):
- [x] PATCH 1: BIDS_FILE + load_bids/save_bids/_save_bid_record/_update_offer_with_bid
- [x] PATCH 2: _admin_manage_menu shows roles + change role button
- [x] PATCH 3: _admin_change_role_menu + _admin_set_role functions
- [x] PATCH 4: Callback handlers admin_role_ + admin_setrole_
- [x] PATCH 5: /add_user supports all 4 roles
- [x] PATCH 6: cmd_myid shows all 4 roles
- [x] PATCH 7: cmd_list_users shows all 4 role icons
- [x] PATCH 8: Bid DB update in _notify_admins_new_request
- [x] PATCH 9: /change_role command
- [x] PATCH 10: /change_role handler registered
- [x] bids.json initial file created
