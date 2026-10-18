"""Comprehensive runtime validator for COLDCHAIN AI.
Tests every page render, verifies JavaScript syntax, inspects data bindings, and checks API endpoints.
"""
import os
import sys
import re
import json
import subprocess
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

from django.test import Client

def main():
    print("=" * 60)
    print("COLDCHAIN AI RUNTIME VALIDATOR")
    print("=" * 60)
    
    c = Client()
    
    # 1. Page routes
    pages = [
        '/',
        '/dashboard/',
        '/live-monitoring/',
        '/predictions/',
        '/optimization/',
        '/alerts/',
        '/model/',
        '/sensors/',
        '/reports/',
        '/upload/',
        '/methodology/',
    ]
    
    total_scripts = 0
    errors = []
    
    for p in pages:
        res = c.get(p)
        if res.status_code != 200:
            errors.append(f"Page {p} returned status {res.status_code}")
            continue
            
        html = res.content.decode('utf-8')
        
        # Check for unhandled template errors or undefined / NaN in values
        nan_matches = re.findall(r'>\s*NaN\s*<', html)
        if nan_matches:
            errors.append(f"Page {p} rendered raw NaN in HTML text")
            
        # Check JavaScript syntax
        scripts = re.findall(r'<script>(.*?)</script>', html, re.DOTALL)
        for idx, s in enumerate(scripts):
            total_scripts += 1
            node_proc = subprocess.run(
                ['node', '--check'],
                input=s.encode('utf-8'),
                capture_output=True
            )
            if node_proc.returncode != 0:
                err_msg = node_proc.stderr.decode('utf-8', errors='ignore').strip()
                errors.append(f"Page {p} script #{idx+1} syntax error:\n{err_msg}")
                
        print(f"  [PAGE] {p:<20} HTTP 200 | {len(scripts)} script block(s) verified")
        
    print(f"\nTotal client script blocks checked: {total_scripts}")
    
    # 2. REST API endpoints
    apis = [
        ('GET', '/api/dashboard/'),
        ('GET', '/api/sensors/'),
        ('GET', '/api/sensors/CC-01/history/?limit=10'),
        ('GET', '/api/pipeline/?sensor=CC-01'),
        ('GET', '/api/model/'),
        ('GET', '/api/predictions/?sensor=CC-01'),
        ('GET', '/api/risk/?sensor=CC-01'),
        ('GET', '/api/optimization/?sensor=CC-01'),
        ('GET', '/api/alerts/?sensor=CC-01'),
        ('GET', '/api/report/?sensor=CC-01'),
        ('GET', '/api/reports/'),
        ('POST', '/api/reports/generate/'),
        ('GET', '/api/file_content/?name=coldchain_report.json'),
        ('GET', '/api/save_case/?sensor=CC-01'),
        ('GET', '/api/profile/?profile=Vaccine'),
        ('POST', '/api/simulation/start/'),
        ('POST', '/api/simulation/pause/'),
        ('POST', '/api/simulation/reset/'),
        ('POST', '/api/alerts/future-breach/resolve/'),
    ]
    
    print("\nValidating APIs:")
    for method, url in apis:
        if method == 'GET':
            r = c.get(url)
        else:
            r = c.post(url)
            
        if r.status_code != 200:
            errors.append(f"API {method} {url} returned HTTP {r.status_code}")
            print(f"  [API] {method:<4} {url:<45} FAIL (HTTP {r.status_code})")
        else:
            print(f"  [API] {method:<4} {url:<45} HTTP 200 OK")
            
    print("\n" + "=" * 60)
    if errors:
        print(f"VALIDATION FAILED WITH {len(errors)} ERROR(S):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("ALL RUNTIME VALIDATIONS PASSED WITH 0 ERRORS.")
        print("=" * 60)

if __name__ == '__main__':
    main()
