import os
import threading
import serial
import time
import customtkinter as ctk
from PIL import Image, ImageTk, ImageOps
from apps import placeholder_app, app10_gallery, app11_imagegen

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
status_label = None
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
    ("Gallery", app10_gallery),
    ("ImageGen", app11_imagegen),
]

# === Initialize root window ===
root = ctk.CTk()
root.title("Todo Pi Dashboard")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.destroy())

container = ctk.CTkFrame(root)
container.pack(fill="both")

content_frame = ctk.CTkFrame(container)
# Make window fullscreen and keep content static
root.geometry("800x480")
content_frame.pack(fill="none")
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
        lbl = ctk.CTkLabel(content_frame, image=cimg, text='')
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = cimg


def go_home():
    update_status("home")
    draw_menu()


def launch_app(index):
    clear_content()
    update_status(f"App {index}")
    _, module = menu_items[index]
    if module == app10_gallery:
        open_gallery_gui()
    elif module == app11_imagegen:
        open_imagegen_gui()
    else:
        ctk.CTkLabel(content_frame, text=f"Placeholder for App {index}", font=FONT_BODY).pack(expand=True)


def open_gallery_gui():
    global gallery_frames, gallery_update_callback
    clear_content()
    update_status("gallery")
    # background image
    bg_path = os.path.join(GRAPHICS_DIR, 'gallery.png')
    if os.path.isfile(bg_path):
        bg_img = Image.open(bg_path).resize((800,480), Image.LANCZOS)
        bg_ctk = ctk.CTkImage(light_image=bg_img, dark_image=bg_img, size=(800,480))
        bg_lbl = ctk.CTkLabel(content_frame, image=bg_ctk, text='')
        bg_lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = bg_ctk

    # load thumbnails
    app10_gallery.load_images()
    thumbs = app10_gallery.get_all_thumbnails(size=(200,150))
    cols = 3
    frame_w, frame_h = 200, 150
    gallery_frames = []

    # display thumbnails in fixed grid
    for i, (thumb, _) in enumerate(thumbs):
        row, col = divmod(i, cols)
        # fit thumbnail to frame preserving aspect ratio
        fit_img = ImageOps.contain(thumb, (frame_w, frame_h), Image.LANCZOS)
        frame = ctk.CTkFrame(
            content_frame,
            width=frame_w,
            height=frame_h,
            fg_color='transparent',
            corner_radius=0,
            border_width=2 if i == app10_gallery.selected_index else 0,
            border_color='blue'
        )
        frame.place(x=col * (frame_w + 10), y=row * (frame_h + 10))
        img_ctk = ctk.CTkImage(light_image=fit_img, dark_image=fit_img, size=(fit_img.width, fit_img.height))
        lbl = ctk.CTkLabel(frame, image=img_ctk, text='', fg_color='transparent')
        lbl.image = img_ctk
        # center the image inside the frame
        lbl.place(x=(frame_w - fit_img.width)//2, y=(frame_h - fit_img.height)//2)
        gallery_frames.append(frame)

    # function to refresh highlight
    def refresh():
        sel = app10_gallery.selected_index
        for j, fr in enumerate(gallery_frames):
            fr.configure(
                border_width=2 if j == sel else 0,
                border_color='blue'
            )

    # bind rotary actions
    def nxt():
        app10_gallery.next_image()
        refresh()

    def prv():
        app10_gallery.prev_image()
        refresh()

    gallery_update_callback = (nxt, prv)


def open_imagegen_gui():
    global prompt_entry, image_label, status_label
    clear_content()
    update_status("images")
    # background image
    bg_path = os.path.join(GRAPHICS_DIR, 'imagegen.png')
    if os.path.isfile(bg_path):
        img = Image.open(bg_path).resize((800,480), Image.LANCZOS)
        cimg = ctk.CTkImage(light_image=img, dark_image=img, size=(800,480))
        lbl = ctk.CTkLabel(content_frame, image=cimg, text='')
        lbl.place(x=0, y=0, relwidth=1, relheight=1)
        root.bg_image = cimg
    status_label = ctk.CTkLabel(content_frame, text='Enter prompt (key2):', font=FONT_BODY)
    status_label.pack(pady=6)
    prompt_entry = ctk.CTkEntry(content_frame, font=FONT_INPUT, width=760)
    prompt_entry.insert(0, 'A futuristic city at sunset')
    prompt_entry.pack(pady=4)
    prompt_entry.focus()
    image_label = ctk.CTkLabel(content_frame)
    image_label.pack(pady=8)


def run_generation():
    p = prompt_entry.get().strip()
    if not p:
        status_label.configure(text='Please enter a prompt', text_color='yellow')
        return
    status_label.configure(text='Generating...', text_color='white')
    image_label.configure(image='')

    def task():
        try:
            img = app11_imagegen.generate_image_from_prompt(p)
            path = app11_imagegen.save_image(img)
            ir = img.resize((640,400))
            ci = ctk.CTkImage(light_image=ir, dark_image=ir, size=(640,400))
            root.after(0, lambda: image_label.configure(image=ci))
            root.after(0, lambda: setattr(image_label, 'image', ci))
            root.after(0, lambda: status_label.configure(text=f'Saved {path}', text_color='green'))
        except Exception as e:
            root.after(0, lambda: status_label.configure(text=str(e), text_color='red'))

    threading.Thread(target=task, daemon=True).start()


def handle_keypress(line):
    if line.startswith('KEY:'):
        line = 'hotkey:' + line.split(':')[1]
    if line.startswith('hotkey:'):
        k = int(line.split(':')[1])
        if k == 0:
            go_home()
            return
        if 3 <= k <= 11:
            launch_app(k - 3)
            return
    if current_screen == 'gallery':
        if line == 'rotary:+1':
            gallery_update_callback[0]()
        elif line == 'rotary:-1':
            gallery_update_callback[1]()
    if current_screen == 'images' and line in ('hotkey:2', 'encoder_press'):
        run_generation()


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
