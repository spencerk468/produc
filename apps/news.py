# apps/news.py

"""
News App - Show Today's New York Times Front Page
Downloads the image from Freedom Forum's static NYT page.
"""

import os
import warnings
from io import BytesIO
from PIL import Image
import requests
from bs4 import BeautifulSoup

# Suppress all warnings (including version mismatch warnings)
warnings.filterwarnings("ignore")

# Constants
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
IMAGES_DIR = os.path.join(PROJECT_ROOT, 'apps', 'news_images')
OUTPUT_PATH = os.path.join(IMAGES_DIR, 'front_page.png')
NYT_URL = "https://frontpages.freedomforum.org/newspapers/ny_nyt-The_New_York_Times"


def fetch_article():
    placeholder = Image.new('RGB', (800, 480), 'white')
    try:
        resp = requests.get(NYT_URL, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Select the best-quality front page image
        img_tag = soup.find("img", src=lambda s: s and "front-page-large.jpg" in s)
        if not img_tag:
            raise RuntimeError("NYT front page image not found.")

        img_url = img_tag['src']
        full_img_url = img_url if img_url.startswith("http") else f"https://frontpages.freedomforum.org{img_url}"

        img_resp = requests.get(full_img_url, timeout=10)
        img_resp.raise_for_status()
        img = Image.open(BytesIO(img_resp.content)).convert("RGB")

        os.makedirs(IMAGES_DIR, exist_ok=True)
        img.save(OUTPUT_PATH)

        return {
            'title': "The New York Times",
            'description': "Today's Front Page",
            'url': NYT_URL,
            'image': img
        }

    except Exception:
        return {'title': 'Error', 'description': 'Could not fetch NYT front page.', 'url': '', 'image': placeholder}


def send_to_inky(image, output_path=None):
    path = output_path or OUTPUT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.save(path)
