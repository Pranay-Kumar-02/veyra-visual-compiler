"""
Automated genuine evidence screenshot capture script for Veyra Visual Compiler Review 3.
Captures real, pixel-perfect screenshots of all Review 3 features running on http://127.0.0.1:5000.
"""

import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
EVIDENCE_DIR = os.path.join(os.path.dirname(__file__), "..", "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)

ARTIFACT_DIR = r"C:\Users\PRANAY KUMAR\.gemini\antigravity-ide\brain\0c366979-28d5-46c6-8503-a331363e9a2f"
if os.path.exists(ARTIFACT_DIR):
    os.makedirs(os.path.join(ARTIFACT_DIR, "evidence"), exist_ok=True)


def save_screenshot(page, filename, description):
    path1 = os.path.join(EVIDENCE_DIR, filename)
    page.screenshot(path=path1, full_page=False)
    print(f"Captured: {path1} ({description})")
    if os.path.exists(ARTIFACT_DIR):
        path2 = os.path.join(ARTIFACT_DIR, "evidence", filename)
        page.screenshot(path=path2, full_page=False)


def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Set desktop resolution suitable for clean presentation
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        print("Navigating to application at", BASE_URL)
        page.goto(BASE_URL)
        page.wait_for_load_state("networkidle")
        time.sleep(2)

        # ---------------------------------------------------------------------
        # 1. Integrated Workspace (AST view on load with default phase3_demo)
        # ---------------------------------------------------------------------
        # Ensure compiled
        page.locator("button:has-text('Run')").click()
        time.sleep(1.5)
        # Select AST tab
        page.locator("button.tab-btn:has-text('AST')").click()
        time.sleep(0.5)
        save_screenshot(page, "01_integrated_workspace.png", "Integrated Veyra Workspace with AST")

        # ---------------------------------------------------------------------
        # 2. CFG Visualization for a conditional program
        # ---------------------------------------------------------------------
        page.locator("button.tab-btn:has-text('CFG')").click()
        time.sleep(1)
        # Select first block B0 to show inspector
        blocks = page.locator("div[style*='cursor: pointer']")
        if blocks.count() > 0:
            blocks.first.click()
            time.sleep(0.5)
        save_screenshot(page, "02_cfg_visualization.png", "CFG Visualization for Conditional Program")

        # ---------------------------------------------------------------------
        # 3. Original versus Optimized 3AC
        # ---------------------------------------------------------------------
        page.locator("button.tab-btn:has-text('Optimizer')").click()
        time.sleep(1)
        save_screenshot(page, "03_original_vs_optimized_3ac.png", "Original vs Optimized 3AC Comparison")

        # ---------------------------------------------------------------------
        # 4. Step-by-Step Debugger with real runtime state
        # ---------------------------------------------------------------------
        page.locator("button.tab-btn:has-text('Debugger')").click()
        time.sleep(1)
        # Step forward 3 times to be inside execution with variables populated
        step_btn = page.locator("button.pane-action-btn:has-text('Step Next')")
        for _ in range(3):
            if step_btn.is_enabled():
                step_btn.click()
                time.sleep(0.4)
        time.sleep(0.5)
        save_screenshot(page, "04_step_debugger.png", "Step-by-Step Debugger Runtime State")

        # ---------------------------------------------------------------------
        # 5. Genuine Invalid-Input Diagnostic
        # ---------------------------------------------------------------------
        # Switch preset to error_syntax or type invalid code
        preset_select = page.locator("select.preset-select")
        preset_select.select_option(value="error_syntax")
        time.sleep(1)
        page.locator("button:has-text('Run')").click()
        time.sleep(1)
        # Select Diagnostics tab
        page.locator("button.tab-btn:has-text('Diagnostics')").click()
        time.sleep(0.5)
        save_screenshot(page, "05_invalid_input_diagnostic.png", "Genuine Invalid-Input Diagnostic")

        # ---------------------------------------------------------------------
        # 6. Test results visualization / workspace
        # ---------------------------------------------------------------------
        # Navigate back to Phase 3 Demo, run, show 3AC/IR tab
        preset_select.select_option(value="phase3_demo")
        time.sleep(1)
        page.locator("button:has-text('Run')").click()
        time.sleep(1)
        page.locator("button.tab-btn:has-text('3AC / IR')").click()
        time.sleep(0.5)
        save_screenshot(page, "06_three_address_code.png", "Three-Address Code Generation Inspection")

        browser.close()
        print("All genuine screenshots captured successfully!")


if __name__ == "__main__":
    run()
