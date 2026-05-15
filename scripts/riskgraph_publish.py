#!/usr/bin/env python3
"""RiskGraph Automation Suite - RapidAPI + Agentic Profiles"""

import subprocess, json, time, os, urllib.request

def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def bh(code):
    r = subprocess.run(["browser-harness"], input=code.encode(),
        capture_output=True, text=True, timeout=120)
    if r.returncode != 0: log(f"BH FAIL: {r.stderr.strip()[:100]}")
    return r.stdout.strip()

def check():
    log("Checking environment...")
    r = subprocess.run(["which", "browser-harness"], capture_output=True, text=True, timeout=5)
    if r.returncode != 0:
        log("ERROR: run 'source ~/sandbox/browser-harness/venv/bin/activate' first")
        return False
    try:
        r = urllib.request.urlopen("http://localhost:8000/", timeout=3)
        log("RiskGraph API: OK")
    except: log("RiskGraph API: unavailable (start Docker first)")
    return True

def run_browser(code):
    """Send Python code to browser-harness for execution."""
    log("Executing browser automation...")
    result = bh(code)
    for line in (result or "").split("\n"):
        if line.strip(): log(f"  {line[:100]}")
    return result

def step1_rapidapi_signup():
    log("Step 1: RapidAPI Signup")
    run_browser("""
import time
navigate("https://rapidapi.com/auth/signup")
time.sleep(5)
info = page_info()
print("Page:", info.get("url", "unknown")[:60])

# Try to fill signup form
for sel, val in [("#email", "riskgraph@proton.me"), ("#password", "AutoM8Risk2026")]:
    try:
        click(sel)
        type(sel, val)
    except Exception as e:
        print(f"Field {sel}: {e}")
print("Signup form filled - may need CAPTCHA")
""")

def step2_publish_api():
    log("Step 2: Publish RiskGraph API")
    run_browser("""
import time
navigate("https://rapidapi.com/developer/new-api")
time.sleep(5)
info = page_info()
print("Page:", info.get("url", "unknown")[:60])
print("Title:", info.get("title", "")[:60])

# Fill API details  
pairs = [
    ("#name, #api-name", "RiskGraph"),
    ("#description, #desc", "Credit score for open-source packages"),
    ("#base-url", "http://localhost:8000"),
    ("#pricing-url", "https://github.com/solosofi/riskgraph"),
]
for sel, val in pairs:
    for s in sel.split(","):
        s = s.strip()
        try:
            click(s); type(s, val); break
        except: pass

print("Fill endpoints in the Endpoints tab:")
print("  GET /api/v1/package-risk/{ecosystem}/{package}")
print("  POST /api/v1/scan")
print("  GET /")

print("Set pricing in Plans & Pricing tab:")
print("  Free: 100/day $0")
print("  Pro: 10K/day $49/mo")
print("  Enterprise: Unlimited $499/mo")
print("Publish manually when ready")
""")

def step3_agentic_profiles():
    log("Step 3: Agentic Economy Profiles")
    for name, url in [("Molt", "https://molt.bot"), ("ClawHub", "https://clawhub.com")]:
        result = run_browser(f"""
import time
navigate("{url}")
time.sleep(4)
info = page_info()
print("Visited {name}:", info.get("url", "unknown")[:50])
try:
    navigate("{url}/register")
    time.sleep(3)
    print("{name} register page loaded")
except:
    print("{name}: register link not found")
""")
        log(f"  {name}: done")

def verify():
    log("Verifying everything...")
    import urllib.request, json
    try:
        r = urllib.request.urlopen("http://localhost:8000/api/v1/package-risk/npm/express", timeout=5)
        d = json.loads(r.read().decode())
        log(f"API OK: express score={d['score']}")
    except Exception as e:
        log(f"API check: {e}")

def main():
    print("RiskGraph Automation Suite v1.0")
    print("=" * 40)
    if not check(): return
    step1_rapidapi_signup()
    step2_publish_api()
    step3_agentic_profiles()
    verify()
    print("Done! Check Chrome for CAPTCHAs/manual steps")

if __name__ == "__main__":
    main()
