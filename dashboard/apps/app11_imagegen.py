def main():
    import openai
    import requests
    import threading
    import os
    import datetime
    from io import BytesIO
    from PIL import Image, ImageTk
    import tkinter as tk
    import serial
    import time

    # --- Load OpenAI API Key ---
    def load_api_key():
        base = os.path.dirname(__file__)  # this is apps/
        path = os.path.abspath(os.path.join(base, "..", "api_key.txt"))
        with open(path, "r") as f:
            return f.read().strip()

    openai.api_key = load_api_key()

    # --- Generate, Show, and Save Image ---
    def generate_and_show_image(prompt):
        try:
            label.config(text="Generating image from AI...", image='', bg="black", fg="white")
            root.update_idletasks()

            # Request image from OpenAI
            response = openai.images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response.data[0].url
            img_data = requests.get(image_url).content
            image = Image.open(BytesIO(img_data))

            # Resize and display
            image_display = image.resize((800, 480), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image_display)
            label.config(image=photo, text="")
            label.image = photo  # prevent garbage collection

            # Save original image
            image_dir = os.path.join(os.path.dirname(__file__), "ai_images")
            os.makedirs(image_dir, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{timestamp}.png"
            save_path = os.path.join(image_dir, filename)
            image.save(save_path)
            print(f"? Image saved to: {save_path}")

        except Exception as e:
            label.config(text=f"Error: {e}", fg="red", bg="black")
            print(f"? Error generating image: {e}")

    # --- Trigger from prompt ---
    def trigger_from_prompt():
        prompt = prompt_entry.get().strip()
        if prompt:
            threading.Thread(target=generate_and_show_image, args=(prompt,)).start()
        else:
            label.config(text="Please enter a prompt.", fg="yellow", bg="black")

    # --- MacroPad Key 2 Listener ---
    def listen_macropad(port="/dev/ttyACM1"):
        try:
            with serial.Serial(port, 115200, timeout=1) as ser:
                print("Listening for key 2 on MacroPad...")
                while True:
                    line = ser.readline().decode("utf-8").strip()
                    if line == "hotkey:2":
                        print("Key 2 pressed - generating image")
                        trigger_from_prompt()
                    time.sleep(0.05)
        except Exception as e:
            print(f"Error listening to MacroPad: {e}")

    # --- GUI Setup ---
    root = tk.Tk()
    root.title("AI Image Generator")
    root.geometry("800x480")
    root.configure(bg="black")

    prompt_entry = tk.Entry(root, font=("Arial", 16), width=60)
    prompt_entry.insert(0, "A futuristic city at sunset")
    prompt_entry.pack(pady=10)

    generate_button = tk.Button(root, text="Generate Image", command=trigger_from_prompt,
                                font=("Arial", 16), bg="gray20", fg="white")
    generate_button.pack()

    label = tk.Label(root, text="Type a prompt and press Generate (or Key 2)", 
                     fg="white", bg="black", font=("Arial", 18))
    label.pack(expand=True)

    threading.Thread(target=listen_macropad, daemon=True).start()

    root.mainloop()
