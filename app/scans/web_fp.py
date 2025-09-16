import subprocess, json

def whatweb(url:str)->dict:
    try:
        cp = subprocess.run(["whatweb","-a","1","-q",url,"--log-json=-"], capture_output=True, text=True)
        arr = json.loads(cp.stdout)
        if isinstance(arr, list) and arr:
            plugins = list(arr[0].get("plugins",{}).keys())
            return {"plugins": plugins}
    except FileNotFoundError:
        # whatweb not installed, use basic HTTP fingerprinting
        print(f"Info: whatweb not found, using basic HTTP fingerprinting for {url}")
        try:
            import requests
            # Use shorter timeout and connection timeout to prevent hanging
            response = requests.get(url, timeout=(3, 5), verify=False)
            plugins = []
            if response.status_code == 200:
                plugins.append("http_server")
                server = response.headers.get('Server', '')
                if server:
                    plugins.append(f"server_{server.lower().replace(' ', '_')}")
                content_type = response.headers.get('Content-Type', '')
                if 'text/html' in content_type:
                    plugins.append("html_content")
                if 'text/plain' in content_type:
                    plugins.append("plain_text")
            return {"plugins": plugins}
        except requests.exceptions.ConnectTimeout:
            print(f"Info: Connection timeout for {url} - port likely filtered")
            return {"plugins": ["connection_timeout"]}
        except requests.exceptions.ReadTimeout:
            print(f"Info: Read timeout for {url} - service may be slow")
            return {"plugins": ["read_timeout"]}
        except requests.exceptions.ConnectionError:
            print(f"Info: Connection refused for {url} - port likely closed/filtered")
            return {"plugins": ["connection_refused"]}
        except Exception as e:
            print(f"Info: HTTP fingerprinting failed for {url}: {e}")
            return {"plugins": ["unknown_web_server"]}
    except Exception as e:
        print(f"Warning: whatweb failed for {url}: {e}")
        pass
    return {"plugins":[]}
