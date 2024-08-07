import mimetypes
import pathlib
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
from datetime import datetime
import socket
from threading import Thread
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class HttpHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length'])) + ('&date=' + str(datetime.now())).encode()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # todo: винести всі мережеві координати в файл параметрів
            ip = 'localhost'
            port = 5000
            sock.connect((ip, port))
            sock.sendto(data, (ip, port))

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def http_run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('', 3000)
    # todo: винести всі мережеві координати в файл параметрів
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


def socket_run(ip='localhost', port=5000):
    # todo: винести всі мережеві координати в файл параметрів
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    sock.bind(server)

    # Create a connection to the MongoDB
    uri = "mongodb://mongo:27017/"
    # uri = "mongodb://localhost:27017/" #27017
    client = MongoClient(uri, server_api=ServerApi('1'))
    db = client.messages

    # Send a ping to confirm a successful connection
    # try:
    #     client.admin.command('ping')
    #     print("Pinged your deployment. You successfully connected to MongoDB!\n")
    # except Exception as e:
    #     print(e)

    try:
        while True:
            data, address = sock.recvfrom(1024)
            # print(f'Received data: {data.decode()} from: {address}')
            data_parse = urllib.parse.unquote_plus(data.decode())
            # print(data_parse)
            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
            # print(data_dict)
            db.messages.insert_one(data_dict)
    except Exception as e:
        print(f'Destroy server. Error is {e}')
    finally:
        sock.close()


if __name__ == '__main__':
    http_thread = Thread(target=http_run)
    socket_thread = Thread(target=socket_run)
    socket_thread.start()
    http_thread.start()
