#!/usr/bin/env python3
"""
RiskGraph Automation Suite
Run this on your WSL machine.
It uses browser-harness to automate:
  1. RapidAPI provider registration + API publishing
  2. Agentic profile creation (Molt, Claw, etc.)
  3. GitHub release creation

Usage: python3 scripts/automate.py
"""

import subprocess, json, time, sys, os, urllib.request

BROWSER_HARNESS_CMD = "browser-harness"
RISKGRAPH_API = "http://localhost:8000"
LAUNCH_PITCH = "RiskGraph: Credit score for open-source packages. Prevents AI agents from installing malicious dependencies."

def log(msg):
    print(f"  [{time.strftime('%H:%M:%S')}] {msg}", flush=True)

def browser(code: str):
    """Run Python code in browser-harness."""
    cmd = f"{BROWSER_HARNESS_CMD} <<'PY'
{code}
PY"
    result = subprocess.run(
        ["bash", "-c", cmd],
        capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        log(f"Browser FAILED: {result.stderr.strip()[:200]}")
        return None
    return result.stdout.strip()

def check_api():
    """Verify RiskGraph API is running."""
    try:
        r = urllib.request.urlopen(f"{RISKGRAPH_API}/api/v1/package-risk/npm/lodash", timeout=10)
        data = json.loads(r.read().decode())
        log(f"RiskGraph API: OK (lodash score={data['score']})")
        return True
    except Exception as e:
        log(f"RiskGraph API: NOT REACHABLE - {e}")
        return False

def check_browser():
    """Check if browser-harness works."""
    log("Checking browser-harness...")
    result = browser("print('BROWSER_OK')")
    if result and "BROWSER_OK" in result:
        log("Browser-harness: OK")
        return True
    log("Browser-harness: NOT FOUND - try: bash ~/sandbox/browser-harness/venv/bin/activate")
    return False

def register_rapidapi():
    """Register RiskGraph on RapidAPI."""
    log("Navigating to RapidAPI provider registration...")
    code = """
import time
navigate("https://rapidapi.com/auth/signup")
time.sleep(3)
print("Page loaded: " + page_info().get("url", "unknown"))
# The signup form fields
try:
    click("#email")
    type("#email", "riskgraph-agent@proton.me")
    time.sleep(0.5)
except: pass
try:
    click("#password")
    type("#password", "R1skGr4ph!Agent2026")
    time.sleep(0.5)
except: pass
print("RapidAPI: Form filled (waiting for user to complete CAPTCHA)")
print("Please complete the CAPTCHA in the Chrome window")
time.sleep(10)
"""
    result = browser(code)
    log(f"RapidAPI result: {result[:300] if result else 'No output'}")

def publish_api():
    """Publish the API on RapidAPI."""
    log("Publishing RiskGraph API on RapidAPI...")
    code = """
import time
navigate("https://rapidapi.com/developer/new-api")
time.sleep(3)
print("Page: " + page_info().get("url", "unknown"))
# Fill API details
try:
    click("#api-name")
    type("#api-name", "RiskGraph")
except: pass
try:
    click("#api-description")
    type("#api-description", "Credit score for open-source packages. Checks npm/PyPI packages for maintainer risk, CVE history, version anomalies, download trust.")
except: pass
try:
    click("#base-url")
    type("#base-url", "https://riskgraph-api.onrender.com")
except: pass
print("API form filled. Publish when ready.")
"""
    result = browser(code)
    log(f"Publish result: {result[:300] if result else 'No output'}")

def create_agentic_profiles():
    """Register on agentic economy platforms."""
    log("Creating agentic profiles...")
    
    # Molt (if it exists as a platform)
    platforms = [
        ("Molt", "https://molt.bot/register"),
        ("ClawHub", "https://clawhub.com/register"),
    ]
    
    for name, url in platforms:
        code = f"""
import time
navigate("{url}")
time.sleep(5)
print("{{0}}: Page loaded".format("{name}"))
# Basic info
for field in ["#name", "#username", "#display-name"]:
    try:
        click(field)
        type(field, "RiskGraph AI Agent")
        time.sleep(0.3)
    except: pass
for field in ["#email", "#email-address"]:
    try:
        click(field)
        type(field, "riskgraph-agent@proton.me")
        time.sleep(0.3)
    except: pass
print("{{0}}: Profile fields filled (complete manually if needed)".format("{name}"))
"""
        result = browser(code)
        log(f"{name}: {'done' if result else 'skipped'}")

def create_github_release():
    """Create a GitHub Release with the latest code."""
    log("Creating GitHub release...")
    try:
        PAT = os.environ.get("GITHUB_PAT", "")
        if not PAT:
            log("GitHub PAT not set in environment")
            return
        
        import subprocess
        os.chdir("/mnt/c/Users/User/riskgraph")
        result = subprocess.run(
            ["git", "tag", "-a", "v0.1.0", "-m", "Initial release: RiskGraph v0.1.0"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            ["git", "push", "origin", "v0.1.0"],
            capture_output=True, text=True, timeout=30
        )
        log(f"Release tag: {'OK' if result.returncode == 0 else result.stderr.strip()[:80]}")
    except Exception as e:
        log(f"Release: {e}")

def main():
    print("""
╔══════════════════════════════════════════════╗
║      RiskGraph Automation Suite v0.1        ║
║  Automated RapidAPI + Agentic Profiles      ║
╚══════════════════════════════════════════════╝
    """)
    
    api_ok = check_api()
    browser_ok = check_browser()
    
    if not api_ok:
        log("WARNING: RiskGraph API not reachable (expected at localhost:8000)")
    if not browser_ok:
        log("WARNING: browser-harness not available")
        log("Activate with: source ~/sandbox/browser-harness/venv/bin/activate")
        return
    
    log("Starting automation...")
    
    # Step 1: Register on RapidAPI
    log("\n--- Step 1: RapidAPI ---")
    register_rapidapi()
    
    log("\n--- Step 2: Publish API ---")
    publish_api()
    
    log("\n--- Step 3: Agentic Profiles ---")
    create_agentic_profiles()
    
    log("\n--- Step 4: GitHub Release ---")
    create_github_release()
    
    log("\n=== AUTOMATION COMPLETE ===")
    log("Check Chrome windows for any CAPTCHAs or confirmation dialogs")
    log("RapidAPI: Sign in / complete CAPTCHA, then API is published")
    log("Agentic profiles: Complete any remaining fields manually")

if __name__ == "__main__":
    main()
