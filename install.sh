#!/bin/bash
echo "========================================"
echo "  Mixpanel Bulk Event Replacer - Setup"
echo "========================================"
echo ""

# Check if Python is installed
if command -v python3 &>/dev/null; then
    echo "[OK] Python is already installed."
else
    echo "[!] Python not found. Installing Python via Homebrew..."
    if ! command -v brew &>/dev/null; then
        echo "[*] Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    brew install python3
    echo "[OK] Python installed."
fi

echo ""
echo "[*] Installing Playwright..."
pip3 install playwright
echo "[OK] Playwright installed."

echo ""
echo "[*] Installing Chromium browser..."
playwright install chromium
echo "[OK] Chromium installed."

echo ""
echo "========================================"
echo "  Setup complete! Run ./run.sh to start."
echo "========================================"
