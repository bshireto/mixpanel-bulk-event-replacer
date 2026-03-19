"""
Mixpanel Bulk Event Replacer
-----------------------------
Connects to an existing Chrome session and replaces any event or breakdown
across all reports on a Mixpanel dashboard — in bulk, automatically.

Built by Barak Shireto, Product Marketing Manager @ Investing.com

Setup (once):
  Run install.bat (Windows) or install.sh (Mac)

Usage:
  Run run.bat (Windows) or run.sh (Mac)
"""

import asyncio
import sys
import re
import csv
import os
from datetime import datetime
from playwright.async_api import async_playwright

CDP_URL = "http://127.0.0.1:9222"


async def set_react_input(page, selector, value):
    """Set an input value in a React-controlled input using the native setter."""
    await page.evaluate("""([selector, value]) => {
        const input = document.querySelector(selector);
        if (!input) return false;
        const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
        setter.call(input, value);
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
    }""", [selector, value])


async def find_template_event_elements(page, template_event):
    """Find .block-menu-label elements in type-events blocks matching the template event."""
    return await page.evaluate("""(matchText) => {
        const scope = document.querySelectorAll(
            '.mp-query-block.type-events .block-menu-label, .mp-query-block-selector .block-menu-label'
        );
        return [...scope].filter(el =>
            el.textContent.trim().toLowerCase().startsWith(matchText)
        ).length;
    }""", template_event[:25].lower())


async def click_template_event(page, template_event):
    """Click the first matching template event label."""
    await page.evaluate("""(matchText) => {
        const scope = document.querySelectorAll(
            '.mp-query-block.type-events .block-menu-label, .mp-query-block-selector .block-menu-label'
        );
        const el = [...scope].find(el =>
            el.textContent.trim().toLowerCase().startsWith(matchText)
        );
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        ['mouseover','mouseenter','mousedown','mouseup','click'].forEach(type =>
            el.dispatchEvent(new MouseEvent(type, {
                bubbles: true, cancelable: true, view: window,
                clientX: cx, clientY: cy
            }))
        );
    }""", template_event[:25].lower())


async def find_breakdown_elements(page, breakdown_from):
    """Find .block-menu-label elements in type-properties blocks matching breakdown_from."""
    return await page.evaluate("""(matchText) => {
        const scope = document.querySelectorAll('.mp-query-block.type-properties .block-menu-label');
        return [...scope].filter(el =>
            el.textContent.trim().toLowerCase().includes(matchText)
        ).length;
    }""", breakdown_from.lower())


async def click_breakdown_element(page, breakdown_from):
    """Click the first matching breakdown label."""
    await page.evaluate("""(matchText) => {
        const scope = document.querySelectorAll('.mp-query-block.type-properties .block-menu-label');
        const el = [...scope].find(el =>
            el.textContent.trim().toLowerCase().includes(matchText)
        );
        if (!el) return;
        const rect = el.getBoundingClientRect();
        const cx = rect.left + rect.width / 2;
        const cy = rect.top + rect.height / 2;
        ['mouseover','mouseenter','mousedown','mouseup','click'].forEach(type =>
            el.dispatchEvent(new MouseEvent(type, {
                bubbles: true, cancelable: true, view: window,
                clientX: cx, clientY: cy
            }))
        );
    }""", breakdown_from.lower())


async def replace_breakdowns_in_report(page, breakdown_from, breakdown_to):
    """Replace breakdown sub-property with the target property."""
    count = await find_breakdown_elements(page, breakdown_from)
    if count == 0:
        return {"replaced": 0}

    print(f"  Found {count} breakdown(s) to replace")
    replaced = 0
    consecutive_failures = 0
    max_consecutive_failures = 4

    while consecutive_failures < max_consecutive_failures:
        remaining = await find_breakdown_elements(page, breakdown_from)
        if remaining == 0:
            break

        print(f"  Clicking breakdown ({remaining} remaining)...")
        await click_breakdown_element(page, breakdown_from)
        await asyncio.sleep(1)

        clicked = await select_event_from_shadow_dom(page, breakdown_to)
        if clicked:
            replaced += 1
            consecutive_failures = 0
            print(f"  ✓ Replaced breakdown occurrence {replaced}")
            await asyncio.sleep(0.8)
        else:
            consecutive_failures += 1
            print(f"  Could not find '{breakdown_to}' in dropdown, retrying... ({consecutive_failures}/{max_consecutive_failures})")
            await asyncio.sleep(0.5)

    return {"replaced": replaced}


