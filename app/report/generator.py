from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.db import SessionLocal, Scan, Host, Port, Finding, WebTarget
import os
import sys
import json

env = Environment(loader=FileSystemLoader("app/ui/templates"), autoescape=select_autoescape())

def build_context(scan_id:str):
    s = SessionLocal()
    scan = s.query(Scan).get(scan_id)
    if not scan:
        s.close()
        raise ValueError(f"Scan with ID '{scan_id}' not found")
    
    hosts = s.query(Host).filter_by(scan_id=scan_id).all()
    ctx_hosts=[]
    totals={"high":0,"medium":0,"low":0,"info":0}
    for h in hosts:
        ports = s.query(Port).filter_by(host_id=h.id).all()
        findings = s.query(Finding).filter_by(host_id=h.id).all()
        web_targets = s.query(WebTarget).filter_by(host_id=h.id).all()
        
        for f in findings:
            if f.severity in totals: totals[f.severity]+=1
        
        # Parse WHOIS data if available
        whois_data = {}
        if h.whois_json:
            try:
                whois_data = json.loads(h.whois_json)
            except:
                whois_data = {}
        
        # Parse TLS data if available
        tls_data = {}
        if h.tls_json:
            try:
                tls_data = json.loads(h.tls_json)
            except:
                tls_data = {}
        
        # Parse web fingerprinting data
        web_data = []
        for wt in web_targets:
            try:
                fp_data = json.loads(wt.fp_json) if wt.fp_json else {}
                web_data.append({
                    "url": wt.url,
                    "fingerprint": fp_data
                })
            except:
                web_data.append({
                    "url": wt.url,
                    "fingerprint": {}
                })
        
        ctx_hosts.append({
            "ip": h.ip, "rdns": h.rdns, "whois": whois_data, "tls": tls_data,
            "ports": [dict(port=p.port, proto=p.proto, service=p.service, version=p.version, state=p.state) for p in ports],
            "findings": [dict(severity=f.severity, name=f.name, evidence=f.evidence, remediation=f.remediation, source=f.source) for f in findings],
            "web_targets": web_data
        })
    s.close()
    return {"scan": scan, "hosts": ctx_hosts, "totals": totals}

