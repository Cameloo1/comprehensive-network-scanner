import subprocess, json, os
SAFE_TAGS = "exposure,cve,misconfiguration,weak-password,default-cred"
EXCLUDE_TAGS = "takeover,bruteforce,osint,exploit"

def run_nuclei(ip:str, outdir:str)->str|None:
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"nuclei_{ip}.json")
    cmd = ["nuclei.exe","-u",ip,"-as","-tags",SAFE_TAGS,"-etags",EXCLUDE_TAGS,"-j","-o",out,"-timeout","10"]
    try:
        print(f"Nuclei: Starting scan of {ip} (timeout: 10s)")
        result = subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
        print(f"Nuclei: Scan completed for {ip}")
        return out if os.path.exists(out) else None
    except subprocess.TimeoutExpired:
        print(f"Nuclei: Scan timed out for {ip} - killing process")
        return None
    except FileNotFoundError:
        print(f"Nuclei: nuclei.exe not found - skipping vulnerability scan")
        return None
    except Exception as e:
        print(f"Nuclei: Error scanning {ip}: {e}")
        return None

def load_linejson(path:str)->list[dict]:
    items=[]
    if not (path and os.path.exists(path)): return items
    with open(path) as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try: items.append(json.loads(line))
            except: pass
    return items

def nuclei_to_finding(row:dict)->dict:
    info = row.get("info",{})
    sev = (info.get("severity") or "info").lower()
    cvss = None
    cls = info.get("classification") or {}
    if "cvss-score" in cls:
        try: cvss = float(cls["cvss-score"])
        except: pass
    return {
        "source":"nuclei",
        "name": info.get("name") or row.get("template-id"),
        "severity": sev,
        "cvss": cvss,
        "evidence": row.get("matched-at"),
        "remediation": "Review vendor guidance / patch / disable exposure."
    }
