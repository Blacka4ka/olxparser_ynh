from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
import urllib.parse
import re

app = Flask(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_prices_links_titles_from_url(url, pages=1):
    all_results = []
    for page in range(1, pages + 1):
        page_url = f"{url}?page={page}"
        resp = requests.get(page_url, headers=HEADERS)
        if resp.status_code != 200:
            continue
        soup = BeautifulSoup(resp.text, "html.parser")
        listings = soup.select("div[data-testid='listing-grid'] div[data-cy='l-card']")
        for listing in listings:
            price_tag = listing.select_one("p[data-testid='ad-price']")
            link_tag = listing.find("a", href=True)
            title_tag = listing.select_one("a[data-cy='listing-ad-title']")
            if not price_tag or not link_tag or not title_tag:
                continue
            price_text = price_tag.get_text(strip=True)
            match = re.search(r"(\d[\d\s]*)", price_text.replace('\xa0', ' '))
            price = int(match.group(1).replace(" ", "")) if match else 0
            link = "https://www.olx.ua" + link_tag['href'].split('#')[0]
            title = title_tag.get_text(strip=True)
            all_results.append({"price": price, "title": title, "link": link})
    return all_results

HTML_TEMPLATE = '''
<!doctype html>
<html lang="uk">
<head>
  <meta charset="utf-8">
  <title>OLX Парсер</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2em; }
    table { border-collapse: collapse; width: 100%; max-width: 900px; }
    th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
    th { background: #f2f2f2; }
    input[type="text"] { width: 300px; padding: 6px; }
    input[type="submit"] { padding: 6px 12px; }
  </style>
</head>
<body>
<h2>Парсер OLX</h2>
<form method="get">
  <input name="query" placeholder="Введіть запит" value="{{query|default('')}}" autocomplete="off" required>
  <input type="submit" value="Шукати">
</form>

{% if results %}
<h3>Результати для "{{query}}"</h3>
<table>
<tr><th>#</th><th>Ціна</th><th>Назва</th><th>Посилання</th></tr>
{% for i, item in enumerate(results, 1) %}
<tr>
  <td>{{i}}</td>
  <td>{{item.price if item.price > 0 else "Договірна"}} грн</td>
  <td>{{item.title}}</td>
  <td><a href="{{item.link}}" target="_blank" rel="noopener noreferrer">Перейти</a></td>
</tr>
{% endfor %}
</table>
{% endif %}
</body>
</html>
'''

@app.route("/", methods=["GET"])
def home():
    query = request.args.get("query", "").strip()
    results = []
    if query:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.olx.ua/uk/list/q-{encoded_query}/"
        results = get_prices_links_titles_from_url(url, pages=2)
    return render_template_string(HTML_TEMPLATE, query=query, results=results)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
