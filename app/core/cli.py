import typer, uuid, sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.core.db import init_db, SessionLocal, Host, Finding, WebTarget
from app.api.server import expand_targets
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.scans.baseline import sh, run_tcp_scan
from app.report.generator import make_report, build_context
from app.report.normalize import update_scan_totals
from app.utils.nessus_import import parse_nessus
from app.utils.zap_import import parse_zap
from app.utils.progress import progress_manager

def run_concurrent_scan(scan_id: str, ips: list[str], safe_mode: bool, max_workers: int = 8) -> str:
    """Run concurrent scan with configurable max_workers"""
    import os
    import datetime
    import json
    from app.core.db import SessionLocal, Scan
    
    os.makedirs("runs", exist_ok=True)
    
    # Create progress tracker
    progress = progress_manager.create_scan_progress(scan_id, len(ips), max_workers)
    
    # Create scan record once
    sess = SessionLocal()
    try:
        scan = Scan(id=scan_id, target=",".join(ips), safe_mode=safe_mode)
        sess.add(scan)
        sess.commit()
    finally:
        sess.close()
    
    try:
        typer.echo(f"Starting concurrent scan of {len(ips)} targets with {max_workers} workers...")
        
        # Use ThreadPoolExecutor with configurable max_workers
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit each IP for scanning
            future_to_ip = {
                executor.submit(run_single_ip_scan_with_progress, scan_id, ip, safe_mode, progress): ip 
                for ip in ips
            }
            
            # Process completed scans
            completed_scans = []
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result_path = future.result()
                    completed_scans.append(result_path)
                except Exception as e:
                    progress.target_failed(ip)
                    typer.echo(f"Error scanning {ip}: {e}", err=True)
        
        # Print final summary
        progress.print_final_summary()
        
        # Update scan totals after all concurrent scans complete
        update_scan_totals(scan_id)
        
        # Generate consolidated result file
        result_path = f"runs/{scan_id}.json"
        with open(result_path, "w") as f:
            json.dump({
                "scan_id": scan_id, 
                "targets": ips, 
                "started": datetime.datetime.utcnow().isoformat() + "Z", 
                "safe_mode": safe_mode,
                "status": "completed",
                "concurrent": True,
                "max_workers": max_workers
            }, f, indent=2)
        
        return result_path
        
    except Exception as e:
        progress.target_failed("system_error")
        typer.echo(f"Error during concurrent scan: {e}", err=True)
        # Create error result file
        result_path = f"runs/{scan_id}.json"
        with open(result_path, "w") as f:
            json.dump({
                "scan_id": scan_id, 
                "targets": ips, 
                "started": datetime.datetime.utcnow().isoformat() + "Z", 
                "safe_mode": safe_mode,
                "status": "error",
                "error": str(e),
                "concurrent": True,
                "max_workers": max_workers
            }, f, indent=2)
        return result_path
    finally:
        # Clean up progress tracker
        progress_manager.remove_scan_progress(scan_id)

def run_single_ip_scan_with_progress(scan_id: str, ip: str, safe_mode: bool, progress) -> str:
    """Run scan for a single IP with progress tracking"""
    progress.target_started(ip)
    try:
        result = run_single_ip_scan(scan_id, ip, safe_mode)
        progress.target_completed(ip)
        return result
    except Exception as e:
        progress.target_failed(ip)
        raise e

def run_single_ip_scan(scan_id: str, ip: str, safe_mode: bool) -> str:
    """Run scan for a single IP without creating scan record (for concurrent use)"""
    import subprocess, os, datetime, json
    from typing import List
    from app.core.db import SessionLocal, Host, Port, WebTarget, Finding
    from app.scans.recon import reverse_dns, whois_ip, dns_records
    from app.utils.nmap_parse import parse_nmap_xml
    from app.scans.web_fp import whatweb
    from app.scans.tls import run_testssl, run_sslyze
    from app.scans.nuclei_safe import run_nuclei, load_linejson, nuclei_to_finding
    from app.report.normalize import update_scan_totals
    
    os.makedirs("runs", exist_ok=True)
    sess = SessionLocal()
    
    try:
        # Use faster scan settings for localhost and lab networks
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
        
        return f"runs/{scan_id}_{ip}.xml"
        
    except Exception as e:
        print(f"Error during scan of {ip}: {e}")
        return f"runs/{scan_id}_{ip}.xml"
    finally:
        sess.close()

def scan(
    target: str = typer.Argument(..., help="Target IP, CIDR, or comma-separated list to scan"),
    safe: bool = typer.Option(True, "--safe/--no-safe", help="Enable safe mode"),
    max_workers: int = typer.Option(8, "--workers", "-w", help="Maximum number of concurrent workers (1-32)")
):
    """Start a network scan of the specified target."""
    # Validate max_workers
    if max_workers < 1 or max_workers > 32:
        typer.echo("Error: max_workers must be between 1 and 32", err=True)
        raise typer.Exit(1)
    
    init_db()
    ips = expand_targets(target)
    scan_id = str(uuid.uuid4())
    
    # For multiple targets, use concurrent scanning
    if len(ips) > 1:
        path = run_concurrent_scan(scan_id, ips, safe, max_workers)
    else:
        # Single IP - use existing sequential scan
        typer.echo(f"Scanning single target: {ips[0]}")
        path = run_tcp_scan(scan_id, ips, safe)
    
    typer.echo(f"Results saved to: {path}")

