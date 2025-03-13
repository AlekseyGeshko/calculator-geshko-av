from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import json
import subprocess
import structlog

from logging_conf import configure_logging

logger = None


class CalcRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query_params = urllib.parse.parse_qs(parsed_url.query)

        logger.info("request_received", method="POST", path=path, query=query_params)

        if path != "/calc":
            self.send_response(500)
            self.end_headers()
            response = {"error": "Not Found"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.warning("not_found", path=path)
            return

        content_length = int(self.headers.get("Content-Length", 0))
        if content_length == 0:
            self.send_response(500)
            self.end_headers()
            response = {"error": "Empty body"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.error("empty_body")
            return

        raw_body = self.rfile.read(content_length)
        content_type = self.headers.get("Content-Type", "")

        if "application/json" not in content_type:
            self.send_response(500)
            self.end_headers()
            response = {"error": "Invalid content type, must be application/json"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.error("invalid_content_type", content_type=content_type)
            return

        try:
            expression = json.loads(raw_body)
            if not isinstance(expression, str):
                expression = str(expression)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            response = {"error": f"Invalid JSON: {e}"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.exception("invalid_json")
            return

        use_float = False
        if "float" in query_params:
            val = query_params["float"][0].lower()
            if val == "true":
                use_float = True

        logger.info("received_expression", expression=expression, float_mode=use_float)

        cmd = ["./build/app.exe"]
        if use_float:
            cmd.append("--float")

        try:
            result = subprocess.run(
                cmd,
                input=expression,
                text=True,
                capture_output=True
            )
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            response = {"error": f"Subprocess error: {e}"}
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.exception("subprocess_run_error", cmd=cmd)
            return

        if result.returncode != 0:
            self.send_response(500)
            self.end_headers()
            response = {
                "error": "Calculation error",
                "stderr": result.stderr.strip()
            }
            self.wfile.write(json.dumps(response).encode("utf-8"))
            logger.error("calc_error", returncode=result.returncode, stderr=result.stderr)
            return
        else:
            output = result.stdout.strip()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(output).encode("utf-8"))
            logger.info("calc_success", output=output, returncode=result.returncode)


def run_server(host="0.0.0.0", port=8000):
    global logger
    logger = configure_logging()
    logger.info("server_start", host=host, port=port)

    httpd = HTTPServer((host, port), CalcRequestHandler)
    logger.info("server_listening", address=f"{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
        logger.info("server_stopped")


if __name__ == "__main__":
    run_server()
