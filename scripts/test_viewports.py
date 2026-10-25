import time
from playwright.sync_api import sync_playwright

viewports = [(1920, 1080), (1440, 900), (1366, 768), (1024, 768)]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    
    # 1. Test responsive viewports in Focus mode
    for w, h in viewports:
        ctx = browser.new_context(viewport={"width": w, "height": h})
        page = ctx.new_page()
        page.goto("http://127.0.0.1:5000")
        page.wait_for_load_state("networkidle")
        
        # Switch to Focus mode
        page.locator("button.mode-btn:has-text('Focus')").click()
        time.sleep(0.5)
        
        # Verify Editor Box matches App Body Box width
        editor_box = page.locator(".pane-editor").bounding_box()
        body_box = page.locator(".app-body").bounding_box()
        sw = page.evaluate("() => document.body.scrollWidth")
        iw = page.evaluate("() => window.innerWidth")
        overflow = sw > iw
        
        print(f"Viewport {w}x{h} Focus Mode: Editor Width={editor_box['width']}, Body Width={body_box['width']}, Overflow={overflow}")
        assert abs(editor_box["width"] - body_box["width"]) < 2, f"Editor width ({editor_box['width']}) does not fill body width ({body_box['width']}) at {w}x{h}"
        assert not overflow, f"Unexpected horizontal overflow at {w}x{h}"

    # 2. Test switching between Workbench, Pipeline Studio, and Focus mode
    ctx = browser.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.goto("http://127.0.0.1:5000")
    page.wait_for_load_state("networkidle")
    
    # Switch to Focus
    page.locator("button.mode-btn:has-text('Focus')").click()
    time.sleep(0.5)
    page.screenshot(path="evidence/08_focus_mode.png")
    page.screenshot(path="docs/assets/08_focus_mode.png")
    print("Saved genuine Focus mode screenshot to evidence/08_focus_mode.png and docs/assets/08_focus_mode.png")
    
    # Switch to Pipeline Studio
    page.locator("button.mode-btn:has-text('Pipeline Studio')").click()
    time.sleep(0.5)
    assert page.locator(".spatial-studio-container").is_visible(), "Pipeline studio did not mount"
    
    # Switch to Workbench
    page.locator("button.mode-btn:has-text('Workbench')").click()
    time.sleep(0.5)
    assert page.locator(".pane-inspector").is_visible(), "Workbench inspector did not mount"
    
    # Switch back to Focus
    page.locator("button.mode-btn:has-text('Focus')").click()
    time.sleep(0.5)
    assert not page.locator(".pane-inspector").is_visible(), "Workbench inspector should be hidden in focus mode"
    editor_box = page.locator(".pane-editor").bounding_box()
    assert abs(editor_box["width"] - 1440) < 2, "Editor did not re-expand to 100% on returning to Focus mode"

    # Test typing and compilation in Focus mode
    textarea = page.locator("textarea.editor-textarea")
    textarea.fill("let total = 100;\nprint(total);")
    time.sleep(0.3)
    page.locator("button:has-text('Run')").click()
    time.sleep(1)
    status_pill = page.locator(".status-pill.success")
    assert status_pill.is_visible(), "Compilation failed in focus mode"
    print("Compilation and editing verified in Focus mode!")

    browser.close()
    print("All Focus mode verification checks passed successfully!")
