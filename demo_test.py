"""
StackConnect Phoenix 2026 — Demo 1: Self-Healing Selector Test

Setup:
  pip install selenium python-dotenv webdriver-manager

.env file in THIS folder:
  OPENAI_API_KEY=sk-proj-...

Demo flow:
  PASS run:  UI_BROKEN=False in app.py  →  python demo_test.py  →  green
  HEAL run:  UI_BROKEN=True  in app.py  →  python demo_test.py  →  breaks then heals
"""

import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ── Load .env ─────────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    # Manual fallback if python-dotenv not installed
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        for raw in env_file.read_text(encoding="utf-8").splitlines():
            raw = raw.strip()
            if raw and not raw.startswith("#") and "=" in raw:
                k, v = raw.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

# ── Config ────────────────────────────────────────────────────────────────────
APP_URL         = "http://localhost:8080"
BROKEN_SELECTOR = "#book-now"   # always starts here — healer updates at runtime
CONFIDENCE_MIN  = 0.81

# ── Colours ───────────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def log(msg, color="", delay=0):
    print(f"{color}[{datetime.now().strftime('%H:%M:%S')}] {msg}{RESET}")
    if delay: time.sleep(delay)

def banner(msg, color=CYAN):
    print(f"\n{BOLD}{color}{'='*60}{RESET}")
    print(f"{BOLD}{color}  {msg}{RESET}")
    print(f"{BOLD}{color}{'='*60}{RESET}\n")


# ── Slow human-like typing ────────────────────────────────────────────────────
def slow_type(el, text, delay=0.09):
    el.clear()
    for ch in text:
        el.send_keys(ch)
        time.sleep(delay)


# ── Git diff ──────────────────────────────────────────────────────────────────
def get_git_diff():
    try:
        r = subprocess.run(
            ["git", "diff", "HEAD~1", "HEAD", "--", "*.html", "*.py"],
            capture_output=True, text=True, cwd=str(Path(__file__).parent)
        )
        if r.stdout.strip():
            return r.stdout[:1200]
    except Exception:
        pass
    return ('- <button id="book-now">Book Now</button>\n'
            '+ <button id="reserve-room">Reserve Now</button>\n'
            '(UI_BROKEN flag changed to True in app.py)')


# ── AI call ───────────────────────────────────────────────────────────────────
def call_ai_for_selector(broken_selector, git_diff, page_source):
    import urllib.request

    api_key = os.environ.get("OPENAI_API_KEY", "").strip()

    # Debug: show key status
    if api_key:
        log(f"  API key found: {api_key[:8]}...{api_key[-4:]}", CYAN)
    else:
        log("  No OPENAI_API_KEY found — using demo fallback", YELLOW)
        log("  Make sure demo_app/.env contains: OPENAI_API_KEY=sk-...", YELLOW)
        time.sleep(2.5)
        # Fallback: scan page source to find correct button id
        # This makes the fallback work correctly regardless of UI state
        # page source may have &quot; instead of " (HTML encoded)
        clean_src = page_source.replace('&quot;', '"')
        ids = re.findall(r'<button[^>]+id="([^"]+)"', clean_src)
        btn_id = ids[0] if ids else "reserve-room"
        return {
            "selector":   f"#{btn_id}",
            "confidence": 0.91,
            "reason":     f"Found button id '{btn_id}' in page source (demo fallback)"
        }

    # Extract button section from page source
    snip = ""
    m = re.search(r'<button[^>]*id=[^>]+>.*?</button>', page_source, re.DOTALL)
    if m:
        snip = page_source[max(0, m.start()-100):m.end()+100]

    prompt = f"""A Selenium test failed with NoSuchElementException.

Broken selector: {broken_selector}

Git diff (what changed):
{git_diff}

Page source snippet (buttons):
{snip[:600]}

Return ONLY valid JSON — no markdown:
{{"selector": "#id-here", "confidence": 0.94, "reason": "one line"}}"""

    payload = json.dumps({
        "model": "gpt-4o",
        "max_tokens": 120,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": "QA expert. Return only JSON."},
            {"role": "user",   "content": prompt}
        ]
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {api_key}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read())["choices"][0]["message"]["content"]
            return json.loads(re.sub(r"```(?:json)?|```", "", raw).strip())
    except Exception as e:
        log(f"  API error: {e} — using page-source fallback", YELLOW)
        # page source may have &quot; instead of " (HTML encoded)
        clean_src = page_source.replace('&quot;', '"')
        ids = re.findall(r'<button[^>]+id="([^"]+)"', clean_src)
        btn_id = ids[0] if ids else "reserve-room"
        return {"selector": f"#{btn_id}", "confidence": 0.88,
                "reason": f"Found button id '{btn_id}' in page source"}


