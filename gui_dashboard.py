import os
import threading
import serial
import time
import math
import customtkinter as ctk
from PIL import Image, ImageOps

from apps import placeholder_app, gallery, imagegen
from apps.news import fetch_article, send_to_inky

# === Directories ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
GRAPHICS_DIR = os.path.join(SCRIPT_DIR, "graphics")

# === Appearance ===
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# === Global state ===
exit_requested = False
current_screen = "home"
prompt_entry = None
image_label = None
gallery_frames = []
gallery_update_callback = None
status_label = None
article_data = None

# === Fonts ===
FONT_BODY = ("Noto Sans", 14)
FONT_INPUT = ("Noto Sans", 16)

# === Menu items ===
menu_items = [
    ("App 0", placeholder_app),
    ("App 1", placeholder_app),
    ("App 2", placeholder_app),
    ("App 3", placeholder_app),
    ("News", None),
    ("App 5", placeholder_app),
    ("App 6", placeholder_app),
    ("Gallery", gallery),
    ("ImageGen", imagegen),
]

# === Initialize root window ===
root = ctk.CTk()
root.title("Todo Pi Dashboard")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.destroy())
root.geometry("800x480")

container = ctk.CTkFrame(root)
container.pack(fill="both")
content_frame = ctk.CTkFrame(container)
content_frame.pack(fill="both")
content_frame.configure(width=800, height=480)
content_frame.pack_propagate(False)

# === Utility functions ===
def update_status(screen_name):
    global current_screen
    current_screen = screen_name


def clear_content():
    for w in content_frame.winfo_children():
        w.destroy()

# === Screen functions ===
def draw_menu():
    clear_content()
    bg_path = os.path.join(GRAPHICS_DIR, 'home.png')
    if os.path.isfile(bg_path):
        img = Image.open(bg_path).resize((800, 480), Image.LANCZOS)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(800, 480))
        bg_label = ctk.CTkLabel(content_frame, image=cimg, text="")
        bg_label.image = cimg
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    update_status("home")


def open_news_gui():
    """Fetch & display the full positive news article in E-ink style"""
    clear_content()
    update_status("news")
    global article_data
    try:
        article_data = fetch_article()
        img = article_data['image'].resize((400, 240), Image.LANCZOS)
        bw = img.convert('1', dither=Image.FLOYDSTEINBERG)
        w, h = bw.size
        framed = Image.new('1', (w+20, h+20), color=1)
        framed.paste(bw, (10, 10))
        disp = framed.convert('RGB')
        cimg = ctk.CTkImage(light_image=disp, dark_image=disp, size=(w+20, h+20))
        img_lbl = ctk.CTkLabel(content_frame, image=cimg, text="")
        img_lbl.image = cimg
        img_lbl.pack(pady=10)
        title = article_data.get('title', '')
        ctk.CTkLabel(content_frame, text=title, font=("Noto Sans", 18), wraplength=780).pack(pady=(0, 4))
        desc = article_data.get('description', '')
        ctk.CTkLabel(content_frame, text=desc, font=FONT_BODY, wraplength=780).pack(pady=(0, 4))
    except Exception as e:
        ctk.CTkLabel(content_frame, text=f"Error: {e}", font=FONT_BODY).pack(expand=True)


