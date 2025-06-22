#!/usr/bin/env python3

import cgi
import cgitb
import requests
import html

cgitb.enable()
print("Content-Type: text/html\n")

form = cgi.FieldStorage()
query = form.getvalue("q")

if not query:
    print("<p>No query provided.</p>")
    exit()

api_key = ""  # Replace with your SerpAPI key
params = {
    "q": query,
    "engine": "google",
    "api_key": api_key,
    "num": 10
}

try:
    response = requests.get("https://serpapi.com/search", params=params)
    results = response.json()

    if "organic_results" in results:
        print("<ol>")
        for result in results["organic_results"][:10]:
            title = result.get("title", "No Title")
            link = result.get("link", "#")
            print(f'<li><a href="{link}" target="_blank">{html.escape(title)}</a></li>')
        print("</ol>")
    else:
        print("<p>No results found or API limit reached.</p>")

except Exception as e:
    print(f"<p>Error fetching results: {html.escape(str(e))}</p>")
