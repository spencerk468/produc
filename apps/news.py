"""
apps/news.py

News App - Positive News via NewsAPI
Triggered by MacroPad key 7.
Fetches the latest positive news article details (title, description, URL, image) using NewsAPI
and saves the article image to apps/news_images/front_page.png.
Requires your API key in apps/news_images/news_api.txt.
"""
import os
from io import BytesIO
from PIL import Image
import requests

# Paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR    = os.path.join(PROJECT_ROOT, 'apps', 'news_images')
OUTPUT_PATH   = os.path.join(IMAGES_DIR, 'front_page.png')
API_KEY_PATH  = os.path.join(IMAGES_DIR, 'news_api.txt')

# NewsAPI endpoint
NEWSAPI_QUERY = 'https://newsapi.org/v2/everything'

# Load API key
try:
    with open(API_KEY_PATH) as f:
        NEWSAPI_KEY = f.read().strip()
except Exception:
    NEWSAPI_KEY = None
    print(f"Could not load API key from {API_KEY_PATH}")

# Query params
QUERY_PARAMS = {
    'q': 'positive news',
    'language': 'en',
    'pageSize': 1,
    'sortBy': 'publishedAt'
}


def fetch_article():
    """
    Fetches top 'positive news' article via NewsAPI.
    Returns dict: {title, description, url, image:PIL}
    """
    placeholder = Image.new('RGB', (800,480), 'white')
    if not NEWSAPI_KEY:
        return {'title': 'No API Key', 'description': '', 'url': '', 'image': placeholder}

    params = QUERY_PARAMS.copy()
    params['apiKey'] = NEWSAPI_KEY
    try:
        resp = requests.get(NEWSAPI_QUERY, params=params, timeout=10)
        resp.raise_for_status()
        articles = resp.json().get('articles') or []
        if not articles:
            raise RuntimeError('No articles')
        art = articles[0]
        title = art.get('title','')
        desc  = art.get('description','')
        url   = art.get('url','')
        img_url = art.get('urlToImage')
        if img_url:
            try:
                r = requests.get(img_url, timeout=10)
                r.raise_for_status()
                img = Image.open(BytesIO(r.content))
            except:
                img = placeholder
        else:
            img = placeholder
        # Save locally
        os.makedirs(IMAGES_DIR, exist_ok=True)
        img.save(OUTPUT_PATH)
        return {'title': title, 'description': desc, 'url': url, 'image': img}
    except Exception as e:
        print(f"Fetch article failed: {e}")
        return {'title': 'Error', 'description': str(e), 'url': '', 'image': placeholder}


def send_to_inky(image, output_path=None):
    """
    Saves image locally (front_page.png).
    """
    path = output_path or OUTPUT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
    print(f"Saved to {path}")

# No imports from apps.news here to avoid circular references
