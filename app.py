from flask import Flask, render_template_string, request
import requests
import threading
import time
import math
from bs4 import BeautifulSoup

app = Flask(__name__)

# API Keys
NEWS_API_KEY = "1e84fd043dc14c318b730dbcd702b137"
GNEWS_API_KEY = "b2f0b1d5c079c3a71b4c8ef304e06645"
MARKETAUX_API_KEY = "2uLrGu0LRNY8nT6OO6pKgiolYZHK5XxvdNxPy924"

cached_news = []

def extract_symbol(keywords):
    for k in keywords:
        k_low = k.lower()
        if 'bitcoin' in k_low or 'crypto' in k_low:
            return 'bitcoin'
        if 'ethereum' in k_low:
            return 'ethereum'
    return None

def fetch_all_news():
    global cached_news
    news_items = []

    # NewsAPI
    try:
        r1 = requests.get(f"https://newsapi.org/v2/top-headlines?category=business&language=id&apiKey={NEWS_API_KEY}")
        for article in r1.json().get('articles', []):
            news_items.append({
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'image': article['urlToImage'],
                'source': article['source']['name'],
                'category': 'ekonomi',
                'symbol': None
            })
    except:
        pass

    # GNews
    try:
        r2 = requests.get(f"https://gnews.io/api/v4/top-headlines?topic=business&lang=id&token={GNEWS_API_KEY}")
        for article in r2.json().get('articles', []):
            news_items.append({
                'title': article['title'],
                'description': article['description'],
                'url': article['url'],
                'image': article['image'],
                'source': article['source']['name'],
                'category': 'ekonomi global',
                'symbol': None
            })
    except:
        pass

    # Marketaux
    try:
        r3 = requests.get(f"https://api.marketaux.com/v1/news/all?language=id&filter_entities=true&api_token={MARKETAUX_API_KEY}")
        for article in r3.json().get('data', []):
            keywords = article.get('keywords', []) or []
            kategori = 'saham'
            if any('crypto' in k.lower() for k in keywords):
                kategori = 'crypto'
            elif any('forex' in k.lower() for k in keywords):
                kategori = 'forex'
            symbol = extract_symbol(keywords)

            news_items.append({
                'title': article['title'],
                'description': article.get('description', ''),
                'url': article['url'],
                'image': article.get('image_url'),
                'source': article.get('source', {}).get('name', 'Marketaux'),
                'category': kategori,
                'symbol': symbol
            })
    except:
        pass

    # Bloomberg Asia
    try:
        r4 = requests.get("https://www.bloomberg.com/asia")
        if r4.ok:
            soup = BeautifulSoup(r4.text, 'html.parser')
            for item in soup.select('article'):
                link = item.find('a')
                title = link.text.strip() if link else ''
                url = 'https://www.bloomberg.com' + link['href'] if link and link.has_attr('href') else ''
                image = item.find('img')
                image_url = image['src'] if image and image.has_attr('src') else ''
                if title:
                    news_items.append({
                        'title': title,
                        'description': '',
                        'url': url,
                        'image': image_url,
                        'source': 'Bloomberg Asia',
                        'category': 'ekonomi asia',
                        'symbol': None
                    })
    except:
        pass

    cached_news = sorted(news_items, key=lambda x: x['title'])

def refresh_loop():
    while True:
        fetch_all_news()
        time.sleep(1800)

threading.Thread(target=refresh_loop, daemon=True).start()

@app.route('/')
def index():
    selected_category = request.args.get('kategori')
    selected_source = request.args.get('sumber')
    search_query = request.args.get('search', '').lower()
    page = int(request.args.get('page', 1))
    per_page = 10

    filtered = cached_news
    if selected_category:
        filtered = [n for n in filtered if n['category'] == selected_category]
    if selected_source:
        filtered = [n for n in filtered if selected_source.lower() in n['source'].lower()]
    if search_query:
        filtered = [n for n in filtered if search_query in n['title'].lower() or (n['description'] and search_query in n['description'].lower())]

    total_pages = math.ceil(len(filtered) / per_page)
    news_page = filtered[(page-1)*per_page : page*per_page]

    categories = sorted(set(n['category'] for n in cached_news))
    sources = sorted(set(n['source'] for n in cached_news))

    return render_template_string(TEMPLATE_INDEX, news_items=news_page,
                                  categories=categories, sources=sources,
                                  selected_category=selected_category,
                                  selected_source=selected_source,
                                  search_query=search_query,
                                  page=page, total_pages=total_pages)

