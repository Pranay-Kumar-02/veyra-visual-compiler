import time
from playwright.sync_api import sync_playwright

viewports = [(1920, 1080), (1440, 900), (1366, 768), (1024, 768)]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for w, h in viewports:
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        page.goto("http://127.0.0.1:5000")
        page.wait_for_load_state("networkidle")
        page.locator("button:has-text('Run')").click()
        time.sleep(1)

        for tab_name in ["Debugger", "Optimizer", "CFG", "AST", "Diagnostics"]:
            page.locator(f"button.tab-btn:has-text('{tab_name}')").click()
            time.sleep(0.3)
            sw = page.evaluate("() => document.body.scrollWidth")
            iw = page.evaluate("() => window.innerWidth")
            overflow = sw > iw
            print(f"Viewport {w}x{h} [{tab_name}]: scrollWidth={sw}, innerWidth={iw}, has_overflow={overflow}")
            assert not overflow, f"Unexpected horizontal overflow at {w}x{h} in {tab_name}"

    browser.close()
    print("All viewports verified without horizontal overflow!")
