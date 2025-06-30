import os
import threading
import serial
import time
import math
import customtkinter as ctk
from PIL import Image, ImageOps
from apps import placeholder_app, gallery, imagegen

# === Directories ===
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(SCRIPT_DIR, "ai_images")
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

# === Fonts ===
FONT_BODY = ("Noto Sans", 14)
FONT_INPUT = ("Noto Sans", 16)

# === Menu items ===
menu_items = [
    ("App 0", placeholder_app),
    ("App 1", placeholder_app),
    ("App 2", placeholder_app),
    ("App 3", placeholder_app),
    ("App 4", placeholder_app),
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
        img = Image.open(bg_path).resize((800,480), Image.LANCZOS)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(800,480))
        lbl = ctk.CTkLabel(content_frame, image=cimg, text="")
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = cimg

def open_gallery_gui():
    global gallery_frames, gallery_update_callback
    clear_content()
    update_status("gallery")
    bg_path = os.path.join(GRAPHICS_DIR, 'gallery.png')
    if os.path.isfile(bg_path):
        img = Image.open(bg_path).resize((800,480), Image.LANCZOS)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(800,480))
        lbl = ctk.CTkLabel(content_frame, image=cimg, text="")
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = cimg

    gallery.load_images()
    thumbs = gallery.get_all_thumbnails(size=(200,120))
    cols, frame_w, frame_h = 3, 200, 120
    rows = math.ceil(len(thumbs) / cols)
    gap_x = (800 - cols * frame_w) / (cols + 1)
    gap_y = (480 - rows * frame_h) / (rows + 1)
    gallery_frames = []

    for i, (thumb, _) in enumerate(thumbs):
        row, col = divmod(i, cols)
        fit_img = ImageOps.contain(thumb, (frame_w, frame_h), Image.LANCZOS)
        frame = ctk.CTkFrame(
            content_frame,
            width=frame_w,
            height=frame_h,
            corner_radius=0,
            border_width=2 if i == gallery.selected_index else 0,
            border_color='lightblue'
        )
        frame.place(
            x=int(gap_x + col * (frame_w + gap_x)),
            y=int(gap_y + row * (frame_h + gap_y))
        )

        img_ctk = ctk.CTkImage(
            light_image=fit_img,
            dark_image=fit_img,
            size=(fit_img.width, fit_img.height)
        )
        thumb_label = ctk.CTkLabel(frame, image=img_ctk, text="")
        thumb_label.image = img_ctk
        thumb_label.place(
            x=(frame_w - fit_img.width) // 2,
            y=(frame_h - fit_img.height) // 2
        )
        gallery_frames.append(frame)

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
    bg_path = os.path.join(GRAPHICS_DIR, 'imagegen.png')
    if os.path.isfile(bg_path):
        img = Image.open(bg_path).resize((800,480), Image.LANCZOS)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(800,480))
        lbl = ctk.CTkLabel(content_frame, image=cimg, text="")
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = cimg

    prompt_entry = ctk.CTkEntry(content_frame, font=FONT_INPUT, width=760)
    prompt_entry.insert(0, 'A futuristic city at sunset')
    prompt_entry.pack(padx=10, pady=4)
    prompt_entry.focus()

    image_label = ctk.CTkLabel(content_frame, text="")
    image_label.pack(pady=8)


def launch_app(index):
    # Added missing definition
    clear_content()
    update_status(f"App {index}")
    _, module = menu_items[index]
    if module == gallery:
        open_gallery_gui()
    elif module == imagegen:
        open_imagegen_gui()


def run_generation():
    p = prompt_entry.get().strip()
    if not p:
        return
    def task():
        img = imagegen.generate_image_from_prompt(p)
        imagegen.save_image(img)
        ir = img.resize((640,400))
        ci = ctk.CTkImage(light_image=ir, dark_image=ir, size=(640,400))
        root.after(0, lambda: image_label.configure(image=ci))
        root.after(0, lambda: setattr(image_label, 'image', ci))
    threading.Thread(target=task, daemon=True).start()


def handle_keypress(line):
    if line.startswith('KEY:'):
        line = 'hotkey:' + line.split(':')[1]
    if line.startswith('hotkey:'):
        k = int(line.split(':')[1])
        if k == 1:
            draw_menu()
            return
        if current_screen == 'images' and k == 2:
            run_generation()
            return
        if current_screen == 'gallery' and k == 2:
            gallery.send_to_inky()
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
        l = ser.readline().decode(errors='ignore').strip()
        if l:
            root.after(0, lambda ln=l: handle_keypress(ln))
        time.sleep(0.01)

if __name__ == '__main__':
    draw_menu()
    threading.Thread(target=macropad_listener, daemon=True).start()
    root.mainloop()
