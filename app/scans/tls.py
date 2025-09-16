import subprocess, json, os
from sslyze import ServerNetworkLocation, Scanner, ServerScanRequest

def run_testssl(host:str, outdir:str)->str|None:
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"testssl_{host}.json")
    cmd = ["testssl.sh","--jsonfile",out,"--quiet", host]
    try:
        print(f"TestSSL: Starting scan of {host} (timeout: 30s)")
        subprocess.run(cmd, check=False, capture_output=True, text=True, timeout=30)
        print(f"TestSSL: Scan completed for {host}")
        return out if os.path.exists(out) else None
    except subprocess.TimeoutExpired:
        print(f"TestSSL: Scan timed out for {host} - killing process")
        return None
    except FileNotFoundError:
        print(f"TestSSL: testssl.sh not found - skipping TLS scan")
        return None
    except Exception as e:
        print(f"TestSSL: Error scanning {host}: {e}")
        return None

def run_sslyze(host:str)->dict:
    res={}
    try:
        # First, do a quick connectivity test to avoid hanging
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # 5 second timeout
        try:
            result = sock.connect_ex((host, 443))
            sock.close()
            if result != 0:
                print(f"SSLyze: Port 443 not accessible on {host} - skipping TLS analysis")
                res["error"] = "Port 443 not accessible"
                return res
        except Exception as e:
            print(f"SSLyze: Connection test failed for {host}:443 - {e}")
            res["error"] = "Connection test failed"
            return res
        
        # If we can connect, proceed with SSLyze
        loc = ServerNetworkLocation(hostname=host, port=443)
        scanner = Scanner()
        scanner.queue_scans([ServerScanRequest(server_location=loc)])
        
        for scan_result in scanner.get_results():
            # Check if scan was successful
            if scan_result.scan_status.name == "ERROR_NO_CONNECTIVITY":
                print(f"SSLyze: No connectivity to {host}:443 - port may be filtered/closed")
                res["error"] = "No connectivity - port filtered or closed"
                continue
                
            if scan_result.scan_status.name != "COMPLETED":
                print(f"SSLyze: Scan failed for {host}:443 - {scan_result.scan_status.name}")
                res["error"] = f"Scan failed: {scan_result.scan_status.name}"
                continue
            
            # Extract TLS information from scan result
            if hasattr(scan_result, 'scan_result') and scan_result.scan_result:
                scan_data = scan_result.scan_result
                
                # Get certificate information
                if hasattr(scan_data, 'certificate_info') and scan_data.certificate_info:
                    cert_attempt = scan_data.certificate_info
                    if cert_attempt.status.name == "COMPLETED" and cert_attempt.result:
                        cert_result = cert_attempt.result
                        deployments = cert_result.certificate_deployments
                        if deployments:
                            # Get info from first deployment
                            deployment = deployments[0]
                            if deployment.received_certificate_chain:
                                leaf_cert = deployment.received_certificate_chain[0]
                                res["certificate_subject"] = str(leaf_cert.subject)
                                res["certificate_issuer"] = str(leaf_cert.issuer)
                                # Check if certificate is currently valid
                                from datetime import datetime
                                now = datetime.utcnow()
                                try:
                                    # Use UTC datetime properties if available
                                    not_before = leaf_cert.not_valid_before_utc if hasattr(leaf_cert, 'not_valid_before_utc') else leaf_cert.not_valid_before
                                    not_after = leaf_cert.not_valid_after_utc if hasattr(leaf_cert, 'not_valid_after_utc') else leaf_cert.not_valid_after
                                    res["certificate_valid"] = not_before <= now <= not_after
                                except:
                                    # Fallback to basic validation
                                    res["certificate_valid"] = True
                
                # Get cipher suites information
                cipher_attrs = ['ssl_2_0_cipher_suites', 'ssl_3_0_cipher_suites', 'tls_1_0_cipher_suites', 'tls_1_1_cipher_suites', 'tls_1_2_cipher_suites', 'tls_1_3_cipher_suites']
                total_ciphers = 0
                for attr in cipher_attrs:
                    if hasattr(scan_data, attr):
                        cipher_attempt = getattr(scan_data, attr)
                        if cipher_attempt.status.name == "COMPLETED" and cipher_attempt.result:
                            total_ciphers += len(cipher_attempt.result.accepted_cipher_suites)
                if total_ciphers > 0:
                    res["total_cipher_suites"] = total_ciphers
                
                # Get TLS version support
                tls_versions = []
                for version in ['tls_1_0', 'tls_1_1', 'tls_1_2', 'tls_1_3']:
                    version_attr = f"{version}_cipher_suites"
                    if hasattr(scan_data, version_attr):
                        version_attempt = getattr(scan_data, version_attr)
                        if version_attempt.status.name == "COMPLETED" and version_attempt.result and version_attempt.result.accepted_cipher_suites:
                            tls_versions.append(version.upper().replace('_', '.'))
                if tls_versions:
                    res["supported_tls_versions"] = tls_versions
                
                print(f"SSLyze: Successfully analyzed TLS configuration for {host}:443")
            else:
                res["error"] = "No scan data available"
                
    except Exception as e:
        print(f"SSLyze failed for {host}: {e}")
        res["error"] = str(e)
    return res
