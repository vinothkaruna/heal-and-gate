"""
StackConnect Phoenix 2026 — Demo 2
GitHub Merge Gate Simulation
=============================
Simulates the full merge gate pipeline:
  1. Webhook received from GitHub
  2. AI reads the diff
  3. Self-healer patches 3 broken selectors
  4. Suite runs — 3 real failures found
  5. PR blocked with detailed comment

Zero external dependencies — no browser, no API, always works.
Safe fallback if Demo 1 has any issues.

Run: python merge_gate_demo.py
"""

import time
from datetime import datetime

GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def log(msg, color="", delay=0.35):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{ts}] {msg}{RESET}")
    time.sleep(delay)

def banner(msg, color=CYAN):
    print(f"\n{BOLD}{color}{'═'*60}{RESET}")
    print(f"{BOLD}{color}  {msg}{RESET}")
    print(f"{BOLD}{color}{'═'*60}{RESET}\n")
    time.sleep(0.5)


def main():
    banner("GitHub Merge Gate — Live Demo", CYAN)

    # ── Step 1: Webhook arrives ───────────────────────────────────────────────
    log("📨  Incoming GitHub webhook...", CYAN, 0.5)
    time.sleep(0.3)

    payload = {
        "event":   "pull_request",
        "action":  "opened",
        "pr":      "#42",
        "branch":  "feature/update-booking-flow",
        "sha":     "a3f9c2d",
        "author":  "dev-sarah",
        "message": "Update booking form — rename IDs for consistency",
    }
    print()
    for k, v in payload.items():
        log(f"  {k:10s}: {v}", YELLOW, 0.12)

    print()
    log("🔐  Signature verified — webhook is authentic", GREEN, 0.5)
    log("📂  Event received — spawning test pipeline...", CYAN, 0.8)

    # ── Step 2: AI reads the diff ─────────────────────────────────────────────
    banner("🤖  AI Reading the Diff", YELLOW)
    log("Fetching git diff for PR #42...", CYAN, 0.6)
    time.sleep(0.4)

    diff_lines = [
        '  - <button id="book-now">Book Now</button>',
        '  + <button id="reserve-room">Reserve Now</button>',
        '  - <input id="email" type="email" ...>',
        '  + <input id="guest-email" type="email" ...>',
        '  - <select id="guests" ...>',
        '  + <select id="guest-count" ...>',
    ]
    for line in diff_lines:
        col = RED if line.strip().startswith("-") else GREEN
        log(line, col, 0.22)

    print()
    log("🎯  AI analysis complete:", CYAN, 0.3)
    log("    → 3 element IDs renamed in booking form", YELLOW, 0.2)
    log("    → Affected suites: e2e_booking, form_validation", YELLOW, 0.2)
    log("    → Self-healer will patch selectors before running", YELLOW, 0.8)

    # ── Step 3: Self-healer ───────────────────────────────────────────────────
    banner("🔧  Self-Healer Running", CYAN)
    heals = [
        ("#book-now",   "#reserve-room", 0.94),
        ("#email",      "#guest-email",  0.87),
        ("#guests",     "#guest-count",  0.91),
    ]
    for old, new, conf in heals:
        log(f"  Healing: {old:<18} →  {new:<20}  (confidence {conf:.0%})", GREEN, 0.65)

    print()
    log("✅  All 3 selectors auto-patched", GREEN, 0.8)
    log("    Running suite against patched tests now...", CYAN, 0.5)

    # ── Step 4: Tests run ─────────────────────────────────────────────────────
    banner("⚡  Running Test Suite on Staging", CYAN)

    tests = [
        ("TC_001", "Guest can fill booking form",                    True,  1.1),
        ("TC_002", "Date validation — past dates rejected",          True,  0.75),
        ("TC_003", "Guest count minimum is 1",                       True,  0.6),
        ("TC_004", "Booking submission — confirmation shown",        False, 1.4),
        ("TC_005", "Email confirmation sent to guest",               False, 0.9),
        ("TC_006", "Booking appears in admin dashboard",             False, 1.1),
        ("TC_007", "Cancel booking flow works",                      True,  0.65),
        ("TC_008", "Room price displayed correctly",                 True,  0.5),
    ]

    passed = failed = 0
    for tc_id, name, result, delay in tests:
        if result:
            log(f"  ✅  {tc_id}  {name}", GREEN, delay)
            passed += 1
        else:
            log(f"  ✗   {tc_id}  {name}  — FAILED", RED, delay)
            failed += 1

    # ── Step 5: Post to PR ────────────────────────────────────────────────────
    banner("📊  Posting Result to GitHub PR", RED)

    log(f"  Status:  ✗  FAILED  ({passed} passed, {failed} failed)", RED, 0.3)
    log(f"  PR #42:  MERGE BLOCKED", RED, 0.3)
    log(f"  Action:  Required status check did not pass\n", RED, 0.5)

    log("  PR comment posted automatically:", CYAN, 0.3)

    print(f"""
{RED}  ┌─────────────────────────────────────────────────────┐
  │  ✗  QA Gate — 3 tests failed                        │
  │                                                     │
  │  TC_004  Booking submission — confirmation not shown │
  │  TC_005  Email confirmation not sent to guest       │
  │  TC_006  Booking not in admin dashboard             │
  │                                                     │
  │  Root cause: POST /api/book returning 500           │
  │  Likely cause: server-side handler not updated      │
  │  after form fields were renamed                     │
  │                                                     │
  │  Selectors: auto-healed ✅  (3 of 3)               │
  │  Regressions: 3 real failures ✗                     │
  │                                                     │
  │  Fix the backend handler and re-push.               │
  └─────────────────────────────────────────────────────┘{RESET}""")

    print()
    log("🛑  Developer is notified. Bad code never reached main.", YELLOW, 0.5)
    log("⏱   Total time — push to blocked PR: 73 seconds", CYAN, 0.3)

    banner("Demo Complete", GREEN)
    log("This entire flow ran automatically.", GREEN, 0.3)
    log("No QA engineer was involved.", GREEN, 0.3)
    log("Developer gets feedback in under 90 seconds.", GREEN, 0.3)
    print()


if __name__ == "__main__":
    main()
