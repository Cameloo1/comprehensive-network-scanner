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
        
        # Add fallback for WHOIS data
        if not whois_data:
            whois_data = {
                "error": "WHOIS lookup failed or not performed",
                "network": {"name": "Unknown", "start_address": "N/A", "end_address": "N/A"},
                "asn": "N/A",
                "asn_description": "N/A",
                "asn_country_code": "N/A",
                "asn_cidr": "N/A"
            }
        
        # Parse TLS data if available
        tls_data = {}
        if h.tls_json:
            try:
                tls_data = json.loads(h.tls_json)
            except:
                tls_data = {}
        
        # Ensure TLS data has fallback structure
        if not tls_data:
            tls_data = {
                "testssl_json": None,
                "sslyze": {"error": "TLS analysis not performed - no open HTTPS ports found"},
                "open_ports": []
            }
        else:
            # Add fallback for missing testssl data
            if "testssl_json" not in tls_data:
                tls_data["testssl_json"] = None
            # Add fallback for missing sslyze data
            if "sslyze" not in tls_data:
                tls_data["sslyze"] = {"error": "SSLyze analysis failed or not performed"}
            # Add fallback for missing open_ports
            if "open_ports" not in tls_data:
                tls_data["open_ports"] = []
        
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
                    "fingerprint": {"error": "Web fingerprinting failed or returned no data"}
                })
        
        # Add fallback for no web targets found
        if not web_data:
            # Check if there were any HTTP/HTTPS ports that should have been fingerprinted
            http_ports = [p for p in ports if p.service in ("http", "https") and p.state == "open"]
            if http_ports:
                for p in http_ports:
                    scheme = "https" if (p.port == 443 or p.service == "https") else "http"
                    url = f"{scheme}://{h.ip}:{p.port}"
                    web_data.append({
                        "url": url,
                        "fingerprint": {"error": "Web fingerprinting not performed - tool may have failed"}
                    })
            else:
                web_data.append({
                    "url": "No HTTP/HTTPS ports found",
                    "fingerprint": {"status": "No web services detected"}
                })
        
        # Ensure findings have proper fallback
        findings_data = []
        for f in findings:
            findings_data.append(dict(
                severity=f.severity or "info",
                name=f.name or "Unknown finding",
                evidence=f.evidence or "No evidence available",
                remediation=f.remediation or "No remediation provided",
                source=f.source or "unknown"
            ))
        
        # Add fallback finding if no vulnerabilities found
        if not findings_data:
            findings_data.append({
                "severity": "info",
                "name": "No vulnerabilities detected",
                "evidence": "Nuclei scan completed with no findings",
                "remediation": "Continue regular security monitoring",
                "source": "nuclei"
            })
        
        # Add tool status information
        tool_status = {
            "nuclei": {
                "status": "Success" if findings else "No findings",
                "details": f"Found {len(findings)} vulnerabilities" if findings else "No vulnerabilities detected"
            },
            "whatweb": {
                "status": "Success" if web_data and any(wt.get('fingerprint', {}).get('error') is None for wt in web_data) else "No web services",
                "details": f"Analyzed {len(web_data)} web targets" if web_data else "No HTTP/HTTPS ports found"
            },
            "sslyze": {
                "status": "Success" if tls_data.get('sslyze') and not tls_data['sslyze'].get('error') else "Not performed",
                "details": "TLS analysis completed" if tls_data.get('sslyze') and not tls_data['sslyze'].get('error') else "No open HTTPS ports found"
            },
            "testssl": {
                "status": "Success" if tls_data.get('testssl_json') else "Not performed",
                "details": "TLS configuration analyzed" if tls_data.get('testssl_json') else "No open HTTPS ports found"
            },
            "whois": {
                "status": "Success" if whois_data and not whois_data.get('error') else "Failed",
                "details": "Network information retrieved" if whois_data and not whois_data.get('error') else "WHOIS lookup failed"
            },
            "reverse_dns": {
                "status": "Success" if h.rdns else "No record",
                "details": f"Resolved to {h.rdns}" if h.rdns else "No reverse DNS record found"
            }
        }
        
        ctx_hosts.append({
            "ip": h.ip, 
            "rdns": h.rdns or "No reverse DNS record found",
            "whois": whois_data, 
            "tls": tls_data,
            "ports": [dict(port=p.port, proto=p.proto, service=p.service, version=p.version, state=p.state) for p in ports],
            "findings": findings_data,
            "web_targets": web_data,
            "tool_status": tool_status
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
            
            # Create custom style for host headers (30% bigger than Heading2)
            host_header_style = styles['Heading2'].clone('HostHeader')
            host_header_style.fontSize = int(styles['Heading2'].fontSize * 1.3)
            
            story = []
            
            # Parse HTML content and convert to PDF
            title = "Comprehensive Penetration Test Report"
            story.append(Paragraph(title, styles['Title']))
            story.append(Spacer(1, 12))
            
            # Add executive summary with professional formatting
            story.append(Paragraph("Executive Summary", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            # Scan overview section
            story.append(Paragraph("Scan Overview:", styles['Heading3']))
            story.append(Paragraph(f" Total IPs Scanned: {len(ctx['hosts'])}", styles['Normal']))
            story.append(Paragraph(f" Scan Sessions: 1", styles['Normal']))
            story.append(Paragraph(f" Safe Mode: {'Enabled' if ctx['scan'].safe_mode else 'Disabled'}", styles['Normal']))
            # Format scan period using actual scan times
            scan_start_time = ctx['scan'].started
            scan_end_time = ctx['scan'].finished if ctx['scan'].finished else datetime.datetime.utcnow()
            story.append(Paragraph(f" Scan Period: {scan_start_time.strftime('%Y-%m-%d %H:%M UTC')} to {scan_end_time.strftime('%Y-%m-%d %H:%M UTC')}", styles['Normal']))
            story.append(Spacer(1, 6))
            
            # Vulnerability summary
            story.append(Paragraph("Vulnerability Summary:", styles['Heading3']))
            story.append(Paragraph(f" High: {ctx['totals']['high']}", styles['Normal']))
            story.append(Paragraph(f" Medium: {ctx['totals']['medium']}", styles['Normal']))
            story.append(Paragraph(f" Low: {ctx['totals']['low']}", styles['Normal']))
            story.append(Paragraph(f" Info: {ctx['totals']['info']}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Target IPs summary table
            story.append(Paragraph("Target IPs Scanned:", styles['Heading2']))
            story.append(Spacer(1, 6))
            
            # Create a simple table for target summary
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            
            table_data = [['IP Address', 'Reverse DNS', 'Ports Found', 'Findings']]
            for host in ctx['hosts']:
                total_ports = len(host['ports'])
                open_ports = len([p for p in host['ports'] if p['state'] == 'open'])
                findings_count = len(host['findings'])
                
                rdns = host['rdns'] or 'No RDNS'
                if total_ports > 0:
                    ports_text = f"{total_ports} total ({open_ports} open)"
                else:
                    ports_text = "No ports found"
                findings_text = f"{findings_count} findings" if findings_count > 0 else "No findings"
                
                table_data.append([host['ip'], rdns, ports_text, findings_text])
            
            target_table = Table(table_data, colWidths=[120, 200, 100, 100])
            target_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(target_table)
            story.append(Spacer(1, 20))
            
            # Add detailed host information
            for host in ctx['hosts']:
                story.append(Paragraph(f"Host: {host['ip']}", host_header_style))
                if host['rdns']:
                    story.append(Paragraph(f"Reverse DNS: {host['rdns']}", styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Add port scan results with table
                if host['ports']:
                    story.append(Paragraph("Port Scan Results:", styles['Heading3']))
                    story.append(Spacer(1, 3))
                    
                    # Create port scan table
                    port_data = [['Port', 'Protocol', 'Service', 'Version', 'State']]
                    for p in host['ports']:
                        port_data.append([
                            str(p['port']),
                            p['proto'],
                            p['service'] or 'unknown',
                            p['version'] or 'N/A',
                            p['state']
                        ])
                    
                    port_table = Table(port_data, colWidths=[60, 60, 100, 120, 60])
                    port_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8)
                    ]))
                    story.append(port_table)
                    story.append(Spacer(1, 6))
                else:
                    story.append(Paragraph("No ports found", styles['Normal']))
                    story.append(Spacer(1, 6))
                
                # Add WHOIS information with table
                if host.get('whois') and host['whois'].get('network'):
                    story.append(Paragraph("WHOIS Information:", styles['Heading3']))
                    story.append(Spacer(1, 3))
                    
                    whois = host['whois']
                    whois_data = [
                        ['Field', 'Value'],
                        ['Organization', whois.get('network', {}).get('name', 'N/A')],
                        ['ASN', f"{whois.get('asn', 'N/A')} ({whois.get('asn_description', 'N/A')})"],
                        ['Country', whois.get('asn_country_code', 'N/A')],
                        ['CIDR', whois.get('asn_cidr', 'N/A')],
                        ['Network Range', f"{whois.get('network', {}).get('start_address', 'N/A')} - {whois.get('network', {}).get('end_address', 'N/A')}"]
                    ]
                    
                    whois_table = Table(whois_data, colWidths=[120, 300])
                    whois_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8)
                    ]))
                    story.append(whois_table)
                    story.append(Spacer(1, 6))
                    
                    # Add contact information if available
                    if whois.get('objects'):
                        story.append(Paragraph("Contact Information:", styles['Heading4']))
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
                        story.append(Spacer(1, 6))
                
                # Add web fingerprinting data with table
                if host.get('web_targets'):
                    story.append(Paragraph("Web Application Fingerprinting:", styles['Heading3']))
                    story.append(Spacer(1, 3))
                    
                    web_data = [['URL', 'Technologies Detected']]
                    for wt in host['web_targets']:
                        if wt['fingerprint'].get('plugins'):
                            plugins = ", ".join(wt['fingerprint']['plugins'])
                        else:
                            status = wt['fingerprint'].get('status_code', 'N/A')
                            plugins = f"Basic HTTP response ({status})"
                        web_data.append([wt['url'], plugins])
                    
                    web_table = Table(web_data, colWidths=[200, 220])
                    web_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, 0), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                        ('GRID', (0, 0), (-1, -1), 1, colors.black),
                        ('FONTSIZE', (0, 1), (-1, -1), 8)
                    ]))
                    story.append(web_table)
                    story.append(Spacer(1, 6))
                
                # Add TLS analysis data with table
                story.append(Paragraph("TLS/SSL Analysis:", styles['Heading3']))
                story.append(Spacer(1, 3))
                
                tls = host.get('tls', {})
                tls_data = [['Tool', 'Status', 'Details']]
                
                # SSLyze data
                if tls.get('sslyze') and not tls['sslyze'].get('error'):
                    sslyze = tls['sslyze']
                    details = []
                    if sslyze.get('certificate_subject'):
                        details.append(f"Subject: {str(sslyze['certificate_subject'])[:50]}...")
                    if sslyze.get('supported_tls_versions'):
                        versions = ", ".join(sslyze['supported_tls_versions'])
                        details.append(f"TLS Versions: {versions}")
                    if sslyze.get('total_cipher_suites'):
                        details.append(f"Cipher Suites: {sslyze['total_cipher_suites']}")
                    
                    status = "Success" if details else "No data"
                    details_text = "; ".join(details) if details else "Analysis completed but no detailed data available"
                    tls_data.append(['SSLyze', status, details_text])
                else:
                    error = tls.get('sslyze', {}).get('error', 'Not performed') if tls.get('sslyze') else 'Not performed'
                    tls_data.append(['SSLyze', 'Failed', error])
                
                # TestSSL data
                if tls.get('testssl_json'):
                    tls_data.append(['TestSSL', 'Success', 'TLS configuration analyzed (detailed data available)'])
                else:
                    tls_data.append(['TestSSL', 'Not performed', 'No open HTTPS ports or tool failed'])
                
                # Open ports info
                if tls.get('open_ports'):
                    ports_info = ", ".join([f"{p['port']}/{p['service']}" for p in tls['open_ports']])
                    tls_data.append(['Target Ports', 'Found', f"Analyzed: {ports_info}"])
                else:
                    tls_data.append(['Target Ports', 'None', 'No open HTTPS ports found for analysis'])
                
                tls_table = Table(tls_data, colWidths=[80, 80, 260])
                tls_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(tls_table)
                story.append(Spacer(1, 6))
            
                # Add tool status summary
                story.append(Paragraph("Tool Status Summary:", styles['Heading3']))
                story.append(Spacer(1, 3))
                
                tool_status_data = [['Tool', 'Status', 'Details']]
                tool_status = host.get('tool_status', {})
                
                tools = [
                    ('Nuclei (Vulnerability Scanner)', 'nuclei'),
                    ('WhatWeb (Web Fingerprinting)', 'whatweb'),
                    ('SSLyze (TLS Analysis)', 'sslyze'),
                    ('TestSSL (TLS Analysis)', 'testssl'),
                    ('WHOIS (Network Information)', 'whois'),
                    ('Reverse DNS', 'reverse_dns')
                ]
                
                for tool_name, tool_key in tools:
                    status_info = tool_status.get(tool_key, {'status': 'Unknown', 'details': 'No data available'})
                    tool_status_data.append([
                        tool_name,
                        status_info['status'],
                        status_info['details']
                    ])
                
                tool_status_table = Table(tool_status_data, colWidths=[200, 100, 220])
                tool_status_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(tool_status_table)
                story.append(Spacer(1, 6))
            
            # Add findings with table
            if host['findings']:
                story.append(Paragraph("Vulnerability Findings:", styles['Heading3']))
                story.append(Spacer(1, 3))
                
                findings_data = [['Severity', 'Source', 'Title', 'Evidence']]
                for finding in host['findings']:
                    evidence = finding.get('evidence', 'N/A')[:100] if finding.get('evidence') else 'N/A'
                    findings_data.append([
                        finding['severity'].upper(),
                        finding.get('source', 'unknown').upper(),
                        finding['name'][:80],
                        evidence
                    ])
                
                findings_table = Table(findings_data, colWidths=[80, 80, 200, 160])
                findings_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('FONTSIZE', (0, 1), (-1, -1), 8)
                ]))
                story.append(findings_table)
            else:
                story.append(Paragraph("No vulnerability findings", styles['Normal']))
            
            story.append(Spacer(1, 12))
        
            # Build the complete PDF document
            doc.build(story)
            return {"html": html_path, "pdf": pdf_path}
            
        except Exception as pdf_error:
            # If both methods fail, return HTML only
            print(f"PDF generation failed with both WeasyPrint and ReportLab: {e}, {pdf_error}", file=sys.stderr)
        print("HTML report generated successfully. PDF generation requires additional system dependencies.", file=sys.stderr)
        return {"html": html_path, "pdf": None}
