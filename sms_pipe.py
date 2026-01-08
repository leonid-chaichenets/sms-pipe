#!/usr/bin/env python3

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time

HOST = "127.0.0.1"
PORT = 8765

AVAILABLE_FIELDS = {
    "from": str,
    "text": str,
    "sentStamp": int,
    "receivedStamp": int,
    "sim": str,
}

REQUIRED_FIELDS = {"from", "text", "sentStamp", "receivedStamp"}

class SMSHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(length)

            print("\n=== NEW REQUEST ===")
            print(f"Path: {self.path}")

            print("\n--- Headers ---")
            for k, v in self.headers.items():
                print(f"{k}: {v}")

            # --- Decode body ---
            try:
                body = raw.decode("utf-8")
            except UnicodeDecodeError:
                self._bad_request("Body is not valid UTF-8")
                return

            # --- Parse JSON ---
            try:
                data = json.loads(body)
            except json.JSONDecodeError as e:
                self._bad_request(f"Invalid JSON: {e}")
                return

            # --- Parse fields ---
            errors = []
            for field in data:
                if field not in AVAILABLE_FIELDS:
                    errors.append(f"unknown field '{field}'")
                elif not isinstance(data[field], AVAILABLE_FIELDS[field]):
                    errors.append(
                        f"field '{field}' has wrong type "
                        f"(expected {AVAILABLE_FIELDS[field]}, got {type(data[field])})"
                    )

            # --- Check fields ---
            missing = REQUIRED_FIELDS - data.keys()
            for f in missing:
                errors.append(f"missing required field: {f}")

            # --- Handle errors ---
            if errors:
                self._bad_request("; ".join(errors))
                return

            print("\n=== SMS RECEIVED ===")
            for k, v in data.items():
                print(f"{k}: {v}")
            print("====================\n", flush = True)
            print("=== END REQUEST ===\n", flush = True)

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK\n")

        except Exception as e:
            # Always respond, even on error
            print(f"ERROR: {e}", flush = True)
            self.send_response(500)
            self.end_headers()

    def _bad_request(self, msg: str):
        print(f"BAD REQUEST: {msg}", flush = True)
        self.send_response(400)
        self.end_headers()
        self.wfile.write(msg.encode("utf-8"))

    def log_message(self, fmt, *args):
        # Disable default access logging
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), SMSHandler)
    print(f"Listening on http://{HOST}:{PORT}", flush=True)
    server.serve_forever()
