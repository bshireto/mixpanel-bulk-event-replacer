# Mixpanel Bulk Event Replacer

Automatically replace any event or breakdown across every report on a Mixpanel dashboard — in one run, no manual editing.

Built by [Barak Shireto]([https://www.linkedin.com/in/barakshireto/](https://www.linkedin.com/in/barak-shireto-699b253b/)), Product Marketing Manager @ [Investing.com](https://www.investing.com)

---

## What it does

When you duplicate a template dashboard in Mixpanel, every report still points to the original template event. Updating them one by one is tedious and error-prone — especially on dashboards with 20, 40, or 100+ reports.

This tool connects to your open Chrome session, opens each report editor automatically, finds every instance of the event or breakdown you want to replace, swaps it with the new value, and saves — all without you touching anything.

**It handles:**
- Event replacements in Metrics
- Breakdown replacements
- Both in a single run
- Skips reports that don't contain the target value
- Saves a log CSV when done so you can verify what changed

---

## Requirements

- Google Chrome
- Python 3.8+
- Windows or Mac

---

## Setup (run once)

**Windows:** Double-click `install.bat`

**Mac:**
```bash
chmod +x install.sh && ./install.sh
```

This installs Python (if needed), Playwright, and Chromium automatically.

---

## How to use

**Windows:** Double-click `run.bat`

**Mac:**
```bash
chmod +x run.sh && ./run.sh
```

### Steps

1. Chrome opens automatically
2. Log into Mixpanel and navigate to the dashboard you want to update
3. Scroll down to load all report cards on the dashboard
4. Come back to the terminal and press **Enter**
5. When prompted, enter:
   - **Replace:** the event or breakdown value to find
   - **Replace with:** the new value
6. The script runs through every report automatically
7. A log CSV is saved in the same folder when done

### Example

```
Replace (event or breakdown): Web Desktop · Pricing Page · Swap plans · V1 · Feb 09, 2026 · Experiment
Replace with: Marketing Experiment Template
```

---

## Tips

- You can minimize Chrome or switch tabs while the script runs — it won't be affected
- Don't navigate the Mixpanel dashboard tab manually while the script is running
- If a report fails, just run the script again — already-updated reports are automatically skipped
- To replace a breakdown sub-property (e.g. `variant` inside `uiTemplate ▸ variant`), enter just the sub-property name as the "Replace" value

---

## Output

A log file (`mp_replacement_log_YYYYMMDD_HHMMSS.csv`) is saved in the same folder as the script after each run. It lists every report processed, how many replacements were made, and whether it succeeded.

---
