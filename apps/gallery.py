import os
from PIL import Image
import subprocess

# === Configuration ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Show images from apps/ai_images directory
IMAGE_DIR = os.path.join(SCRIPT_DIR, "ai_images")

# === State ===
image_files = []
selected_index = 0

# === Image Management ===

def load_images():
    """
    Populate image_files with all PNG/JPG images in IMAGE_DIR,
    sorted newest-first, and reset the selection index.
    """
    global image_files, selected_index
    if not os.path.isdir(IMAGE_DIR):
        image_files = []
        selected_index = 0
        return

    image_files = sorted(
        [f for f in os.listdir(IMAGE_DIR)
         if f.lower().endswith((".png", ".jpg", ".jpeg"))],
        reverse=True
    )
    selected_index = 0


def next_image():
    """Advance the selected_index to the next image."""
    global selected_index
    if image_files:
        selected_index = (selected_index + 1) % len(image_files)


def prev_image():
    """Move the selected_index to the previous image."""
    global selected_index
    if image_files:
        selected_index = (selected_index - 1) % len(image_files)


def get_thumbnail(path, size):
    """
    Load the image at `path`, generate a thumbnail of `size`, and return the PIL Image.
    """
    img = Image.open(path)
    img.thumbnail(size)
    return img


def get_all_thumbnails(size=(270, 160)):
    """
    Returns a list of tuples (PIL.Image thumbnail, index)
    for every image in image_files in display order.
    """
    thumbs = []
    for i, fname in enumerate(image_files):
        full_path = os.path.join(IMAGE_DIR, fname)
        try:
            thumb = get_thumbnail(full_path, size)
            thumbs.append((thumb, i))
        except Exception:
            continue
    return thumbs


def get_current_image_path():
    """
    Returns the full path of the currently selected image.
    """
    if image_files:
        return os.path.join(IMAGE_DIR, image_files[selected_index])
    return None


def send_to_inky():
    """
    Uploads the currently selected image to Pi Zero & triggers it.
    """
    local = get_current_image_path()
    if not local:
        print("No image selected")
        return

    filename = os.path.basename(local)
    remote_dir = "/home/spencer/ai_images"
    remote = f"{remote_dir}/{filename}"

    try:
        subprocess.run(["ssh", "spencer@pizero", f"mkdir -p {remote_dir}"], check=True)
        subprocess.run(["scp", local, f"spencer@pizero:{remote}"], check=True)
        subprocess.run([
            "ssh", "spencer@pizero",
            f"/home/spencer/.virtualenvs/pimoroni/bin/python3 /home/spencer/send_to_inky.py '{remote}'"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to send to Inky: {e}")

# Bind key 2 to send_to_inky
# This function will be called from gui_dashboard.py when key 2 is pressed.