@app.route('/chart')
def chart():
    symbol = request.args.get('symbol')
    labels, values = [], []
    if symbol:
        data = requests.get(
            f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart?vs_currency=usd&days=7"
        ).json()
        prices = data.get('prices', [])
        labels = [time.strftime('%m-%d', time.gmtime(p[0]/1000)) for p in prices]
        values = [p[1] for p in prices]
    return render_template_string(TEMPLATE_CHART, symbol=symbol, labels=labels, values=values)

# Template HTML disimpan langsung di bawah sini
TEMPLATE_INDEX = '''
<!DOCTYPE html>
<html>
<head>
    <title>Globe - Berita Ekonomi</title>
    <style>
        body { font-family: Arial; background: #f6f6f6; margin: 0; padding: 0; }
        header { background: #1a1a1a; color: white; padding: 10px 20px; display: flex; align-items: center; }
        header img { height: 40px; margin-right: 15px; }
        .container { padding: 20px; }
        .news-card { background: white; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .news-card img { width: 100%; max-height: 200px; object-fit: cover; border-radius: 4px; }
        .news-meta { font-size: 0.9em; color: gray; }
        nav a { margin: 0 5px; }
    </style>
</head>
<body>
    <header>
        <img src="/static/logo.png" alt="Globe">
        <h1>Globe - Berita Ekonomi</h1>
    </header>
    <div class="container">
        <form method="get">
            <input type="text" name="search" placeholder="Cari..." value="{{ search_query }}">
            <select name="kategori">
                <option value="">Semua Kategori</option>
                {% for cat in categories %}
                    <option value="{{ cat }}" {% if selected_category == cat %}selected{% endif %}>{{ cat }}</option>
                {% endfor %}
            </select>
            <select name="sumber">
                <option value="">Semua Sumber</option>
                {% for s in sources %}
                    <option value="{{ s }}" {% if selected_source == s %}selected{% endif %}>{{ s }}</option>
                {% endfor %}
            </select>
            <button type="submit">Filter</button>
        </form>

        {% for item in news_items %}
        <div class="news-card">
            <h2><a href="{{ item.url }}" target="_blank">{{ item.title }}</a></h2>
            {% if item.image %}
                <img src="{{ item.image }}">
            {% endif %}
            <p>{{ item.description }}</p>
            <p class="news-meta">{{ item.source }} | {{ item.category }}</p>
            {% if item.symbol %}
                <a href="/chart?symbol={{ item.symbol }}">Lihat Chart {{ item.symbol }}</a>
            {% endif %}
        </div>
        {% endfor %}

        <nav>
            {% if page > 1 %}
                <a href="?page={{ page-1 }}&kategori={{ selected_category }}&sumber={{ selected_source }}&search={{ search_query }}">Sebelumnya</a>
            {% endif %}
            Halaman {{ page }} dari {{ total_pages }}
            {% if page < total_pages %}
                <a href="?page={{ page+1 }}&kategori={{ selected_category }}&sumber={{ selected_source }}&search={{ search_query }}">Berikutnya</a>
            {% endif %}
        </nav>
    </div>
</body>
</html>
'''

TEMPLATE_CHART = '''
<!DOCTYPE html>
<html>
<head>
    <title>Chart {{ symbol }}</title>
</head>
<body>
    <h1>Harga {{ symbol }}</h1>
    <ul>
    {% for l, v in zip(labels, values) %}
        <li>{{ l }}: ${{ v }}</li>
    {% endfor %}
    </ul>
    <a href="/">Kembali</a>
</body>
</html>
'''

if __name__ == '__main__':
    fetch_all_news()
    app.run(debug=True, port=5000)
