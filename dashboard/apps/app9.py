def main():
    import tkinter as tk

    root = tk.Tk()
    root.title("App 9")
    root.geometry("800x480")
    root.configure(bg="black")

    label = tk.Label(root, text="This is App 9", font=("Arial", 24), fg="white", bg="black")
    label.pack(expand=True)

    # Close window when 'Escape' is pressed
    root.bind("<Escape>", lambda e: root.destroy())

    root.mainloop()
