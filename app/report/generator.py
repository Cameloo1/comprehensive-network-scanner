from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.core.db import SessionLocal, Scan, Host, Port, Finding
import os
import sys

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
        for f in findings:
            if f.severity in totals: totals[f.severity]+=1
        # Parse WHOIS data if available
        whois_data = {}
        if h.whois_json:
            try:
                import json
                whois_data = json.loads(h.whois_json)
            except:
                whois_data = {}
        
        ctx_hosts.append({
            "ip": h.ip, "rdns": h.rdns, "whois": whois_data,
            "ports": [dict(port=p.port, proto=p.proto, service=p.service, version=p.version) for p in ports],
            "findings": [dict(severity=f.severity, name=f.name, evidence=f.evidence, remediation=f.remediation) for f in findings]
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
                
                if host['ports']:
                    story.append(Paragraph("Open Ports:", styles['Heading3']))
                    ports_text = ", ".join([f"{p['port']}/{p['proto']} ({p['service']})" for p in host['ports']])
                    story.append(Paragraph(ports_text, styles['Normal']))
                
                if host['findings']:
                    story.append(Paragraph("Findings:", styles['Heading3']))
                    for finding in host['findings']:
                        finding_text = f"{finding['severity'].upper()}: {finding['name']}"
                        story.append(Paragraph(finding_text, styles['Normal']))
                
                story.append(Spacer(1, 12))
            
            doc.build(story)
            return {"html": html_path, "pdf": pdf_path}
            
        except Exception as pdf_error:
            # If both methods fail, return HTML only
            print(f"PDF generation failed with both WeasyPrint and ReportLab: {e}, {pdf_error}", file=sys.stderr)
            print("HTML report generated successfully. PDF generation requires additional system dependencies.", file=sys.stderr)
            return {"html": html_path, "pdf": None}
