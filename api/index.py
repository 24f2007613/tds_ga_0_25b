import json
import math
from http.server import BaseHTTPRequestHandler
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "telemetry.json"


def percentile(values, p):
    """Linear-interpolated percentile (same convention as NumPy's default)."""
    ordered = sorted(values)
    if not ordered:
        return 0.0
    if len(ordered) == 1:
        return float(ordered[0])
    index = (len(ordered) - 1) * p / 100.0
    lo = math.floor(index)
    hi = math.ceil(index)
    if lo == hi:
        return float(ordered[lo])
    return float(ordered[lo] + (ordered[hi] - ordered[lo]) * (index - lo))


with DATA_PATH.open("r", encoding="utf-8") as f:
    TELEMETRY = json.load(f)


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Expose-Headers", "Access-Control-Allow-Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Max-Age", "86400")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self):
        if self.path not in ("/", "/api", "/api/index"):
            self.send_response(404)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"error":"Not found"}')
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            regions = body.get("regions")
            threshold = body.get("threshold_ms", 180)

            if not isinstance(regions, list) or not all(isinstance(r, str) for r in regions):
                raise ValueError("'regions' must be a list of strings")
            if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
                raise ValueError("'threshold_ms' must be a number")

            results = []
            for region in regions:
                rows = [row for row in TELEMETRY if row.get("region") == region]
                if not rows:
                    results.append({
                        "region": region,
                        "avg_latency": None,
                        "p95_latency": None,
                        "avg_uptime": None,
                        "breaches": 0,
                    })
                    continue

                latencies = [float(row["latency_ms"]) for row in rows]
                uptimes = [float(row["uptime_pct"]) for row in rows]
                results.append({
                    "region": region,
                    "avg_latency": round(sum(latencies) / len(latencies), 2),
                    "p95_latency": round(percentile(latencies, 95), 2),
                    "avg_uptime": round(sum(uptimes) / len(uptimes), 3),
                    "breaches": sum(1 for value in latencies if value > threshold),
                })

            payload = json.dumps({"regions": results}, separators=(",", ":")).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            payload = json.dumps({"error": str(exc)}).encode("utf-8")
            self.send_response(400)
            self._cors()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

    def log_message(self, format, *args):
        # Keep serverless logs concise.
        pass