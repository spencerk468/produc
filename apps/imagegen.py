# apps/app11_imagegen.py

import openai
import requests
import os
import datetime
from io import BytesIO
from PIL import Image

# === Load OpenAI API Key ===
def load_api_key():
    base = os.path.dirname(__file__)
    path = os.path.abspath(os.path.join(base, "..", "api_key.txt"))
    with open(path, "r") as f:
        return f.read().strip()

openai.api_key = load_api_key()

# === Generate Image from Prompt ===
def generate_image_from_prompt(prompt: str) -> Image.Image:
    try:
        prompt = prompt.strip()
        response = openai.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1792x1024",  # Closest supported landscape format
            quality="standard"
        )
        image_url = response.data[0].url
        img_data = requests.get(image_url).content
        image = Image.open(BytesIO(img_data))
        return image
    except Exception as e:
        raise RuntimeError(f"Image generation failed: {e}")

# === Save Only the Full-Size Original Image ===
def save_image(image: Image.Image):
    image_dir = os.path.join(os.path.dirname(__file__), "ai_images")
    os.makedirs(image_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    filename = f"{timestamp}.png"
    save_path = os.path.join(image_dir, filename)
    image.save(save_path)
    print(f"? Image saved: {save_path}")

    return save_path