def open_gallery_gui():
    global gallery_frames, gallery_update_callback, status_label
    clear_content()
    update_status("gallery")
    status_label = ctk.CTkLabel(content_frame, text="", font=FONT_BODY)
    status_label.place(x=20, y=20)
    gallery.load_images()
    thumbs = gallery.get_all_thumbnails(size=(200, 120))
    cols, fw, fh = 3, 200, 120
    rows = math.ceil(len(thumbs) / cols)
    gap_x = (800 - fw * cols) / (cols + 1)
    gap_y = (480 - fh * rows) / (rows + 1)
    gallery_frames = []
    for i, (thumb, _) in enumerate(thumbs):
        r, c = divmod(i, cols)
        fit = ImageOps.contain(thumb, (fw, fh), Image.LANCZOS)
        fr = ctk.CTkFrame(content_frame, width=fw, height=fh,
                          corner_radius=0,
                          border_width=2 if i == gallery.selected_index else 0,
                          border_color='lightblue')
        fr.place(x=gap_x + c * (fw + gap_x), y=gap_y + r * (fh + gap_y))
        ci = ctk.CTkImage(light_image=fit, dark_image=fit, size=(fit.width, fit.height))
        lbl = ctk.CTkLabel(fr, image=ci, text="")
        lbl.image = ci
        lbl.place(x=(fw - fit.width) // 2, y=(fh - fit.height) // 2)
        gallery_frames.append(fr)
    def refresh():
        sel = gallery.selected_index
        for j, fr in enumerate(gallery_frames):
            fr.configure(border_width=2 if j == sel else 0)
    gallery_update_callback = (
        lambda: (gallery.next_image(), refresh()),
        lambda: (gallery.prev_image(), refresh())
    )


def open_imagegen_gui():
    global prompt_entry, image_label
    clear_content()
    update_status("images")
    prompt_entry = ctk.CTkEntry(content_frame, font=FONT_INPUT, width=760)
    prompt_entry.insert(0, 'A futuristic city at sunset')
    prompt_entry.pack(padx=10, pady=4)
    prompt_entry.focus()
    image_label = ctk.CTkLabel(content_frame, text="")
    image_label.pack(pady=8)


def run_generation():
    p = prompt_entry.get().strip()
    if not p:
        return
    def task():
        img = imagegen.generate_image_from_prompt(p)
        imagegen.save_image(img)
        ir = img.resize((640, 400), Image.LANCZOS)
        ci = ctk.CTkImage(light_image=ir, dark_image=ir, size=(640, 400))
        root.after(0, lambda: image_label.configure(image=ci))
        root.after(0, lambda: setattr(image_label, 'image', ci))
    threading.Thread(target=task, daemon=True).start()


def show_sending():
    status_label.configure(text="Sending to display...")
    root.after(10000, lambda: status_label.configure(text=""))


def launch_app(index):
    clear_content()
    name, module = menu_items[index]
    if name == "News":
        open_news_gui()
    elif module == gallery:
        open_gallery_gui()
    elif module == imagegen:
        open_imagegen_gui()
    else:
        ctk.CTkLabel(content_frame, text=f"Placeholder for {name}", font=FONT_BODY).pack(expand=True)


def handle_keypress(line):
    if line.startswith('KEY:'):
        line = 'hotkey:' + line.split(':')[1]
    if line.startswith('hotkey:'):
        k = int(line.split(':')[1])
        if k == 1:
            draw_menu()
            return
        if current_screen == 'news' and k == 2:
            show_sending()
            if article_data and 'image' in article_data:
                send_to_inky(article_data['image'])
            return
        if current_screen == 'gallery' and k == 2:
            show_sending()
            gallery.send_to_inky()
            return
        if current_screen == 'images' and k == 2:
            run_generation()
            return
        if 3 <= k <= 11:
            launch_app(k - 3)
            return
    if current_screen == 'gallery':
        if line == 'rotary:+1':
            gallery_update_callback[0]()
        elif line == 'rotary:-1':
            gallery_update_callback[1]()


def macropad_listener():
    try:
        ser = serial.Serial('/dev/ttyACM1', 115200, timeout=0.1)
    except Exception as e:
        print(f'? MacroPad conn fail: {e}')
        return
    while not exit_requested:
        line = ser.readline().decode(errors='ignore').strip()
        if line:
            root.after(0, lambda ln=line: handle_keypress(ln))
        time.sleep(0.01)

if __name__ == '__main__':
    draw_menu()
    threading.Thread(target=macropad_listener, daemon=True).start()
    root.mainloop()
