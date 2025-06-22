import http.server
import socketserver
import os

PORT = 8000

class Handler(http.server.CGIHTTPRequestHandler):
    cgi_directories = ['/cgi-bin']

# Change the current working directory to the website directory
# Get directory from environment variable or use current directory as default
website_dir = os.environ.get('WEBSITE_DIR', os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  
os.chdir(website_dir)

# Start the server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Server started at localhost:" + str(PORT))
    httpd.serve_forever()