async def select_event_from_shadow_dom(page, new_event):
    """Click the result in the mp-items-menu shadow DOM."""
    return await page.evaluate("""(newEvent) => {
        const menus = document.querySelectorAll('mp-items-menu');
        for (const menu of menus) {
            const shadow = menu.shadowRoot;
            if (!shadow) continue;
            const rect = menu.getBoundingClientRect();
            if (rect.width === 0 || rect.height === 0) continue;
            let item = shadow.querySelector(`li[aria-label="${newEvent}"]`);
            if (!item) {
                const items = shadow.querySelectorAll('li[role="listitem"]');
                item = [...items].find(li => li.textContent.trim() === newEvent);
            }
            if (item) { item.click(); return true; }
        }
        return false;
    }""", new_event)


async def click_save(page):
    """Click the save button through shadow DOM layers."""
    return await page.evaluate("""
        (function() {
            const container = document.querySelector('mp-boards-save-button');
            const btn = container?.shadowRoot?.querySelector('mp-button.save');
            if (btn && !btn.hasAttribute('disabled')) {
                btn.click();
                return true;
            }
            return false;
        })()
    """)


async def wait_for_saved(page, timeout=15):
    """Wait until the save button shows 'Saved' (disabled state)."""
    for _ in range(timeout * 5):
        saved = await page.evaluate("""
            document.querySelector('mp-boards-save-button')
                ?.shadowRoot?.querySelector('mp-button.save')
                ?.hasAttribute('disabled') || false
        """)
        if saved:
            return True
        await asyncio.sleep(0.2)
    return False


async def wait_for_metrics_loaded(page, timeout=25):
    """Wait for the metrics panel to load — tries multiple selectors."""
    selectors = [
        "div.mp-query-entry-section-body",
        ".mp-query-block",
        ".block-menu-label",
        "[class*='query-builder']",
    ]
    for selector in selectors:
        try:
            await page.wait_for_selector(selector, timeout=timeout * 1000)
            await asyncio.sleep(2)
            return True
        except Exception:
            continue
    return False


async def replace_events_in_report(page, template_event, new_event, report_name):
    """Replace all instances of template_event with new_event in the current report."""
    print(f"  Waiting for metrics to load...")

    if not await wait_for_metrics_loaded(page):
        return {"success": False, "message": "Metrics panel did not load in time"}

    count = await find_template_event_elements(page, template_event)
    if count == 0:
        print(f"  No template events found — skipping")
        return {"success": True, "replaced": 0}

    print(f"  Found {count} template event(s) to replace")
    await asyncio.sleep(2)
    replaced = 0
    consecutive_failures = 0
    max_consecutive_failures = 5

    while consecutive_failures < max_consecutive_failures:
        remaining = await find_template_event_elements(page, template_event)
        if remaining == 0:
            break

        print(f"  Clicking template event ({remaining} remaining)...")
        await click_template_event(page, template_event)
        await asyncio.sleep(0.8)

        try:
            await page.wait_for_selector('input[placeholder*="Search Events"]', timeout=5000)
            consecutive_failures = 0
        except Exception:
            consecutive_failures += 1
            print(f"  Search panel didn't open, retrying... ({consecutive_failures}/{max_consecutive_failures})")
            continue

        await set_react_input(page, 'input[placeholder*="Search Events"]', new_event)
        print(f"  Typed new event name, waiting for results...")
        await asyncio.sleep(3)

        clicked = await select_event_from_shadow_dom(page, new_event)
        if clicked:
            replaced += 1
            consecutive_failures = 0
            print(f"  ✓ Replaced occurrence {replaced}")
            await asyncio.sleep(0.8)
        else:
            consecutive_failures += 1
            print(f"  Could not find result in dropdown, retrying... ({consecutive_failures}/{max_consecutive_failures})")
            await asyncio.sleep(0.5)

    if replaced == 0:
        return {"success": False, "replaced": 0, "message": "Could not select new event from search results"}

    return {"success": True, "replaced": replaced}


