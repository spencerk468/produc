import importlib
import serial
import time
import multiprocessing

APP_KEYS = {
    6: "app6",
    7: "app7",
    8: "app8",
    9: "app9",
    10: "app10",
    11: "app11_imagegen"
}

current_app_process = None
current_app_key = None

def launch_app(app_key):
    global current_app_process, current_app_key

    app_name = APP_KEYS[app_key]

    # If an app is already running, terminate it
    if current_app_process and current_app_process.is_alive():
        print(f"Closing currently running app: {APP_KEYS[current_app_key]}")
        current_app_process.terminate()
        current_app_process.join()

    # Launch new app as separate process
    def run_app():
        try:
            module = importlib.import_module(f"apps.{app_name}")
            if hasattr(module, "main"):
                module.main()
            else:
                print(f"App {app_name} has no main() function.")
        except Exception as e:
            print(f"Error running {app_name}: {e}")

    print(f"Launching {app_name}...")
    current_app_process = multiprocessing.Process(target=run_app)
    current_app_process.start()
    current_app_key = app_key

def listen_macropad(port="/dev/ttyACM1"):
    try:
        with serial.Serial(port, 115200, timeout=1) as ser:
            print("Dashboard listening on", port)
            while True:
                line = ser.readline().decode("utf-8").strip()
                if line.startswith("hotkey:"):
                    try:
                        key = int(line.split(":")[1])
                        print(f"Key {key} pressed")
                        if key in APP_KEYS:
                            launch_app(key)
                        else:
                           pass
                    except ValueError:
                        print(f"Ignoring invalid input: {line}")
                time.sleep(0.05)
    except Exception as e:
        print(f"Serial error: {e}")

if __name__ == "__main__":
    multiprocessing.set_start_method("fork")  # Important for Unix-like systems
    listen_macropad()
