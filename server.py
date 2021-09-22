#  coding: utf-8 
import os
import socketserver
import http.client
import mimetypes
from urllib.parse import urlparse, unquote

# http.client prodives a dictionary of Status Codes and Reasons

# Copyright 2013 Abram Hindle, Eddie Antonio Santos
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

BLANK_LINE = b"\r\n"
BASE_DIR = "www/"

class MyWebServer(socketserver.BaseRequestHandler):
    headers = {
        'Server': 'MyLittleServer',
        'Content-Type': 'text/html',
    }

    def response_status(self, status_code):
        # Returns first line of response
        reason = http.client.responses[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode()

    def response_headers(self, extra_headers=None):
        headers_copy = self.headers.copy() 

        if extra_headers:
            headers_copy.update(extra_headers)

        headers = ""

        for header_type in headers_copy:
            headers += "%s: %s\r\n" % (header_type, headers_copy[header_type])

        return headers.encode()

    def handle(self):
        self.data = self.request.recv(1024).strip()
        print ("Got a request of: %s\n" % self.data)

        request = HTTPRequest(self.data)
        print("request is %s" % (request))

        try:
            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = self.handle_invalid_method()

        response = handler(request)

        print(response)
        self.request.sendall(response)

    def handle_GET(self, request):
        filename = unquote(request.uri)
        file_path = self.check_file_location(filename)
        print(file_path)
        print("requestttttttt")

        if file_path == "Forbidden":
            return self.response_403()

        if file_path == "Not Found":
            return self.response_404()

        try:
            file = open(file_path, 'rb')
            response_body = file.read()
            content_type = mimetypes.guess_type(file_path)[0] or 'text/html'
            extra_headers = {'Content-Type': content_type}

            return self.response_200(response_body=response_body, extra_headers=extra_headers)
        except Exception as e:
            return self.response_403()
        finally:
            file.close()

    def handle_invalid_method(self):
        self.response_405()

    def check_file_location(self, filename):
        print(filename)
        print("filename")
        base_dir = os.path.abspath("www/")
        file_path = os.path.abspath("www/" + filename)

        print(file_path)
        print("path hello")

        # File out of scope
        if (file_path.find(base_dir) != 0):
            return "Forbidden"

        # Given Filepath does not exist
        if (not os.path.exists(file_path)):
            return "Not Found"

        # path to existent file
        if (os.path.exists(file_path) and os.path.isfile(file_path) and filename[-1] != "/"):
            return file_path

        # path to directory, must end in "/"
        # add index.html endint -> recurse  
        if (os.path.exists(file_path) and os.path.isdir(file_path) and filename[-1] == "/"):
            return self.check_file_location(filename + "/index.html")

        return "Not Found"

    def response_200(self, response_body, extra_headers=None):
        status_code = 200
        response_status = self.response_status(status_code=status_code)
        
        return self.compose_response(response_status=response_status, extra_headers=extra_headers, response_body=response_body)

    def response_403(self, extra_headers=None):
        status_code = 403
        response_status = self.response_status(status_code=status_code)
        response_body = str.encode('<h1>%i %s</h1>' % (status_code, http.client.responses[status_code]))
        
        return self.compose_response(response_status=response_status, extra_headers=extra_headers, response_body=response_body)

    def response_404(self, extra_headers=None):
        status_code = 404
        response_status = self.response_status(status_code=status_code)
        response_body = str.encode('<h1>%i %s</h1>' % (status_code, http.client.responses[status_code]))
        
        return self.compose_response(response_status=response_status, extra_headers=extra_headers, response_body=response_body)

    def response_405(self, extra_headers=None):
        status_code = 405
        response_status = self.response_status(status_code=status_code)
        response_body = str.encode('<h1>%i %s</h1>' % (status_code, http.client.responses[status_code]))

        return self.compose_response(response_status=response_status, extra_headers=extra_headers, response_body=response_body)

    def compose_response(self, response_status, extra_headers, response_body):
        response_headers = self.response_headers(extra_headers=extra_headers)
        return b"".join([response_status, response_headers, BLANK_LINE, response_body])

class HTTPRequest:
    def __init__(self, HTTPRequest):
        self.method = None
        self.uri = None
        self.http_version = "1.1"

        # extract values by parsing
        self.parse(HTTPRequest)

    def parse(self, request):
        lines = request.split(b"\r\n")
        params = lines[0].decode().split(" ")

        self.method = params[0]
        self.uri = params[1]

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server;
    server.serve_forever()
