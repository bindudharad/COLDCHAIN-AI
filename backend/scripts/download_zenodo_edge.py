"""Download Zenodo Hohenheim cold-room dataset using Microsoft Edge via Playwright."""
import os
import zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright

def download_zenodo_data():
    dest_dir = Path("Datasets/zenodo_hohenheim")
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    print("Launching Microsoft Edge to download Zenodo cold-room dataset...")
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()
        
        print("Navigating to https://zenodo.org/records/15130001 ...")
        page.goto("https://zenodo.org/records/15130001", wait_until="networkidle", timeout=30000)
        
        # Files to download
        files_to_download = ["Preprocessed.zip", "Raw.zip"]
        
        for fname in files_to_download:
            target_file = dest_dir / fname
            if target_file.exists() and target_file.stat().st_size > 1000:
                print(f"[+] {fname} already exists ({target_file.stat().st_size:,} bytes). Skipping.")
                continue
                
            print(f"Locating download link for {fname}...")
            # Locator for link containing the filename
            link = page.locator(f"a[href*='{fname}']").first
            if link.count() == 0:
                print(f"[-] Could not find download link for {fname}")
                continue
                
            href = link.get_attribute("href")
            print(f"Found link: {href}. Triggering download...")
            
            try:
                with page.expect_download(timeout=120000) as download_info:
                    link.click()
                download = download_info.value
                print(f"Saving to {target_file}...")
                download.save_as(str(target_file))
                print(f"[+] Download complete: {fname} ({target_file.stat().st_size:,} bytes)")
                
                # If Preprocessed.zip, extract it
                if fname == "Preprocessed.zip":
                    extract_dir = dest_dir / "preprocessed_extracted"
                    extract_dir.mkdir(parents=True, exist_ok=True)
                    print(f"Extracting {fname} to {extract_dir}...")
                    with zipfile.ZipFile(target_file, "r") as zf:
                        zf.extractall(extract_dir)
                    extracted_files = list(extract_dir.glob("*.csv"))
                    print(f"[+] Extracted {len(extracted_files)} CSV files:")
                    for ef in extracted_files:
                        print(f"    - {ef.name} ({ef.stat().st_size:,} bytes)")
            except Exception as e:
                print(f"[-] Download failed for {fname}: {e}")
                
        browser.close()

if __name__ == "__main__":
    download_zenodo_data()
