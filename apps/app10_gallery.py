import os
from PIL import Image, ImageTk
import subprocess

IMAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "ai_images"))
image_files = []
selected_index = 0

def load_images():
    global image_files
    if not os.path.isdir(IMAGE_DIR):
        print(f"Image directory does not exist: {IMAGE_DIR}")
        image_files = []
        return
    image_files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    image_files.sort(reverse=True)

def get_current_image_path():
    if image_files:
        return os.path.join(IMAGE_DIR, image_files[selected_index])
    return None

def next_image():
    global selected_index
    if image_files:
        selected_index = (selected_index + 1) % len(image_files)

def prev_image():
    global selected_index
    if image_files:
        selected_index = (selected_index - 1) % len(image_files)

def preprocess_image_for_inky(local_path):
    try:
        img = Image.open(local_path).convert("RGB")
        img = img.resize((800, 480))
        img = img.convert("P", palette=Image.ADAPTIVE, colors=6)
        prepped_path = os.path.join(IMAGE_DIR, "_prepped_for_inky.png")
        img.save(prepped_path)
        return prepped_path
    except Exception as e:
        print(f"Preprocessing failed: {e}")
        return None

def send_to_inky():
    local_path = get_current_image_path()
    if not local_path:
        print("No image selected")
        return

    prepped_path = preprocess_image_for_inky(local_path)
    if not prepped_path:
        print("Image preprocessing failed. Aborting send.")
        return

    filename = os.path.basename(prepped_path)
    remote_dir = "/home/spencer/ai_images"
    remote_path = f"{remote_dir}/{filename}"

    print(f"Uploading {prepped_path} to Pi Zero...")
    try:
        subprocess.run([
            "ssh", "spencer@pizero", f"mkdir -p {remote_dir}"
        ], check=True)
        subprocess.run([
            "scp", prepped_path, f"spencer@pizero:{remote_path}"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to upload image: {e}")
        return

    print(f"Triggering remote display script on Pi Zero for {remote_path}...")
    try:
        subprocess.run([
            "ssh", "spencer@pizero",
            f"python3 /home/spencer/send_to_inky.py '{remote_path}'"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to trigger remote script: {e}")

def draw_gallery_grid(parent, canvas):
    for widget in parent.winfo_children():
        widget.destroy()

    cols = 3
    thumb_size = (120, 120)

    for i, file in enumerate(image_files):
        img_path = os.path.join(IMAGE_DIR, file)
        try:
            img = Image.open(img_path)
            img.thumbnail(thumb_size)
            photo = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Error loading image: {e}")
            continue

        import tkinter as tk
        frame = tk.Frame(parent, bd=2, relief="solid", bg=("cyan" if i == selected_index else "black"))
        frame.grid(row=i // cols, column=i % cols, padx=4, pady=4)
        lbl = tk.Label(frame, image=photo, bg=frame["bg"])
        lbl.image = photo
        lbl.pack()
        lbl.file_path = img_path

    canvas.update_idletasks()
