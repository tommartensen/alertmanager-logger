#!/usr/bin/python3

import json
import logging
import os
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

from pythonjsonlogger import jsonlogger


class HTTPError(Exception):
    def __init__(self, message, response_code):
        self.message = message
        self.response_code = response_code


def setup_logger(log_level):
    logger = logging.getLogger()
    logger.setLevel(log_level)

    logHandler = logging.StreamHandler()
    logHandler.setFormatter(jsonlogger.JsonFormatter())
    logger.addHandler(logHandler)
    return logger


def get_current_time():
    local_time = datetime.now(timezone.utc).astimezone()
    return local_time.isoformat()


def is_authenticated(function):
    def authentication_wrapper(server):
        authorization_header = server.headers.get("Authorization", "")
        if not authorization_header.startswith("Bearer "):
            raise HTTPError("Authentication required", 401)
        token = authorization_header.split()[1]
        if not token == AUTH_TOKEN:
            raise HTTPError("Bad credentials", 401)
        function(server)
    return authentication_wrapper


def handle_errors(function):
    def error_handling_wrapper(server):
        try:
            function(server)
        except HTTPError as e:
            server.set_response(e.response_code, e.message)
            logger.error({"message": "error", "log-level": "error", "response-code": e.response_code, "log": e.message, "time": get_current_time()})
    return error_handling_wrapper


class Server(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        request_method, request_path, protocol_version = args[0].split(" ")
        response_code = args[1]
        logger.info({
            "time": get_current_time(),
            "message": "request",
            "log-level": "info",
            "client_address": self.client_address[0],
            "request_method": request_method,
            "request_path": request_path,
            "protocol_version": protocol_version,
            "response_code": response_code,
        })

    def set_response(self, code=200, text="OK"):
        self.send_response(code)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(text.encode('utf-8'))

    @staticmethod
    def is_valid_alert(alert_data):
        for x in ["receiver", "status", "alerts", "groupLabels"]:
            if not x in alert_data.keys():
                return False
        if not alert_data["status"] in ["firing", "resolved"]:
            return False
        return True

    def parse_alert_from_request(self):
        content_length = int(self.headers["Content-Length"])
        if not content_length:
            raise HTTPError("No alert payload", 400)
        try:
            alert = json.loads(self.rfile.read(content_length))
        except Exception:
            raise HTTPError("Bad payload", 400)
        return alert

    @handle_errors
    @is_authenticated
    def do_POST(self):
        alert = self.parse_alert_from_request()
        if not Server.is_valid_alert(alert):
            raise HTTPError(f"Not a valid alert: {json.dumps(alert)}", 400)
        logger.info({"message": "alert", "time": get_current_time(), **alert})
        self.set_response()


def run(host, port, server_class=HTTPServer, handler_class=Server, ):
    server_address = (host, port)
    httpd = server_class(server_address, handler_class)
    logger.info({
        "message": "system",
        "log-level": "info",
        "log": "Server started",
        "time": get_current_time()
    })
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()
        logger.info({"message": "system", "log-level": "info", "log": "Server stopped", "time": get_current_time()})

if __name__ == '__main__':
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    logger = setup_logger(log_level=LOG_LEVEL)

    AUTH_TOKEN = os.environ.get('AUTH_TOKEN')
    if not AUTH_TOKEN:
        logger.fatal({"message": "system", "log-level": "fatal", "log": "AUTH_TOKEN environment variable not set", "time": get_current_time()})
        sys.exit(1)
    HOST = os.environ.get('HOST', "")
    PORT = os.environ.get('PORT', 5001)
    run(host=HOST, port=PORT)
