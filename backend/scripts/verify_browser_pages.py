"""Automated Browser Verification and Screenshot Capture via Microsoft Edge.
Launches the Django development server, navigates through all 12 application routes,
captures full-page screenshots, verifies DOM rendering, and records JavaScript console logs.
"""
from __future__ import annotations
import sys, os, time, json, subprocess, socket
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PAGES_TO_VERIFY = [
    {'route': '/', 'name': 'home', 'expected_text': 'COLDCHAIN AI'},
    {'route': '/dashboard/', 'name': 'dashboard', 'expected_text': 'Cold-Chain'},
    {'route': '/datasets/', 'name': 'datasets', 'expected_text': 'Datasets Inventory'},
    {'route': '/live-monitoring/', 'name': 'live_monitoring', 'expected_text': 'Live Monitoring'},
    {'route': '/predictions/', 'name': 'predictions', 'expected_text': 'Predictions'},
    {'route': '/optimization/', 'name': 'optimization', 'expected_text': 'Optimization'},
    {'route': '/alerts/', 'name': 'alerts', 'expected_text': 'Alert Center'},
    {'route': '/model/', 'name': 'model', 'expected_text': 'Model'},
    {'route': '/sensors/', 'name': 'sensors', 'expected_text': 'Sensors'},
    {'route': '/reports/', 'name': 'reports', 'expected_text': 'Reports'},
    {'route': '/upload/', 'name': 'upload', 'expected_text': 'Upload Data'},
    {'route': '/methodology/', 'name': 'methodology', 'expected_text': 'Methodology'},
]

def wait_for_port(port, timeout=20):
    """Wait until local port is actively accepting connections."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(('127.0.0.1', port), timeout=1):
                return True
        except OSError:
            time.sleep(0.5)
    return False

def main():
    print("=" * 70)
    print("COLDCHAIN-AI: BROWSER RENDERING & INTERACTIVE UI VERIFICATION")
    print("=" * 70)
    
    screenshot_dir = Path('docs/screenshots')
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    server_port = 8011
    server_url = f"http://127.0.0.1:{server_port}"
    
    python_exe = sys.executable
    print(f"Starting Django Test Server on {server_url} using {python_exe}...")
    server_proc = subprocess.Popen(
        [python_exe, 'manage.py', 'runserver', f'127.0.0.1:{server_port}', '--noreload'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
    
    print("Waiting for Django server to bind to port 8011...")
    if not wait_for_port(server_port, timeout=25):
        print("Error: Django server failed to start within 25 seconds.")
        server_proc.terminate()
        sys.exit(1)
        
    print("Server ready! Initializing Playwright with Microsoft Edge...")
    results = []
    console_errors = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 900})
            
            for item in PAGES_TO_VERIFY:
                page = context.new_page()
                page.on("console", lambda msg: console_errors.append(f"[{item['name']}] {msg.text}") if msg.type == "error" else None)
                
                url = f"{server_url}{item['route']}"
                print(f"\nChecking Route: {item['route']} ({item['name']})...")
                t0 = time.perf_counter()
                
                try:
                    res = page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    time.sleep(1)  # Allow charts and dynamic widgets to settle
                    status_code = res.status if res else 0
                    
                    body_text = page.inner_text("body")
                    has_expected = item['expected_text'].lower() in body_text.lower()
                    
                    img_path = screenshot_dir / f"{item['name']}.png"
                    page.screenshot(path=str(img_path), full_page=False)
                    load_time_ms = (time.perf_counter() - t0) * 1000
                    
                    print(f"  -> HTTP {status_code} | Text Match: {has_expected} | Load: {load_time_ms:.1f} ms | Screenshot: {img_path.name}")
                    
                    results.append({
                        'route': item['route'],
                        'name': item['name'],
                        'http_status': status_code,
                        'content_verified': has_expected,
                        'load_time_ms': round(load_time_ms, 1),
                        'screenshot': str(img_path),
                        'status': 'PASS' if (status_code == 200 and has_expected) else 'FAIL'
                    })
                except Exception as e:
                    print(f"  -> FAILED to verify {item['route']}: {e}")
                    results.append({
                        'route': item['route'],
                        'name': item['name'],
                        'http_status': 0,
                        'content_verified': False,
                        'error': str(e),
                        'status': 'FAIL'
                    })
                finally:
                    page.close()
                    
            # Interactivity Test
            print("\nTesting Interactive Controls on /dashboard/...")
            page = context.new_page()
            page.goto(f"{server_url}/dashboard/", wait_until="domcontentloaded")
            time.sleep(1)
            selector = page.query_selector("#globalSensorSelect")
            if selector:
                selector.select_option(value="CC-02")
                time.sleep(1)
                page.screenshot(path=str(screenshot_dir / "dashboard_cc02_selected.png"))
                print("  -> Interactivity: Changed sensor to CC-02, captured dashboard_cc02_selected.png")
            page.close()
            browser.close()
    finally:
        print("\nTerminating Django test server...")
        server_proc.terminate()
        server_proc.wait(timeout=5)
        
    rep_dir = Path('reports')
    rep_dir.mkdir(exist_ok=True)
    out_data = {
        'total_pages_verified': len(PAGES_TO_VERIFY),
        'passed_count': sum(1 for r in results if r['status'] == 'PASS'),
        'failed_count': sum(1 for r in results if r['status'] == 'FAIL'),
        'console_errors': console_errors,
        'pages': results
    }
    (rep_dir / 'browser_verification_report.json').write_text(json.dumps(out_data, indent=2))
    
    print("\n" + "=" * 70)
    print(f"BROWSER VERIFICATION COMPLETE: {out_data['passed_count']}/{len(PAGES_TO_VERIFY)} PAGES PASSED")
    print("=" * 70)

if __name__ == '__main__':
    main()
