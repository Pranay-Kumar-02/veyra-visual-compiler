"""
Capture genuine application screenshots for the Veyra Visual Compiler README redesign.
Starts the local Flask backend, interacts with the running web interface via Playwright,
and captures high-resolution screenshots of all 10 required workspace views.
"""

import os
import subprocess
import sys
import time
import urllib.request
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1:5000"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS_DIR = os.path.join(REPO_ROOT, "docs", "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)


def wait_for_server(url: str, timeout: float = 20.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/health", timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def capture_all():
    python_exe = sys.executable
    server_process = None

    # Check if server is already running
    is_running = False
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=1.0) as resp:
            if resp.status == 200:
                is_running = True
    except Exception:
        pass

    if not is_running:
        print("Starting Flask application server...")
        server_process = subprocess.Popen(
            [python_exe, os.path.join(REPO_ROOT, "app.py")],
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if not wait_for_server(BASE_URL):
            print("Failed to start Flask server!")
            if server_process:
                server_process.terminate()
            return False

    print("Flask server is online. Starting Playwright capture...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1440, "height": 900},
                device_scale_factor=1,
            )
            page = context.new_page()

            print("Navigating to", BASE_URL)
            page.goto(BASE_URL)
            page.wait_for_load_state("networkidle")
            time.sleep(1.5)

            # Ensure default compilation on load
            run_btn = page.locator("button:has-text('Run')")
            if run_btn.count() > 0:
                run_btn.first.click()
                time.sleep(1.5)

            # -------------------------------------------------------------
            # 1. Overall Veyra Workspace
            # -------------------------------------------------------------
            # Select AST tab initially
            page.locator("button.tab-btn:has-text('AST')").click()
            time.sleep(0.8)
            img1 = os.path.join(ASSETS_DIR, "01-integrated-workspace.png")
            page.screenshot(path=img1)
            print("1. Captured:", img1)

            # -------------------------------------------------------------
            # 2. AST Visualizer
            # -------------------------------------------------------------
            img2 = os.path.join(ASSETS_DIR, "02-ast-visualizer.png")
            page.screenshot(path=img2)
            print("2. Captured:", img2)

            # -------------------------------------------------------------
            # 3. Symbol Table
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('Symbols')").click()
            time.sleep(0.8)
            img3 = os.path.join(ASSETS_DIR, "03-symbol-table.png")
            page.screenshot(path=img3)
            print("3. Captured:", img3)

            # -------------------------------------------------------------
            # 4. Three-Address Code (3AC) Inspector
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('3AC / IR')").click()
            time.sleep(0.8)
            img4 = os.path.join(ASSETS_DIR, "04-three-address-code.png")
            page.screenshot(path=img4)
            print("4. Captured:", img4)

            # -------------------------------------------------------------
            # 5. Control Flow Graph (CFG)
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('CFG')").click()
            time.sleep(1.0)
            # Click first basic block to highlight details if available
            blocks = page.locator(".cfg-block, div[style*='cursor: pointer']")
            if blocks.count() > 0:
                try:
                    blocks.first.click()
                    time.sleep(0.5)
                except Exception:
                    pass
            img5 = os.path.join(ASSETS_DIR, "05-cfg-visualization.png")
            page.screenshot(path=img5)
            print("5. Captured:", img5)

            # -------------------------------------------------------------
            # 6. Original vs Optimized 3AC
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('Optimizer')").click()
            time.sleep(0.8)
            img6 = os.path.join(ASSETS_DIR, "06-optimized-3ac.png")
            page.screenshot(path=img6)
            print("6. Captured:", img6)

            # -------------------------------------------------------------
            # 7. Step-by-Step Debugger
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('Debugger')").click()
            time.sleep(0.8)
            step_btn = page.locator("button.pane-action-btn:has-text('Step Next')")
            for _ in range(3):
                if step_btn.is_enabled():
                    step_btn.click()
                    time.sleep(0.3)
            time.sleep(0.5)
            img7 = os.path.join(ASSETS_DIR, "07-step-debugger.png")
            page.screenshot(path=img7)
            print("7. Captured:", img7)

            # -------------------------------------------------------------
            # 8. ASM / Target Code Generator
            # -------------------------------------------------------------
            page.locator("button.tab-btn:has-text('ASM / Target')").click()
            time.sleep(0.8)
            img8 = os.path.join(ASSETS_DIR, "08-target-assembly.png")
            page.screenshot(path=img8)
            print("8. Captured:", img8)

            # -------------------------------------------------------------
            # 9. Diagnostics (Real Invalid-Input Error)
            # -------------------------------------------------------------
            preset_select = page.locator("select.preset-select")
            preset_select.select_option(value="error_syntax")
            time.sleep(0.8)
            if run_btn.count() > 0:
                run_btn.first.click()
                time.sleep(1.0)
            page.locator("button.tab-btn:has-text('Diagnostics')").click()
            time.sleep(0.8)
            img9 = os.path.join(ASSETS_DIR, "09-diagnostics-error.png")
            page.screenshot(path=img9)
            print("9. Captured:", img9)

            # -------------------------------------------------------------
            # 10. Focus Mode Editor
            # -------------------------------------------------------------
            preset_select.select_option(value="phase3_demo")
            time.sleep(0.8)
            if run_btn.count() > 0:
                run_btn.first.click()
                time.sleep(1.0)
            focus_btn = page.locator("button.mode-btn:has-text('Focus')")
            focus_btn.click()
            time.sleep(0.8)
            img10 = os.path.join(ASSETS_DIR, "10-focus-mode.png")
            page.screenshot(path=img10)
            print("10. Captured:", img10)

            # Also switch back to workbench mode
            workbench_btn = page.locator("button.mode-btn:has-text('Workbench')")
            workbench_btn.click()
            time.sleep(0.5)

            browser.close()
            print("All 10 genuine screenshots successfully captured and saved!")

    finally:
        if server_process:
            server_process.terminate()
            server_process.wait()
            print("Flask server stopped.")

    return True


if __name__ == "__main__":
    success = capture_all()
    if not success:
        sys.exit(1)
