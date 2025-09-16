import subprocess, os, datetime, json
from typing import List
from app.core.db import SessionLocal, Scan, Host, Port, WebTarget, Finding
from app.scans.recon import reverse_dns, whois_ip, dns_records
from app.utils.nmap_parse import parse_nmap_xml
from app.scans.web_fp import whatweb
from app.scans.tls import run_testssl, run_sslyze
from app.scans.nuclei_safe import run_nuclei, load_linejson, nuclei_to_finding
from app.report.normalize import update_scan_totals

def sh(cmd: list[str], timeout: int = 30) -> tuple[int,str,str]:
    """Run shell command with timeout"""
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return cp.returncode, cp.stdout, cp.stderr
    except subprocess.TimeoutExpired:
        return 1, "", f"Command timed out after {timeout} seconds"

def run_tcp_scan(scan_id: str, ips: List[str], safe_mode: bool) -> str:
    """Run TCP scan with optimized settings for faster execution"""
    import typer
    os.makedirs("runs", exist_ok=True)
    sess = SessionLocal()
    
    try:
        scan = Scan(id=scan_id, target=",".join(ips), safe_mode=safe_mode)
        sess.add(scan)
        sess.commit()
        
        # Use faster scan settings for localhost and lab networks
        for i, ip in enumerate(ips, 1):
            if len(ips) > 1:
                typer.echo(f"🔍 Scanning {ip} ({i}/{len(ips)})")
            else:
                typer.echo(f"🔍 Scanning {ip}")
            xml_path = f"runs/{scan_id}_{ip}.xml"
            
            # Optimize scan parameters based on target
            if ip.startswith("127.") or ip.startswith("192.168.") or ip.startswith("10."):
                # Fast scan for local/lab networks
                nmap_cmd = ["nmap", "-sS", "-T4", "-Pn", "--max-retries", "1", "--host-timeout", "30s", "-oX", xml_path, ip]
            else:
                # Standard scan for external targets
                nmap_cmd = ["nmap", "-sV", "-T3", "-Pn", "--max-retries", "2", "--host-timeout", "60s", "-oX", xml_path, ip]
            
            # Run scan with timeout
            returncode, stdout, stderr = sh(nmap_cmd, timeout=60)
            
            # Perform recon on the IP
            rdns = reverse_dns(ip)
            who = whois_ip(ip)
            # dns only if we have a hostname
            if rdns:
                who["dns_records"] = dns_records(rdns)
            
            # Create host record regardless of scan success
            host = Host(scan_id=scan_id, ip=ip, rdns=rdns, whois_json=json.dumps(who))
            sess.add(host)
            sess.commit()
            
            # parse and store ports
            for pr in parse_nmap_xml(xml_path):
                sess.add(Port(host_id=host.id, **pr))
            sess.commit()
            
            # web URLs (only for open ports to prevent hanging)
            ports = sess.query(Port).filter_by(host_id=host.id).all()
            open_web_ports = [p for p in ports if p.service in ("http","https") and p.state == "open"]
            for p in open_web_ports:
                scheme = "https" if (p.port == 443 or p.service == "https") else "http"
                url = f"{scheme}://{ip}:{p.port}"
                print(f"Web fingerprinting: {url} (port {p.port} is open)")
                fp = whatweb(url)
                sess.add(WebTarget(host_id=host.id, url=url, fp_json=json.dumps(fp)))
            if not open_web_ports:
                print(f"Web fingerprinting: Skipped - no open HTTP/HTTPS ports found for {ip}")
            sess.commit()
            
            # TLS analysis for HTTPS targets (only if ports are actually open)
            open_https_ports = [p for p in ports if (p.port==443 or p.service=="https") and p.state=="open"]
            if open_https_ports:
                print(f"TLS Analysis: Found {len(open_https_ports)} open HTTPS ports for {ip}")
                tj = run_testssl(ip, "runs")
                sl = run_sslyze(ip)
                tls = {"testssl_json": tj, "sslyze": sl, "open_ports": [{"port": p.port, "service": p.service} for p in open_https_ports]}
                host.tls_json = json.dumps(tls)
                sess.add(host); sess.commit()
            else:
                print(f"TLS Analysis: No open HTTPS ports found for {ip} (found {len([p for p in ports if p.port==443 or p.service=='https'])} filtered/closed HTTPS ports)")
            
            # nuclei safe
            npath = run_nuclei(ip, "runs")
            for row in load_linejson(npath):
                f = Finding(host_id=host.id, **nuclei_to_finding(row))
                sess.add(f)
            sess.commit()
            
            # Log scan results
            if returncode != 0:
                print(f"Warning: Nmap scan for {ip} returned code {returncode}: {stderr}")
        
        # Generate result file
        result_path = f"runs/{scan_id}.json"
        with open(result_path, "w") as f:
            json.dump({
                "scan_id": scan_id, 
                "targets": ips, 
                "started": datetime.datetime.utcnow().isoformat() + "Z", 
                "safe_mode": safe_mode,
                "status": "completed"
            }, f, indent=2)
        
        return result_path
        
    except Exception as e:
        print(f"Error during scan: {e}")
        # Still create result file with error status
        result_path = f"runs/{scan_id}.json"
        with open(result_path, "w") as f:
            json.dump({
                "scan_id": scan_id, 
                "targets": ips, 
                "started": datetime.datetime.utcnow().isoformat() + "Z", 
                "safe_mode": safe_mode,
                "status": "error",
                "error": str(e)
            }, f, indent=2)
        return result_path
    finally:
        sess.close()
        # update totals after session closed
        update_scan_totals(scan_id)
