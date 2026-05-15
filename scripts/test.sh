#!/usr/bin/env bash
# Test that browser-harness + RiskGraph work
echo "=== RiskGraph Test Suite ==="
echo ""

# 1. Test browser-harness
echo "--- Browser-Harness ---"
if command -v browser-harness &>/dev/null; then
    echo "  binary: FOUND"
    browser-harness --doctor 2>&1 | head -10
else
    echo "  binary: NOT FOUND"
    echo "  Activate venv: source ~/sandbox/browser-harness/venv/bin/activate"
fi

echo ""
echo "--- RiskGraph API ---"
curl -s http://localhost:8000/api/v1/package-risk/npm/lodash 2>&1 | head -1

echo ""
echo "--- Quick Score Test ---"
curl -s http://localhost:8000/api/v1/package-risk/npm/is-even 2>&1
echo ""

echo ""
echo "=== Browser test: type this ==="
echo 'browser-harness <<'"'"'PY'"'"'
print(page_info())
PY'
