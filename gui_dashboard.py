import customtkinter as ctk
import tkinter as tk
import threading
import serial
import time
from PIL import Image, ImageTk
from apps import placeholder_app, app11_imagegen, app10_gallery

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

exit_requested = False
current_screen = "home"
selected_index = 0
prompt_entry = None
image_label = None
status = None
gallery_update_callback = None
gallery_canvas_widget = None

FONT_BODY = ("Noto Sans", 14)
FONT_INPUT = ("Noto Sans", 16)

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

root = ctk.CTk()
root.title("Todo Pi Dashboard")
root.geometry("800x480")
root.attributes("-fullscreen", True)
root.bind("<Escape>", lambda e: root.destroy())

container = ctk.CTkFrame(root)
container.pack(fill="both", expand=True)

content_frame = ctk.CTkFrame(container)
content_frame.pack(fill="both", expand=True)

def update_status(text):
    global current_screen
    current_screen = text

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def go_home():
    update_status("home")
    draw_menu()

def launch_app(index, module=None):
    if index == 8:
        open_imagegen_gui()
    elif index == 7:
        open_gallery_gui()
    else:
        update_status(f"App {index}")
        clear_content()
        label = ctk.CTkLabel(content_frame, text=f"Placeholder for App {index}", font=FONT_BODY)
        label.pack(pady=20)
        back_btn = ctk.CTkButton(content_frame, text="Back to Home", command=go_home)
        back_btn.pack(pady=8)

def open_gallery_gui():
    global gallery_update_callback, gallery_canvas_widget
    clear_content()
    update_status("gallery")
    app10_gallery.load_images()

    gallery_canvas_widget = ctk.CTkFrame(content_frame, fg_color="black")
    gallery_canvas_widget.pack(fill="both", expand=True)

    back_btn = ctk.CTkButton(content_frame, text="Back to Home", command=go_home)
    back_btn.pack(pady=4)

    app10_gallery.draw_gallery_grid(gallery_canvas_widget, thumb_size=(270, 160), padding=1)

    def update_gallery(): app10_gallery.next_image(); app10_gallery.update_gallery_highlight(gallery_canvas_widget)
    def update_gallery_prev(): app10_gallery.prev_image(); app10_gallery.update_gallery_highlight(gallery_canvas_widget)
    gallery_update_callback = (update_gallery, update_gallery_prev)

def open_imagegen_gui():
    global prompt_entry, image_label, status
    clear_content()
    update_status("images")

    status = ctk.CTkLabel(content_frame, text="Enter a prompt (press encoder or key 2 to generate):", font=FONT_BODY)
    status.pack(pady=6)

    prompt_entry = ctk.CTkEntry(content_frame, font=FONT_INPUT, width=760)
    prompt_entry.insert(0, "A futuristic city at sunset")
    prompt_entry.pack(pady=4)
    prompt_entry.focus_set()

    image_label = ctk.CTkLabel(content_frame)
    image_label.pack(pady=8)

    back_btn = ctk.CTkButton(content_frame, text="Back to Home", command=go_home)
    back_btn.pack(pady=8)

def run_generation():
    global prompt_entry, image_label, status
    if not prompt_entry:
        return

    prompt = prompt_entry.get().strip()
    if not prompt:
        status.configure(text="Please enter a prompt", text_color="yellow")
        return

    status.configure(text="Generating image...", text_color="white")
    image_label.configure(image='')

    def task():
        try:
            img = app11_imagegen.generate_image_from_prompt(prompt)
            app11_imagegen.save_image(img)
            img_resized = img.resize((640, 400))
            photo = ImageTk.PhotoImage(img_resized)
            root.after(0, lambda: [image_label.configure(image=photo), setattr(image_label, 'image', photo)])
            root.after(0, lambda: status.configure(text="Image generated!", text_color="green"))
        except Exception as e:
            root.after(0, lambda: status.configure(text=f"{e}", text_color="red"))

    threading.Thread(target=task).start()

def draw_menu():
    clear_content()

    bg = Image.open("home.png").resize((800, 480), Image.LANCZOS)
    bg_image = ctk.CTkImage(light_image=bg, dark_image=bg, size=(800, 480))
    bg_label = ctk.CTkLabel(content_frame, image=bg_image, text="")
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)
    root.bg_image = bg_image

def macropad_listener():
    global selected_index
    try:
        ser = serial.Serial('/dev/ttyACM1', 115200, timeout=0.1)
        print("? Connected to MacroPad")
    except Exception as e:
        print(f"? Failed to connect: {e}")
        return

    while not exit_requested:
        try:
            line = ser.readline().decode(errors='ignore').strip()
            if not line:
                time.sleep(0.01)
                continue

            print(f"[MACROPAD] {line}")

            if current_screen == "home":
                if line.startswith("hotkey:"):
                    key = int(line.split(":")[1])
                    if 3 <= key <= 11:
                        menu_index = key - 3
                        if 0 <= menu_index < len(menu_items[:9]):
                            root.after(0, lambda: launch_app(menu_index))

            elif current_screen == "gallery":
                if line == "rotary:+1":
                    root.after(0, gallery_update_callback[0])
                elif line == "rotary:-1":
                    root.after(0, gallery_update_callback[1])
                elif line in ("hotkey:2", "encoder_press"):
                    root.after(0, app10_gallery.send_to_inky)
                elif line == "hotkey:0":
                    root.after(0, go_home)

            elif current_screen == "images":
                if line in ("hotkey:2", "encoder_press"):
                    root.after(0, run_generation)
                elif line == "hotkey:0":
                    root.after(0, go_home)

        except Exception as e:
            print(f"? Listener error: {e}")

# === Start ===
draw_menu()
threading.Thread(target=macropad_listener, daemon=True).start()
root.mainloop()
