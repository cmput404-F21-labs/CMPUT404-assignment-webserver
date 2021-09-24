#  coding: utf-8 

# http.client prodives a dictionary of Status Codes and Reasons

# Copyright 2013 Abram Hindle, Eddie Antonio Santos, Uladzimir Bondarau
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

import os
import socketserver
import http.client
import mimetypes
from urllib.parse import unquote
from time import gmtime, strftime

CARRIAGE_RETURN = b"\r\n"
BASE_DIR = "www/"
SERVER_NAME = "MyLittleServer"
BUFFER_SIZE = 1024

class MyWebServer(socketserver.BaseRequestHandler):
    def handle(self):
        self.data = self.receive_request()

        request = HTTPRequest(self.data)

        try:
            handler = getattr(self, 'handle_%s' % request.method)
        except AttributeError:
            handler = getattr(self, "handle_invalid_method")

        response = handler(request)

        self.send_response(response)
        return

    def receive_request(self):
        full_data = b''
        while True:
            data = self.request.recv(BUFFER_SIZE)
            full_data += data
            if len(data) < BUFFER_SIZE:
                break

        return full_data

    def send_response(self, response):
        self.request.sendall(response)
        return None

    def handle_GET(self, request):
        filename = unquote(request.uri)
        file_path = self.check_file_location(filename)

        my_response = HTTPResponse()
        if file_path['status'] == "Forbidden":
            # I wanted to serve 403 Forbidden when accessing out of directory
            # but looks like assignment specifiec 404 in this case
            # return my_response.response_403()
            return my_response.response_404()

        if file_path['status'] == "Not Found":
            return my_response.response_404()

        if file_path['status'] == "Redirected":
            extra_headers = {'Location': file_path['location']}
            return my_response.response_301(extra_headers=extra_headers)

        if file_path['status'] == "OK":
            try:
                file = open(file_path['location'], 'rb')
                response_body = file.read()
                content_type = mimetypes.guess_type(file_path['location'])[0] or 'text/html'
                extra_headers = {'Content-Type': content_type}

                return my_response.response_200(response_body=response_body, extra_headers=extra_headers)
            except Exception as e:
                return my_response.response_403()
            finally:
                file.close()
        else:
            return my_response.response_500()

    def handle_invalid_method(self, request=None):
        # handle not implemented methods
        
        my_response = HTTPResponse()
        return my_response.response_405()

    def check_file_location(self, filename):
        #returns a tuple indicating the file existance and possible path

        base_dir = os.path.abspath("www/")
        file_path = os.path.abspath("www/" + filename)

        # File out of scope
        if (file_path.find(base_dir) != 0):
            return {'status': "Forbidden"}

        # Given Filepath does not exist
        if (not os.path.exists(file_path)):
            return {'status': "Not Found"}

        # path to existent file
        if (os.path.exists(file_path) and os.path.isfile(file_path) and filename[-1] != "/"):
            return {'status': "OK", 'location': file_path}

        # path to directory, must end in "/"
        # add index.html endint -> recurse  
        if (os.path.exists(file_path) and os.path.isdir(file_path) and filename[-1] == "/"):
            return self.check_file_location(filename + "/index.html")

        # path to directory, does not end in "/"
        # redirect to "/"
        if (os.path.exists(file_path) and os.path.isdir(file_path) and filename[-1] != "/"):
            return {'status': "Redirected", 'location': filename + "/"}

        return {'status': "Not Found"}

class HTTPRequest:
    # Decodes HTTP request for method and uri

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

class HTTPResponse:
    # Class that does mosh of the formatting for proper HTTP response
    # Provides functions to send specific reposponses

    headers = {
        'Server': SERVER_NAME,
        'Content-Type': 'text/html',
    }

    def datetime_now(self):
        return strftime("%a, %d %b %Y %H:%M:%S GMT", gmtime())
        
    def response_status(self, status_code):
        reason = http.client.responses[status_code]
        line = "HTTP/1.1 %s %s\r\n" % (status_code, reason)

        return line.encode()

    def response_headers(self, extra_headers=None):
        # Picks static headers and appends date, optional user headers and closes connection
        headers = {"Date" : self.datetime_now()}
        headers.update(self.headers)
        headers["Connection"] = "close"

        if extra_headers:
            headers.update(extra_headers)

        headers_str = ""

        for header_type in headers:
            headers_str += "%s: %s\r\n" % (header_type, headers[header_type])

        return headers_str.encode()

    def response_200(self, response_body=None, extra_headers=None):
        status_code = 200
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)

    def response_301(self, response_body=None, extra_headers=None):
        status_code = 301
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)

    def response_403(self, response_body=None, extra_headers=None):
        status_code = 403   
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)

    def response_404(self, response_body=None, extra_headers=None):
        status_code = 404      
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)

    def response_405(self, response_body=None, extra_headers=None):
        status_code = 405
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)
    
    def response_500(self, response_body=None, extra_headers=None):
        status_code = 500
        return self.compose_response(status_code=status_code, extra_headers=extra_headers, response_body=response_body)

    def response_body_by_code(self, status_code):
        return str.encode('<h1>%i %s</h1>' % (status_code, http.client.responses[status_code]))

    def compose_response(self, status_code, extra_headers, response_body):
        response_status = self.response_status(status_code=status_code)
        response_headers = self.response_headers(extra_headers=extra_headers)
        if not response_body:
            response_body = self.response_body_by_code(status_code)

        return b"".join([response_status, response_headers, CARRIAGE_RETURN, response_body])

if __name__ == "__main__":
    HOST, PORT = "localhost", 8080

    socketserver.TCPServer.allow_reuse_address = True
    # Create the server, binding to localhost on port 8080
    server = socketserver.TCPServer((HOST, PORT), MyWebServer)

    # Activate the server;
    server.serve_forever()
