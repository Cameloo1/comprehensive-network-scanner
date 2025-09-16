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
                if host.get('tls') and (host['tls'].get('testssl_json') or host['tls'].get('sslyze')):
                    story.append(Paragraph("TLS/SSL Analysis:", styles['Heading3']))
                    story.append(Spacer(1, 3))
                    
                    tls = host['tls']
                    if tls.get('sslyze') and not tls['sslyze'].get('error'):
                        sslyze = tls['sslyze']
                        tls_data = [['Field', 'Value']]
                        
                        if sslyze.get('certificate_subject'):
                            tls_data.append(['Certificate Subject', str(sslyze['certificate_subject'])[:100]])
                        if sslyze.get('certificate_issuer'):
                            tls_data.append(['Certificate Issuer', str(sslyze['certificate_issuer'])[:100]])
                        if 'certificate_valid' in sslyze:
                            valid = "Valid" if sslyze['certificate_valid'] else "Invalid"
                            tls_data.append(['Certificate Valid', valid])
                        if sslyze.get('supported_tls_versions'):
                            versions = ", ".join(sslyze['supported_tls_versions'])
                            tls_data.append(['Supported TLS Versions', versions])
                        if sslyze.get('total_cipher_suites'):
                            tls_data.append(['Total Cipher Suites', str(sslyze['total_cipher_suites'])])
                        
                        if len(tls_data) > 1:  # More than just header
                            tls_table = Table(tls_data, colWidths=[150, 270])
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
                        else:
                            story.append(Paragraph("No TLS data available", styles['Normal']))
                    else:
                        error = tls.get('sslyze', {}).get('error', 'No data') if tls.get('sslyze') else 'No data'
                        story.append(Paragraph(f"TLS analysis not available: {error}", styles['Normal']))
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
            
            doc.build(story)
            return {"html": html_path, "pdf": pdf_path}
            
        except Exception as pdf_error:
            # If both methods fail, return HTML only
            print(f"PDF generation failed with both WeasyPrint and ReportLab: {e}, {pdf_error}", file=sys.stderr)
        print("HTML report generated successfully. PDF generation requires additional system dependencies.", file=sys.stderr)
        return {"html": html_path, "pdf": None}
