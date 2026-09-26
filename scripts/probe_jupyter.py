"""Check a campaign Jupyter server and shut it down without printing its token."""
import argparse
import json
import re
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("log", type=Path)
args = parser.parse_args()
text = args.log.read_text()
matches = re.findall(r"http://([^/\s:]+):(\d+)/lab\?token=([a-zA-Z0-9]+)", text)
host, port, token = next(item for item in matches if item[0] not in ("localhost", "127.0.0.1"))
base = f"http://{host}:{port}"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
headers = {"Authorization": "token " + token}
with opener.open(urllib.request.Request(base + "/api", headers=headers), timeout=15) as response:
    print(json.dumps({"status": response.status, "api": json.load(response)}))
with opener.open(urllib.request.Request(base + "/api/shutdown", headers=headers, data=b"", method="POST"), timeout=15) as response:
    print(json.dumps({"shutdown_status": response.status}))