async def main():
    replace_from = input("Replace (event or breakdown): ").strip().strip('\u202a\u202c\u200b')
    replace_to = input("Replace with: ").strip().strip('\u202a\u202c\u200b')

    if not replace_from or not replace_to:
        print("Both fields required.")
        sys.exit(1)

    async with async_playwright() as p:
        print(f"\nConnecting to Chrome on {CDP_URL}...")
        try:
            browser = await p.chromium.connect_over_cdp(CDP_URL)
        except Exception as e:
            print(f"ERROR: Could not connect to Chrome.\n{e}")
            print('\nMake sure Chrome is running via run.bat (Windows) or run.sh (Mac)')
            sys.exit(1)

        context = browser.contexts[0]
        pages = context.pages
        dashboard_page = None
        for pg in pages:
            if "mixpanel.com" in pg.url and "/app/boards" in pg.url:
                dashboard_page = pg
                break

        if not dashboard_page:
            print("ERROR: No Mixpanel dashboard tab found.")
            print("Navigate to a Mixpanel dashboard in Chrome, then run again.")
            sys.exit(1)

        print(f"Found dashboard: {dashboard_page.url}")

        dashboard_id_match = re.search(r'[#&]id=(\d+)', dashboard_page.url)
        if not dashboard_id_match:
            print("ERROR: Could not find dashboard ID in URL.")
            sys.exit(1)

        dashboard_id = dashboard_id_match.group(1)
        base_path = dashboard_page.url.split("#")[0]
        print(f"Dashboard ID: {dashboard_id}")

        print("Extracting report links...")
        reports = await dashboard_page.evaluate("""
            (function() {
                const REPORT_PATTERN = /#report\\/(\\d+)/;
                const seen = new Set();
                const results = [];
                document.querySelectorAll('a[href]').forEach(anchor => {
                    const href = anchor.getAttribute('href') || '';
                    const match = href.match(REPORT_PATTERN);
                    if (!match) return;
                    const reportId = match[1];
                    if (seen.has(reportId)) return;
                    seen.add(reportId);
                    const fullText = anchor.innerText?.trim() || '';
                    const name = fullText.split('\\n').map(l => l.trim()).find(l => l.length > 0 && l.length < 200) || `report_${reportId}`;
                    results.push({ name, reportId });
                });
                return results;
            })()
        """)

        print(f"Found {len(reports)} reports\n")

        log = []
        for i, report in enumerate(reports):
            report_name = report['name']
            report_id = report['reportId']
            print(f"[{i+1}/{len(reports)}] {report_name}")

            editor_url = f"{base_path}#id={dashboard_id}&editor-card-id=%22report-{report_id}%22"
            await dashboard_page.goto(editor_url, wait_until="domcontentloaded")
            await dashboard_page.reload(wait_until="domcontentloaded")
            await asyncio.sleep(1)

            deadline = asyncio.get_event_loop().time() + 15
            while asyncio.get_event_loop().time() < deadline:
                if f"report-{report_id}" in dashboard_page.url:
                    break
                await asyncio.sleep(0.3)

            result = await replace_events_in_report(dashboard_page, replace_from, replace_to, report_name)
            bd_result = await replace_breakdowns_in_report(dashboard_page, replace_from, replace_to)
            if bd_result['replaced'] > 0:
                print(f"  ✓ Replaced {bd_result['replaced']} breakdown(s)")

            total_replaced = result.get('replaced', 0) + bd_result.get('replaced', 0)

            if total_replaced > 0:
                print(f"  Waiting for Save button to activate...")
                for _ in range(40):
                    is_active = await dashboard_page.evaluate("""
                        !document.querySelector('mp-boards-save-button')
                            ?.shadowRoot?.querySelector('mp-button.save')
                            ?.hasAttribute('disabled')
                    """)
                    if is_active:
                        break
                    await asyncio.sleep(0.2)
                await dashboard_page.evaluate("window.focus()")
                await asyncio.sleep(0.3)
                print(f"  Saving...")
                await click_save(dashboard_page)
                saved = await wait_for_saved(dashboard_page)
                print(f"  {'✓ Saved' if saved else '⚠ Save confirmation not detected'}")

            status = f"✓ replaced {total_replaced}" if total_replaced > 0 else f"✗ {result.get('message', 'nothing replaced')}"
            print(f"  → {status}\n")
            log.append({
                "report": report_name,
                "report_id": report_id,
                "result": status,
                "replace_from": replace_from,
                "replace_to": replace_to
            })

            await dashboard_page.goto(f"{base_path}#id={dashboard_id}", wait_until="domcontentloaded")
            await asyncio.sleep(1.5)

        # Save log next to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(script_dir, f"mp_replacement_log_{timestamp}.csv")
        with open(log_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["report", "report_id", "result", "replace_from", "replace_to"])
            writer.writeheader()
            writer.writerows(log)

        print(f"Done! Log saved to {log_file}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    input("\nPress Enter to exit...")