app = typer.Typer()

app.command()(scan)

@app.command()
def report(scan_id: str):
    try:
        p = make_report(scan_id)
        import json
        print(json.dumps(p, indent=2))
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def import_nessus(scan_id: str, path: str):
    """Import Nessus findings from a .nessus XML file."""
    try:
        sess = SessionLocal()
        by_ip = {h.ip: h.id for h in sess.query(Host).filter_by(scan_id=scan_id).all()}
        count = 0
        for item in parse_nessus(path):
            ip = item["host"]
            if ip in by_ip:
                exists = (sess.query(Finding)
                    .filter_by(host_id=by_ip[ip], source="nessus", name=item["name"]).first())
                if not exists:
                    f = Finding(
                        host_id=by_ip[ip], 
                        source="nessus", 
                        **{k: item[k] for k in ("name", "severity", "cvss", "evidence", "remediation")}
                    )
                    sess.add(f)
                    count += 1
        sess.commit()
        sess.close()
        update_scan_totals(scan_id)
        typer.echo(f"Imported {count} findings from Nessus.")
    except FileNotFoundError:
        typer.echo(f"Error: File not found: {path}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error importing Nessus file: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def import_zap(scan_id: str, path: str, host_ip: str):
    """Import ZAP findings from a JSON file."""
    try:
        sess = SessionLocal()
        host = sess.query(Host).filter_by(scan_id=scan_id, ip=host_ip).first()
        if not host:
            typer.echo(f"Error: Host {host_ip} not found in scan {scan_id}", err=True)
            sess.close()
            raise typer.Exit(1)
        
        items = parse_zap(path)
        count = 0
        for item in items:
            exists = (sess.query(Finding)
                .filter_by(host_id=host.id, source="zap", name=item["name"]).first())
            if not exists:
                f = Finding(host_id=host.id, source="zap", **item)
                sess.add(f)
                count += 1
        
        sess.commit()
        sess.close()
        update_scan_totals(scan_id)
        typer.echo(f"Imported {count} ZAP alerts.")
    except FileNotFoundError:
        typer.echo(f"Error: File not found: {path}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Error importing ZAP file: {e}", err=True)
        raise typer.Exit(1)

@app.command()
def export_json(scan_id: str):
    import json
    s=SessionLocal()
    hosts = s.query(Host).filter_by(scan_id=scan_id).all()
    out=[]
    for h in hosts:
        finds = s.query(Finding).filter_by(host_id=h.id).all()
        out.append({"ip":h.ip,"rdns":h.rdns,"findings":[{"source":f.source,"name":f.name,"severity":f.severity,"cvss":f.cvss} for f in finds]})
    s.close()
    print(json.dumps(out, indent=2))

@app.command()
def export_csv(scan_id: str):
    import csv, sys
    s=SessionLocal()
    hosts = s.query(Host).filter_by(scan_id=scan_id).all()
    w = csv.writer(sys.stdout)
    w.writerow(["ip","source","name","severity","cvss"])
    for h in hosts:
        for f in s.query(Finding).filter_by(host_id=h.id).all():
            w.writerow([h.ip, f.source, f.name, f.severity, f.cvss or ""])
    s.close()

@app.command()
def summary(scan_id: str):
    ctx = build_context(scan_id)
    t = ctx["totals"]
    print(f"Assessment Summary: Identified {t['high']} high, {t['medium']} medium, {t['low']} low, and {t['info']} informational issues across {len(ctx['hosts'])} host(s). Prioritize patching high-severity findings and hardening exposed services.")

@app.command()
def help():
    """Show detailed help and usage examples"""
    print("""
NetScan - Network Penetration Testing Tool

USAGE EXAMPLES:

Single Target:
  python -m app.core.cli scan 192.168.1.1 --safe

Multiple Targets (Comma-separated):
  python -m app.core.cli scan 1.1.1.1,2.2.2.2,3.3.3.3 --safe

CIDR Range:
  python -m app.core.cli scan 192.168.1.0/24 --safe

Mixed Targets:
  python -m app.core.cli scan 127.0.0.1,192.168.1.0/30,8.8.8.8 --safe

With Custom Workers:
  python -m app.core.cli scan 1.1.1.1,2.2.2.2 --safe --workers 4

OPTIONS:
  --safe/--no-safe    Enable safe mode (default: --safe)
  --workers, -w       Maximum concurrent workers (1-32, default: 8)

PROGRESS INDICATOR:
  • Real-time progress bar showing completion percentage
  • Active worker count vs maximum workers
  • Failed target tracking
  • ETA calculation based on current performance
  • Final summary with success rate and timing

COMMANDS:
  scan <target>       Start a network scan
  report <scan_id>    Generate HTML/PDF report
  summary <scan_id>   Show scan summary
  help               Show this help message
""")

if __name__ == "__main__":
    app()
