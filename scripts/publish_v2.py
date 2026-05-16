#!/usr/bin/env python3
"""RiskGraph Automation v2 - opens Chrome, handles CAPTCHA"""
import subprocess, time, sys, urllib.request, json

def log(m): print(f"  [{time.strftime('%H:%M:%S')}] {m}", flush=True)

def bh(code):
    r = subprocess.run(["browser-harness"], input=code.encode(), capture_output=True, text=True, timeout=180)
    if r.returncode != 0: log(f"BH: {r.stderr.strip()[:80]}")
    return r.stdout.strip()

log("Activate venv: source ~/sandbox/browser-harness/venv/bin/activate")
log("")
log("=== STEP 1: RAPIDAPI SIGNUP ===")
print("\nOpen RapidAPI signup. Fill CAPTCHA when prompted (30s wait).")

bh("""import time, urllib.request
navigate("https://rapidapi.com/")
time.sleep(5)
for btn in page_info().get("buttons", []):
    if "Sign Up" in str(btn):
        try: click(btn); time.sleep(3); break
        except: pass
navigate("https://rapidapi.com/auth/sign-up")
time.sleep(4)
for sel, val in [("username","riskgraph_io"),("email","riskgraph@proton.me"),("password","R1skGr4ph!@2026"),("confirmPassword","R1skGr4ph!@2026")]:
    try:
        el = page_info().get_element("#"+sel)
        click("#"+sel)
        type("#"+sel, val)
        time.sleep(0.3)
    except: pass
print("Form filled. You have 30s to solve CAPTCHA...")
time.sleep(30)
try:
    click("button[type=submit]")
    print("Submitted")
except: print("Submit failed")
"""+"")

log("=== STEP 2: PUBLISH API ===")
bh("""import time
navigate("https://rapidapi.com/developer/new-api")
time.sleep(5)
print("Fill API details manually, then publish.")
time.sleep(60)
"""+"")

log("=== STEP 3: AGENTIC PROFILES ===")
for name, url in [("Molt","https://molt.bot"),("ClawHub","https://clawhub.com")]:
    bh("""import time
    navigate("""+url+""")
    time.sleep(4)
    print("Opened", """+name+""")
    """+"")
    log(f"  {name}: opened")

log("=== DONE ===")