import http.server
import socketserver

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("That's my first Python App. Serving at port", PORT)
    print("promqna1")
    httpd.serve_forever()
