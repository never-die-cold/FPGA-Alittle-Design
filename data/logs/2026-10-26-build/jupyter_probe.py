import re, sys
try:
    import requests
except Exception as e:
    print("NO_REQUESTS", repr(e)); sys.exit(2)
base = "http://192.168.50.99:9090"
s = requests.Session()
try:
    r = s.get(base + "/login", timeout=10)
    print("login_page", r.status_code, len(r.text))
    m = re.search(r'name="_xsrf" value="([^"]+)"', r.text)
    print("xsrf", bool(m))
    if m:
        r = s.post(base + "/login?next=%2F", data={"_xsrf": m.group(1), "password": "xilinx"}, timeout=10, allow_redirects=False)
        print("login_post", r.status_code, r.headers.get("Location"))
        print("cookies", list(s.cookies.keys()))
    r = s.get(base + "/api/terminals", timeout=10)
    print("terminals", r.status_code, r.text[:200])
    r = s.get(base + "/api/status", timeout=10)
    print("status", r.status_code, r.text[:200])
except Exception as e:
    print("JUPYTER_FAIL", repr(e))
