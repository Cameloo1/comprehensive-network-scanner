from xml.etree import ElementTree as ET

def parse_nmap_xml(path: str) -> list[dict]:
    ports = []
    try:
        root = ET.parse(path).getroot()
        for p in root.iterfind(".//port"):
            info = {"port": int(p.get("portid")), "proto": p.get("protocol")}
            st = p.find("state")
            info["state"] = st.get("state") if st is not None else None
            svc = p.find("service")
            if svc is not None:
                info["service"] = svc.get("name")
                info["product"] = svc.get("product")
                info["version"] = svc.get("version")
            ports.append(info)
    except Exception:
        pass
    return ports
