from xml.etree import ElementTree as ET

def parse_nessus(path: str) -> list[dict]:
    items = []
    root = ET.parse(path).getroot()
    for h in root.iterfind(".//ReportHost"):
        host_name = h.get("name")
        for it in h.iterfind("ReportItem"):
            sev = it.get("severity") or "0"
            sev_map = {"0": "info", "1": "low", "2": "medium", "3": "high", "4": "critical"}
            # Handle CVSS score conversion safely
            cvss_score = 0.0
            try:
                cvss_str = it.get("cvssBaseScore")
                if cvss_str:
                    cvss_score = float(cvss_str)
            except (ValueError, TypeError):
                cvss_score = 0.0
            
            items.append({
                "host": host_name,
                "name": it.get("pluginName"),
                "severity": sev_map.get(sev, "info"),
                "cvss": cvss_score,
                "evidence": (it.findtext("description") or "")[:400],
                "remediation": (it.findtext("solution") or "")[:400]
            })
    return items
