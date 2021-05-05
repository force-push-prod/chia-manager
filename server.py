# from livereload import Server
# server = Server()
# server.watch('html/*')
# server.serve(root='html/')

from http.server import BaseHTTPRequestHandler, HTTPServer

hostName = 'localhost'
serverPort = 5500

# https://pythonbasics.org/webserver/

from helper import *

FILES = { 'graph.js': '', 'index.html': '', 'helpers.js': ''}
def load_files():
    for file in FILES.keys():
        with open('html/' + file, 'r') as content:
            FILES[file] = content.read()
load_files()

class MyServer(BaseHTTPRequestHandler):

    def do_GET(self):
        if self.path == '/':
            load_files()
            self.respond(FILES['index.html'], 'html')

        if self.path.strip('/') in FILES.keys():
            load_files()
            self.respond(FILES[self.path.strip('/')], 'js')

        if self.path == '/data':
            x = run_shell_get_stdout('cat ~/mbp2-disk1-1.log | python ~/Developer/chia-manager/main.py js')
            self.respond(x)


    def do_PUT(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()


    def respond(self, body, content_type='json'):
        self.send_response(200)
        match content_type:
            case 'html':
                self.send_header('Content-type', 'text/html')
            case 'js':
                self.send_header('Content-type', 'application/javascript')
            case 'json':
                self.send_header('Content-type', 'application/json')
        self.end_headers()

        if not isinstance(body, str):
            body = convert_object_to_str(body)

        self.wfile.write(bytes(body, 'utf-8'))


if __name__ == '__main__':
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print('Server started http://%s:%s' % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print('Server stopped.')
