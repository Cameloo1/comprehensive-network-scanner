import socket, json
import dns.resolver
from ipwhois import IPWhois

def reverse_dns(ip:str)->str|None:
    try: return socket.gethostbyaddr(ip)[0]
    except Exception: return None

def whois_ip(ip:str)->dict:
    try:
        return IPWhois(ip).lookup_rdap(depth=1)
    except Exception: return {}

def dns_records(host:str)->dict:
    out = {}
    for rtype in ("A","AAAA","MX","TXT"):
        try:
            out[rtype]=[str(r) for r in dns.resolver.resolve(host, rtype)]
        except Exception:
            pass
    return out
