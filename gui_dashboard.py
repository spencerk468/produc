import tkinter as tk
import threading
import serial
import time
import os
from PIL import ImageTk, Image
from apps import placeholder_app, app11_imagegen, app10_gallery

root = tk.Tk()
root.title("Todo Pi Dashboard")
root.geometry("480x320")
root.configure(bg="black")

container = tk.Frame(root, bg="black")
container.pack(fill=tk.BOTH, expand=True)

content_frame = tk.Frame(container, bg="black")
content_frame.pack(fill=tk.BOTH, expand=True)

bottom_frame = tk.Frame(root, bg="black")
bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

status_label = tk.Label(bottom_frame, text="Screen: home", font=("Arial", 10), bg="black", fg="white")
status_label.pack(anchor="w", padx=5)

buttons = []
selected_index = 0
current_screen = "home"
prompt_entry = None
image_label = None
status = None

gallery_update_callback = None

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

def draw_menu():
    global buttons
    for widget in content_frame.winfo_children():
        widget.destroy()
    buttons.clear()

    for i, (label_text, app_module) in enumerate(menu_items):
        row, col = divmod(i, 3)
        btn = tk.Button(
            content_frame, text=label_text,
            font=("Arial", 14), bg="#222222", fg="white",
            width=12, height=3, relief=tk.RAISED, bd=2,
            command=(lambda m=app_module, idx=i: launch_app(idx, m))
        )
        btn.grid(row=row, column=col, padx=5, pady=5)
        buttons.append(btn)

    for j in range(3):
        lbl = tk.Label(content_frame, text="Settings", font=("Arial", 12), bg="#111111", fg="gray", width=12, height=2, relief=tk.RIDGE)
        lbl.grid(row=3, column=j, padx=5, pady=5)

def update_status(text):
    global current_screen
    current_screen = text
    status_label.config(text=f"Screen: {current_screen}")

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def go_home():
    update_status("home")
    draw_menu()
    update_button_styles()

def open_imagegen_gui():
    global prompt_entry, image_label, status
    clear_content()
    update_status("images")

    status = tk.Label(content_frame, text="Enter a prompt (press encoder or key 2 to generate):", fg="white", bg="black", font=("Arial", 14))
    status.pack(pady=10)

    prompt_entry = tk.Entry(content_frame, font=("Arial", 16), width=40)
    prompt_entry.insert(0, "A futuristic city at sunset")
    prompt_entry.pack(pady=5)
    prompt_entry.focus_set()

    image_label = tk.Label(content_frame, bg="black")
    image_label.pack(pady=10)

    btn = tk.Button(content_frame, text="Back to Home", command=go_home)
    btn.pack(pady=10)

def run_generation():
    global prompt_entry, image_label, status
    if not prompt_entry:
        return

    prompt = prompt_entry.get().strip()
    if not prompt:
        status.config(text="?? Please enter a prompt", fg="yellow")
        return

    status.config(text="? Generating image...", fg="white")
    image_label.config(image='')

    def task():
        try:
            img = app11_imagegen.generate_image_from_prompt(prompt)
            app11_imagegen.save_image(img)

            img_resized = img.resize((400, 400))
            photo = ImageTk.PhotoImage(img_resized)
            image_label.config(image=photo)
            image_label.image = photo

            status.config(text="? Image generated!", fg="green")
        except Exception as e:
            status.config(text=f"? {e}", fg="red")

    threading.Thread(target=task).start()

def open_gallery_gui():
    global gallery_update_callback
    clear_content()
    update_status("gallery")
    app10_gallery.load_images()

    gallery_canvas = tk.Canvas(content_frame, bg="black")
    gallery_canvas.pack(expand=True, fill=tk.BOTH)

    app10_gallery.draw_gallery_grid(content_frame, gallery_canvas)

    gallery_update_callback = lambda: app10_gallery.draw_gallery_grid(content_frame, gallery_canvas)

    btn = tk.Button(content_frame, text="Back to Home", command=go_home)
    btn.pack(pady=10)

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
            btn.config(bg="cyan", fg="black")
        else:
            btn.config(bg="#222222", fg="white")

def thread_safe_update_styles():
    root.after(0, update_button_styles)

def macropad_listener():
    global selected_index
    try:
        ser = serial.Serial('/dev/ttyACM1', 115200, timeout=0.1)
        print("? Connected to MacroPad on /dev/ttyACM1")
    except serial.SerialException as e:
        print(f"?? Could not connect to MacroPad: {e}")
        return

    while True:
        line = ser.readline().decode().strip()
        if not line:
            time.sleep(0.01)
            continue

        print(f"[MACROPAD] {line}")

        if current_screen == "home":
            if line.startswith("rotary:"):
                direction = line.split(":")[1]
                if direction == "+1":
                    selected_index = (selected_index + 1) % len(menu_items)
                    thread_safe_update_styles()
                elif direction == "-1":
                    selected_index = (selected_index - 1) % len(menu_items)
                    thread_safe_update_styles()
            elif line.startswith("hotkey:"):
                key = int(line.split(":")[1])
                if key == 0:
                    root.after(0, go_home)
                elif key == 7:
                    root.after(0, open_gallery_gui)
                elif key == 8:
                    root.after(0, open_imagegen_gui)
                elif 0 <= key < len(menu_items):
                    root.after(0, lambda: launch_app(key))

        elif current_screen == "gallery":
            if line == "rotary:+1":
                root.after(0, lambda: [app10_gallery.next_image(), gallery_update_callback()])
            elif line == "rotary:-1":
                root.after(0, lambda: [app10_gallery.prev_image(), gallery_update_callback()])
            elif line == "hotkey:2" or line == "encoder_press":
                root.after(0, app10_gallery.send_to_inky)
            elif line == "hotkey:0":
                root.after(0, go_home)

        elif current_screen == "images":
            if line == "hotkey:2" or line == "encoder_press":
                root.after(0, run_generation)
            elif line == "hotkey:0":
                root.after(0, go_home)

# === Start ===
draw_menu()
update_status("home")
update_button_styles()
threading.Thread(target=macropad_listener, daemon=True).start()

if __name__ == "__main__":
    root.mainloop()
