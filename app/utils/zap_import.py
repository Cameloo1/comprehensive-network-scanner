import json

def parse_zap(path: str) -> list[dict]:
    data = json.load(open(path))
    alerts = data.get("site", [])
    out = []
    for s in alerts:
        for a in s.get("alerts", []):
            sev = (a.get("riskdesc", "Info").split()[0] or "Info").lower()
            out.append({
                "name": a.get("name"),
                "severity": {"informational": "info", "low": "low", "medium": "medium", "high": "high"}.get(sev, "info"),
                "evidence": (a.get("desc") or "")[:400],
                "remediation": (a.get("solution") or "")[:400]
            })
    return out
