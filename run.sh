#!/bin/bash
echo "========================================"
echo "  Mixpanel Bulk Event Replacer"
echo "========================================"
echo ""

CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

if [ ! -f "$CHROME_PATH" ]; then
    echo "[!] Chrome not found at $CHROME_PATH"
    echo "    Please install Google Chrome first."
    read -p "Press Enter to exit..."
    exit 1
fi

echo "[*] Closing any existing Chrome windows..."
pkill -f "Google Chrome" 2>/dev/null
sleep 2

echo "[*] Launching Chrome..."
"$CHROME_PATH" --remote-debugging-port=9222 --user-data-dir=/tmp/mixpanel-debug &
sleep 4

echo ""
echo "========================================"
echo " Chrome is open. Now:"
echo "  1. Log into Mixpanel"
echo "  2. Navigate to the dashboard you want to update"
echo "  3. Scroll down to load all report cards"
echo "  4. Come back here and press Enter"
echo "========================================"
echo ""
read -p "Press Enter when ready..."

echo ""
echo "[*] Running script..."
python3 replace_events.py
read -p "Press Enter to exit..."
