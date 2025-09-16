from app.core.db import SessionLocal, Scan, Host, Finding

def update_scan_totals(scan_id: str):
    s = SessionLocal()
    sevmap = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    q = (s.query(Finding)
         .join(Host, Host.id == Finding.host_id)
         .filter(Host.scan_id == scan_id))
    for f in q.all():
        sevmap[f.severity.lower()] = sevmap.get(f.severity.lower(), 0) + 1
    sc = s.query(Scan).filter_by(id=scan_id).first()
    if sc:
        sc.summary_high = sevmap["high"] + sevmap["critical"] * 0  # keep separate if needed
        sc.summary_medium = sevmap["medium"]
        sc.summary_low = sevmap["low"]
        sc.summary_info = sevmap["info"]
        s.add(sc)
        s.commit()
    s.close()
    return sevmap