def make_report(scan_id:str):
    ctx = build_context(scan_id)
    os.makedirs("reports", exist_ok=True)
    html_txt = env.get_template("report.html").render(**ctx)
    html_path = f"reports/{scan_id}.html"
    pdf_path = f"reports/{scan_id}.pdf"
    
    # Write HTML file
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_txt)
    
    # Try to generate PDF with WeasyPrint, fallback to ReportLab if it fails
    try:
        # Suppress WeasyPrint warnings by redirecting stdout temporarily
        import contextlib
        import io
        
        with contextlib.redirect_stdout(io.StringIO()):
            from weasyprint import HTML
            HTML(string=html_txt).write_pdf(pdf_path)
        return {"html": html_path, "pdf": pdf_path}
    except Exception as e:
        # Fallback to ReportLab for PDF generation
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib.units import inch
            import re
            
            # Create PDF with ReportLab
            doc = SimpleDocTemplate(pdf_path, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Parse HTML content and convert to PDF
            title = f"Scan Report {scan_id}"
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))
            
            # Add basic scan information
            story.append(Paragraph(f"<b>Target:</b> {ctx['scan'].target}", styles['Normal']))
            story.append(Paragraph(f"<b>Safe Mode:</b> {ctx['scan'].safe_mode}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Add executive summary
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            summary = f"High: {ctx['totals']['high']}, Medium: {ctx['totals']['medium']}, Low: {ctx['totals']['low']}, Info: {ctx['totals']['info']}"
            story.append(Paragraph(summary, styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Add host information
            for host in ctx['hosts']:
                story.append(Paragraph(f"Host: {host['ip']}", styles['Heading2']))
                if host['rdns']:
                    story.append(Paragraph(f"Reverse DNS: {host['rdns']}", styles['Normal']))
                
                # Add port scan results
                if host['ports']:
                    story.append(Paragraph("Port Scan Results:", styles['Heading3']))
                    for p in host['ports']:
                        port_text = f"Port {p['port']}/{p['proto']}: {p['service'] or 'unknown'}"
                        if p['version']:
                            port_text += f" ({p['version']})"
                        port_text += f" - {p['state']}"
                        story.append(Paragraph(port_text, styles['Normal']))
                else:
                    story.append(Paragraph("No ports found", styles['Normal']))
                
                # Add WHOIS information
                if host.get('whois') and host['whois'].get('network'):
                    story.append(Paragraph("WHOIS Information:", styles['Heading3']))
                    whois = host['whois']
                    story.append(Paragraph(f"<b>Organization:</b> {whois.get('network', {}).get('name', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"<b>ASN:</b> {whois.get('asn', 'N/A')} ({whois.get('asn_description', 'N/A')})", styles['Normal']))
                    story.append(Paragraph(f"<b>Country:</b> {whois.get('asn_country_code', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"<b>CIDR:</b> {whois.get('asn_cidr', 'N/A')}", styles['Normal']))
                    story.append(Paragraph(f"<b>Network Range:</b> {whois.get('network', {}).get('start_address', 'N/A')} - {whois.get('network', {}).get('end_address', 'N/A')}", styles['Normal']))
                    
                    # Add contact information
                    if whois.get('objects'):
                        story.append(Paragraph("Contacts:", styles['Heading4']))
                        for obj_key, obj in whois['objects'].items():
                            if obj.get('contact'):
                                contact = obj['contact']
                                story.append(Paragraph(f"<b>{obj_key}:</b> {contact.get('name', 'N/A')}", styles['Normal']))
                                if contact.get('email'):
                                    email = contact['email'][0]['value'] if contact['email'] else 'N/A'
                                    story.append(Paragraph(f"  Email: {email}", styles['Normal']))
                                if contact.get('phone'):
                                    phone = contact['phone'][0]['value'] if contact['phone'] else 'N/A'
                                    story.append(Paragraph(f"  Phone: {phone}", styles['Normal']))
                
                # Add web fingerprinting data
                if host.get('web_targets'):
                    story.append(Paragraph("Web Application Fingerprinting:", styles['Heading3']))
                    for wt in host['web_targets']:
                        story.append(Paragraph(f"URL: {wt['url']}", styles['Normal']))
                        if wt['fingerprint'].get('plugins'):
                            plugins = ", ".join(wt['fingerprint']['plugins'])
                            story.append(Paragraph(f"  Technologies: {plugins}", styles['Normal']))
                        else:
                            status = wt['fingerprint'].get('status_code', 'N/A')
                            story.append(Paragraph(f"  Basic HTTP response ({status})", styles['Normal']))
                
                # Add TLS analysis data
                if host.get('tls') and (host['tls'].get('testssl_json') or host['tls'].get('sslyze')):
                    story.append(Paragraph("TLS/SSL Analysis:", styles['Heading3']))
                    tls = host['tls']
                    if tls.get('sslyze') and not tls['sslyze'].get('error'):
                        sslyze = tls['sslyze']
                        if sslyze.get('certificate_subject'):
                            story.append(Paragraph(f"Certificate Subject: {sslyze['certificate_subject']}", styles['Normal']))
                        if sslyze.get('certificate_issuer'):
                            story.append(Paragraph(f"Certificate Issuer: {sslyze['certificate_issuer']}", styles['Normal']))
                        if 'certificate_valid' in sslyze:
                            valid = "Valid" if sslyze['certificate_valid'] else "Invalid"
                            story.append(Paragraph(f"Certificate Valid: {valid}", styles['Normal']))
                        if sslyze.get('supported_tls_versions'):
                            versions = ", ".join(sslyze['supported_tls_versions'])
                            story.append(Paragraph(f"Supported TLS Versions: {versions}", styles['Normal']))
                        if sslyze.get('total_cipher_suites'):
                            story.append(Paragraph(f"Total Cipher Suites: {sslyze['total_cipher_suites']}", styles['Normal']))
                    else:
                        error = tls.get('sslyze', {}).get('error', 'No data') if tls.get('sslyze') else 'No data'
                        story.append(Paragraph(f"TLS analysis not available: {error}", styles['Normal']))
                
                # Add findings
                if host['findings']:
                    story.append(Paragraph("Vulnerability Findings:", styles['Heading3']))
                    for finding in host['findings']:
                        finding_text = f"{finding['severity'].upper()} ({finding.get('source', 'unknown').upper()}): {finding['name']}"
                        story.append(Paragraph(finding_text, styles['Normal']))
                        if finding.get('evidence'):
                            story.append(Paragraph(f"  Evidence: {finding['evidence']}", styles['Normal']))
                else:
                    story.append(Paragraph("No vulnerability findings", styles['Normal']))
                
                story.append(Spacer(1, 12))
            
            doc.build(story)
            return {"html": html_path, "pdf": pdf_path}
            
        except Exception as pdf_error:
            # If both methods fail, return HTML only
            print(f"PDF generation failed with both WeasyPrint and ReportLab: {e}, {pdf_error}", file=sys.stderr)
        print("HTML report generated successfully. PDF generation requires additional system dependencies.", file=sys.stderr)
        return {"html": html_path, "pdf": None}
