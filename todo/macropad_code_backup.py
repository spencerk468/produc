import board
import displayio
import terminalio
import usb_cdc
from adafruit_display_text import label, wrap_text_to_lines
import adafruit_macropad

macropad = adafruit_macropad.MacroPad()

# === Display Setup ===
splash = displayio.Group()
macropad.display.root_group = splash
text_label = label.Label(terminalio.FONT, text="Ready", x=0, y=8)
splash.append(text_label)

serial = usb_cdc.data
last_transcript = ""

def send_record_command():
    serial.write(b"record\n")

def update_led(key, state, color=(80, 200, 120)):
    macropad.pixels[key] = color if state else (0, 0, 0)
    macropad.pixels.show()

def display_wrapped_text(text):
    lines = wrap_text_to_lines(text, max_chars=20)
    combined = "\n".join(lines[:4])
    text_label.text = combined

while True:
    event = macropad.keys.events.get()

    if event:
        # === Key 2: Record ===
        if event.key_number == 2:
            if event.pressed:
                text_label.text = "Recording..."
                send_record_command()
                update_led(2, True)
            elif event.released:
                update_led(2, False)

        # === Key 5: Save current transcript ===
        if event.key_number == 5 and event.pressed:
            try:
                with open("/transcripts.txt", "a") as f:
                    f.write(last_transcript + "\n")
                text_label.text = "Saved ?"
            except Exception as e:
                text_label.text = f"Save error: {e}"

    # === Serial input from Pi ===
    if serial.in_waiting > 0:
        received = serial.readline().decode("utf-8").strip()
        last_transcript = received
        display_wrapped_text(received)

    macropad.encoder_switch_debounced.update()