# ── Patch file ────────────────────────────────────────────────────────────────
def patch_test_file(old_sel, new_sel):
    path = Path(__file__)
    src  = path.read_text(encoding="utf-8")
    new  = re.sub(
        r'^(BROKEN_SELECTOR\s*=\s*)"[^"]*"',
        rf'\g<1>"{new_sel}"',
        src, count=1, flags=re.MULTILINE
    )
    if new != src:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def log_heal(old, new, conf, reason):
    log_file = Path(__file__).parent / "heal_log.txt"
    with open(log_file, "a") as f:
        f.write(f"\n[{datetime.now().isoformat()}]\n"
                f"  OLD: {old}\n  NEW: {new}\n"
                f"  CONFIDENCE: {conf:.0%}\n  REASON: {reason}\n")


# ── Selenium test ─────────────────────────────────────────────────────────────
def run_booking_test(selector_override=None):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.support.ui import WebDriverWait, Select
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.service import Service

    opts = Options()
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--start-maximized")

    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()), options=opts)
    except Exception:
        driver = webdriver.Chrome(options=opts)

    page_source = ""
    try:
        log("  Opening hotel app...", CYAN)
        driver.get(APP_URL)
        wait = WebDriverWait(driver, 10)
        time.sleep(1.5)

        # Dates
        log("  Setting dates — check-in tomorrow, 2 nights...", CYAN)
        cin  = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        cout = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        driver.execute_script("document.getElementById('checkin').value = arguments[0]",  cin)
        time.sleep(0.4)
        driver.execute_script("document.getElementById('checkout').value = arguments[0]", cout)
        time.sleep(0.4)
        log(f"  Check-in: {cin}  →  Check-out: {cout}", CYAN)

        # Guests
        time.sleep(0.3)
        Select(driver.find_element(By.ID, "guests")).select_by_visible_text("2 Guests")
        time.sleep(0.5)

        # Name and email — slow type
        log("  Typing guest name and email...", CYAN)
        slow_type(driver.find_element(By.ID, "first-name"), "Demo",   0.10)
        time.sleep(0.35)
        slow_type(driver.find_element(By.ID, "last-name"),  "User",   0.10)
        time.sleep(0.35)
        slow_type(driver.find_element(By.ID, "email"), "demo@stackconnect.io", 0.07)
        time.sleep(1.0)

        # Click the button
        page_source = driver.page_source
        sel = selector_override or BROKEN_SELECTOR
        log(f"  Clicking button: {sel}", CYAN)
        time.sleep(0.5)

        # Diagnostic: show what buttons exist in the DOM
        all_btns = driver.find_elements(By.TAG_NAME, "button")
        if all_btns:
            btn_ids = [b.get_attribute('id') or b.text for b in all_btns]
            log(f"  Buttons found in DOM: {btn_ids}", CYAN)
        else:
            log("  WARNING: No buttons found in DOM at all!", YELLOW)

        # Find the specific selector — raise if not found (triggers healer)
        elements = driver.find_elements(By.CSS_SELECTOR, sel)
        if not elements:
            raise RuntimeError(f"NoSuchElementException: {sel} not found")

        btn = elements[0]
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior:'smooth',block:'center'})", btn)
        time.sleep(0.7)
        driver.execute_script("arguments[0].click()", btn)
        time.sleep(2.0)
        return True, page_source

    except Exception as e:
        page_source = driver.page_source if driver else ""
        raise RuntimeError(
            f"NoSuchElementException: {selector_override or BROKEN_SELECTOR} not found"
        ) from e
    finally:
        time.sleep(0.8)
        driver.quit()


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    global BROKEN_SELECTOR
    banner("StackConnect 2026 — Self-Healing Demo")
    log(f"App URL:         {APP_URL}", CYAN)
    log(f"Looking for:     {BROKEN_SELECTOR}", CYAN)
    log(f"Heal threshold:  {CONFIDENCE_MIN:.0%}", CYAN)

    # .env loading check — helps debug key issues
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        raw_env = env_path.read_text(encoding="utf-8")
        for line in raw_env.splitlines():
            line = line.strip()
            if line.startswith("OPENAI_API_KEY="):
                val = line.split("=", 1)[1].strip()
                if val:
                    os.environ["OPENAI_API_KEY"] = val

    key = os.environ.get("OPENAI_API_KEY", "")
    if key:
        log(f"OpenAI key:      {key[:8]}...{key[-4:]} ✓", GREEN)
    else:
        log("OpenAI key:      NOT FOUND — using smart fallback", YELLOW)
        log(f"                 .env path: {env_path}", YELLOW)
        log(f"                 .env exists: {env_path.exists()}", YELLOW)
    print()

    t0 = time.time()
    log("Running booking test...", BOLD)

    # ── Attempt the test ──────────────────────────────────────────────────────
    try:
        passed, _ = run_booking_test()
        log(f"✅  TEST PASSED  ({time.time()-t0:.1f}s)  —  {BROKEN_SELECTOR} found", GREEN)
        log("Suite is green. No healing needed. 🎉", GREEN)
        return
    except RuntimeError as e:
        log(f"💥  {e}  ({time.time()-t0:.1f}s)", RED)

    # ── Get page source (headless, not visible) ───────────────────────────────
    log("  Getting page source for AI analysis...", CYAN, 0.2)
    page_source = ""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        opts = Options()
        opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            d = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
        except Exception:
            d = webdriver.Chrome(options=opts)
        d.get(APP_URL)
        page_source = d.page_source
        d.quit()
    except Exception:
        pass

    # ── Healing ───────────────────────────────────────────────────────────────
    banner("🤖  Self-Healing Agent Activated")

    log("Step 1: Exception caught — test NOT marked failed yet", CYAN)
    log(f"        Selector '{BROKEN_SELECTOR}' not found in DOM", CYAN, 0.5)

    log("\nStep 2: Reading git diff...", CYAN, 0.3)
    git_diff = get_git_diff()
    for line in git_diff.splitlines()[:5]:
        col = RED if line.startswith("-") else GREEN if line.startswith("+") else YELLOW
        log(f"        {line}", col, 0.12)

    log("\nStep 3: Calling AI — asking for the correct selector...", CYAN, 0.3)
    ai_start = time.time()
    result   = call_ai_for_selector(BROKEN_SELECTOR, git_diff, page_source)
    ai_time  = time.time() - ai_start

    new_sel    = result["selector"]
    confidence = float(result["confidence"])
    reason     = result.get("reason", "")

    print()
    log(f"  🎯  Suggested:   {BOLD}{new_sel}{RESET}", GREEN)
    log(f"  📊  Confidence:  {BOLD}{confidence:.0%}{RESET}",
        GREEN if confidence >= CONFIDENCE_MIN else YELLOW)
    log(f"  💬  Reason:      {reason}", CYAN)
    log(f"  ⏱   AI time:     {ai_time:.1f}s", CYAN)
    print()

    if confidence >= CONFIDENCE_MIN:
        log(f"Step 4: {confidence:.0%} ≥ {CONFIDENCE_MIN:.0%}  →  AUTO-PATCHING", GREEN, 0.3)
        old_sel         = BROKEN_SELECTOR
        BROKEN_SELECTOR = new_sel

        if patch_test_file(old_sel, new_sel):
            log(f"        ✅  Test file updated: {old_sel}  →  {new_sel}", GREEN)
        log_heal(old_sel, new_sel, confidence, reason)
        log(f"        📝  Logged to heal_log.txt", CYAN, 0.5)

        log("\nStep 5: Re-running with healed selector...", CYAN, 0.5)
        try:
            run_booking_test(selector_override=new_sel)
            total = time.time() - t0
            banner("✅  HEALED AND PASSING", GREEN)
            log(f"  Old: {old_sel}  →  New: {new_sel}", GREEN)
            log(f"  Confidence: {confidence:.0%}  |  Total time: {total:.1f}s", GREEN)
            print()
            log("  No engineer paged. No Slack message. 🎉", GREEN)
        except RuntimeError as e:
            log(f"Re-run failed: {e}", RED)
            log("Verify app.py is running and UI_BROKEN=True", YELLOW)
    else:
        banner(f"⚠️  CONFIDENCE {confidence:.0%} < {CONFIDENCE_MIN:.0%} — HUMAN REVIEW", YELLOW)
        log(f"  Suggested: {new_sel}  |  {reason}", YELLOW)


if __name__ == "__main__":
    main()
