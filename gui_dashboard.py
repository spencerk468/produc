import customtkinter as ctk
import threading
import serial
import time
import os
from PIL import ImageTk, Image
from apps import placeholder_app, app11_imagegen, app10_gallery

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

FONT_BODY = ("Noto Sans", 14)
FONT_LABEL = ("Noto Sans", 10)
FONT_INPUT = ("Noto Sans", 16)

exit_requested = False

def on_close():
    global exit_requested
    exit_requested = True
    root.destroy()

def on_key(event):
    if event.char == 'q':
        on_close()

root = ctk.CTk()
root.title("Todo Pi Dashboard")
root.geometry("800x480")
root.attributes("-fullscreen", True)
root.bind("<Key>", on_key)
root.protocol("WM_DELETE_WINDOW", on_close)

container = ctk.CTkFrame(root)
container.pack(fill="both", expand=True)

content_frame = ctk.CTkFrame(container)
content_frame.pack(fill="both", expand=True)

bottom_frame = ctk.CTkFrame(root)
bottom_frame.pack(fill="x", side="bottom")

status_label = ctk.CTkLabel(bottom_frame, text="Screen: home", font=FONT_LABEL)
status_label.pack(anchor="w", padx=5)

buttons = []
selected_index = 0
current_screen = "home"
prompt_entry = None
image_label = None
status = None
gallery_update_callback = None
gallery_canvas_widget = None

def draw_menu():
    global buttons
    for widget in content_frame.winfo_children():
        widget.destroy()
    buttons.clear()

    for i, (label_text, app_module) in enumerate(menu_items[:9]):
        row, col = divmod(i, 3)
        btn = ctk.CTkButton(
            content_frame, text=label_text,
            font=FONT_BODY,
            width=265, height=160,
            corner_radius=2,
            command=(lambda m=app_module, idx=i: launch_app(idx, m))
        )
        btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
        buttons.append(btn)

    for i in range(3):
        content_frame.grid_columnconfigure(i, weight=1)
    for i in range(3):
        content_frame.grid_rowconfigure(i, weight=1)

def update_status(text):
    global current_screen
    current_screen = text
    if root.winfo_exists():
        status_label.configure(text=f"Screen: {current_screen}")

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def go_home():
    update_status("home")
    draw_menu()
    update_button_styles()

def open_gallery_gui():
    global gallery_update_callback, gallery_canvas_widget
    clear_content()
    update_status("gallery")
    app10_gallery.load_images()

    gallery_canvas_widget = ctk.CTkFrame(content_frame, fg_color="black")
    gallery_canvas_widget.pack(padx=0, pady=0, fill="both", expand=True)

    back_button = ctk.CTkButton(content_frame, text="Back to Home", command=go_home)
    back_button.pack(pady=4)

    app10_gallery.draw_gallery_grid(gallery_canvas_widget, thumb_size=(270, 160), padding=1)

    def update_gallery():
        app10_gallery.next_image()
        app10_gallery.update_gallery_highlight(gallery_canvas_widget)

    def update_gallery_prev():
        app10_gallery.prev_image()
        app10_gallery.update_gallery_highlight(gallery_canvas_widget)

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

    btn = ctk.CTkButton(content_frame, text="Back to Home", command=go_home)
    btn.pack(pady=8)

def safe_status_update(text, color="white"):
    if not exit_requested and status and root.winfo_exists():
        root.after(0, lambda: status.configure(text=text, text_color=color))

def run_generation():
    global prompt_entry, image_label, status
    if not prompt_entry:
        return

    prompt = prompt_entry.get().strip()
    if not prompt:
        safe_status_update("Please enter a prompt", "yellow")
        return

    safe_status_update("Generating image...", "white")
    image_label.configure(image='')

    def task():
        try:
            img = app11_imagegen.generate_image_from_prompt(prompt)
            app11_imagegen.save_image(img)

            img_resized = img.resize((640, 400))
            photo = ImageTk.PhotoImage(img_resized)
            if image_label and root.winfo_exists():
                root.after(0, lambda: [image_label.configure(image=photo), setattr(image_label, 'image', photo)])

            safe_status_update("Image generated!", "green")
        except Exception as e:
            safe_status_update(f"{e}", "red")

    threading.Thread(target=task).start()

def launch_app(index, module=None):
    if index == 8:
        open_imagegen_gui()
    elif index == 7:
        open_gallery_gui()
    else:
        update_status(f"App {index}")

def update_button_styles():
    for i, btn in enumerate(buttons):
        if i == selected_index:
            btn.configure(fg_color="cyan", text_color="black")
        else:
            btn.configure(fg_color="#222222", text_color="white")

def thread_safe_update_styles():
    if not exit_requested and root.winfo_exists():
        root.after(0, update_button_styles)

def macropad_listener():
    global selected_index
    try:
        ser = serial.Serial('/dev/ttyACM1', 115200, timeout=0.1)
        print("Connected to MacroPad on /dev/ttyACM1")
    except serial.SerialException as e:
        print(f"Could not connect to MacroPad: {e}")
        return

    while not exit_requested:
        line = ser.readline().decode().strip()
        if not line:
            time.sleep(0.01)
            continue

        print(f"[MACROPAD] {line}")

        if current_screen == "home":
            if line.startswith("rotary:"):
                direction = line.split(":")[1]
                if direction == "+1":
                    selected_index = (selected_index + 1) % len(menu_items[:9])
                    thread_safe_update_styles()
                elif direction == "-1":
                    selected_index = (selected_index - 1) % len(menu_items[:9])
                    thread_safe_update_styles()
            elif line.startswith("hotkey:"):
                key = int(line.split(":")[1])
                if key in (0, 1, 2):
                    return
                if 3 <= key <= 11:
                    menu_index = key - 3
                    if 0 <= menu_index < len(menu_items[:9]):
                        if not exit_requested and root.winfo_exists():
                            root.after(0, lambda idx=menu_index: launch_app(idx))

        elif current_screen == "gallery":
            if line == "rotary:+1":
                if not exit_requested and root.winfo_exists():
                    gallery_update_callback[0]()
            elif line == "rotary:-1":
                if not exit_requested and root.winfo_exists():
                    gallery_update_callback[1]()
            elif line == "hotkey:2" or line == "encoder_press":
                if not exit_requested and root.winfo_exists():
                    root.after(0, app10_gallery.send_to_inky)
            elif line == "hotkey:0":
                if not exit_requested and root.winfo_exists():
                    root.after(0, go_home)

        elif current_screen == "images":
            if line == "hotkey:2" or line == "encoder_press":
                if not exit_requested and root.winfo_exists():
                    root.after(0, run_generation)
            elif line == "hotkey:0":
                if not exit_requested and root.winfo_exists():
                    root.after(0, go_home)

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

# === Start ===
draw_menu()
update_status("home")
update_button_styles()
threading.Thread(target=macropad_listener, daemon=True).start()

if __name__ == "__main__":
    root.mainloop()
