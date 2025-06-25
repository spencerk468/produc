import tkinter as tk
import threading
import serial
import time
from apps import placeholder_app, app11_imagegen
from PIL import ImageTk

# === App Setup ===
root = tk.Tk()
root.title("Todo Pi Dashboard")
root.geometry("480x320")
root.configure(bg="black")

# === Layout Frames ===
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

menu_items = [
    ("App 0", placeholder_app),
    ("App 1", placeholder_app),
    ("App 2", placeholder_app),
    ("App 3", placeholder_app),
    ("App 4", placeholder_app),
    ("App 5", placeholder_app),
    ("App 6", placeholder_app),
    ("App 7", placeholder_app),
    ("App 8", placeholder_app),
    ("App 9", placeholder_app),
    ("App 10", placeholder_app),
    ("Images", app11_imagegen),
]

# === UI Logic ===

def update_status(text):
    global current_screen
    current_screen = text
    status_label.config(text=f"Screen: {current_screen}")

def clear_content():
    for widget in content_frame.winfo_children():
        widget.destroy()

def draw_menu():
    global buttons
    clear_content()
    buttons.clear()

    for i in range(12):
        label = f"App {i}" if i < 11 else "Images"
        btn = tk.Button(
            content_frame,
            text=label,
            font=("Arial", 14),
            width=10,
            height=3,
            command=lambda i=i: launch_app(i),
            bg="gray",
            fg="white"
        )
        btn.grid(row=i // 3, column=i % 3, padx=10, pady=10)
        buttons.append(btn)

def update_button_styles():
    for i, btn in enumerate(buttons):
        if i == selected_index:
            btn.config(bg="cyan", fg="black")
        else:
            btn.config(bg="gray", fg="white")

def thread_safe_update_styles():
    root.after(0, update_button_styles)

def open_placeholder_gui(key_num):
    clear_content()
    update_status(f"app {key_num}")
    label = tk.Label(content_frame, text=f"You pressed key {key_num}", font=("Arial", 20), bg="black", fg="white")
    label.pack(pady=30)
    btn = tk.Button(content_frame, text="Back to Home", command=go_home)
    btn.pack(pady=10)

def open_imagegen_gui():
    global prompt_entry, image_label, status
    clear_content()
    update_status("images")

    status = tk.Label(content_frame, text="Enter a prompt (press encoder or key 2 to generate):", fg="white", bg="black", font=("Arial", 14))
    status.pack(pady=10)

    prompt_entry = tk.Entry(content_frame, font=("Arial", 16), width=40)
    prompt_entry.insert(0, "A futuristic city at sunset")
    prompt_entry.pack(pady=5)
    prompt_entry.focus_set()  # allow keyboard typing

    image_label = tk.Label(content_frame, bg="black")
    image_label.pack(pady=10)

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

def go_home():
    update_status("home")
    draw_menu()
    update_button_styles()

def launch_app(index):
    if index < 11:
        placeholder_app.run(key_number=index)
        open_placeholder_gui(index)
    else:
        open_imagegen_gui()

# === MacroPad Serial Listener ===
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
                    selected_index = (selected_index + 1) % len(buttons)
                    thread_safe_update_styles()
                elif direction == "-1":
                    selected_index = (selected_index - 1) % len(buttons)
                    thread_safe_update_styles()

            elif line.startswith("hotkey:"):
                key = int(line.split(":")[1])
                if 0 <= key < len(menu_items):
                    root.after(0, lambda k=key: launch_app(k))
                elif key == 11:
                    root.after(0, lambda: launch_app(selected_index))

        elif current_screen == "images":
            if line == "hotkey:2" or line == "hotkey:11":
                root.after(0, run_generation)

# === Start ===
draw_menu()
update_status("home")
update_button_styles()
threading.Thread(target=macropad_listener, daemon=True).start()

if __name__ == "__main__":
    root.mainloop()
