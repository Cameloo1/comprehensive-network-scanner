#!/usr/bin/env python3
"""Analyze scan results to see which tools are working"""

import os
import json
from app.core.db import SessionLocal, Host, Port, Finding, WebTarget

def analyze_scan(scan_id):
    print(f"=== Analyzing Scan: {scan_id} ===")
    
    s = SessionLocal()
    try:
        # Get host data
        h = s.query(Host).filter_by(scan_id=scan_id).first()
        if not h:
            print("No host found for this scan ID")
            return
            
        print(f"Host: {h.ip}")
        print(f"rDNS: {h.rdns}")
        print(f"WHOIS: {h.whois_json}")
        print(f"TLS JSON: {h.tls_json}")
        
        # Get ports
        ports = s.query(Port).filter_by(host_id=h.id).all()
        print(f"\nPorts found: {len(ports)}")
        for p in ports:
            print(f"  Port {p.port}: {p.service} ({p.proto})")
        
        # Get findings
        findings = s.query(Finding).filter_by(host_id=h.id).all()
        print(f"\nFindings: {len(findings)}")
        for f in findings:
            print(f"  {f.severity}: {f.name} (source: {f.source})")
        
        # Get web targets
        wts = s.query(WebTarget).filter_by(host_id=h.id).all()
        print(f"\nWebTargets: {len(wts)}")
        for wt in wts:
            print(f"  URL: {wt.url}")
            print(f"  FP JSON: {wt.fp_json}")
        
        # Check for nuclei files
        nuclei_file = f"runs/nuclei_{h.ip}.json"
        if os.path.exists(nuclei_file):
            print(f"\nNuclei file exists: {nuclei_file}")
            with open(nuclei_file, 'r') as f:
                nuclei_data = f.read()
                print(f"Nuclei data length: {len(nuclei_data)} chars")
        else:
            print(f"\nNuclei file NOT found: {nuclei_file}")
        
        # Check for testssl files
        testssl_file = f"runs/testssl_{h.ip}.json"
        if os.path.exists(testssl_file):
            print(f"\ntestssl file exists: {testssl_file}")
            with open(testssl_file, 'r') as f:
                testssl_data = f.read()
                print(f"testssl data length: {len(testssl_data)} chars")
        else:
            print(f"\ntestssl file NOT found: {testssl_file}")
            
    finally:
        s.close()

def main():
    # Get the most recent scan
    s = SessionLocal()
    try:
        recent_scan = s.query(Host).order_by(Host.id.desc()).first()
        if recent_scan:
            analyze_scan(recent_scan.scan_id)
        else:
            print("No scans found in database")
    finally:
        s.close()

if __name__ == "__main__":
    main()
