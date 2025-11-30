import RPi.GPIO as GPIO
import subprocess
import time
import psutil
import os
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import digitalio

# Pin setup
road_button_pin = 18  # Original start button
kill_button_pin = 13   # Kill button pin
track_button_pin = 6    # Road mode button

GPIO.setmode(GPIO.BCM)
GPIO.setup(road_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(kill_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(track_button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# SPI Display setup
cs_pin = digitalio.DigitalInOut(board.D8)    # Chip select
dc_pin = digitalio.DigitalInOut(board.D23)   # Data/Command
spi = board.SPI()
display = adafruit_ssd1306.SSD1306_SPI(128, 64, spi, dc_pin, None, cs_pin)

# Create an image for drawing
width = display.width
height = display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Load a larger font
font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)

def draw_text(text):
    # Clear the display
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Calculate text size and position for centering
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Draw the text
    draw.text((x, y), text, font=font, fill=255)
    
    # Update the display
    display.image(image)
    display.show()

# Variable to keep track of the subprocess
data_logger_process = None

def is_program_running(program_name):
    # Check if the program is already running
    for proc in psutil.process_iter(['name', 'cmdline']):
        if program_name in proc.info['cmdline']:
            return proc.pid  # Return PID if found
    return None

def run_data_logger(program, display_message):
    global data_logger_process
    # Ensure no other logger is running
    if data_logger_process is None or data_logger_process.poll() is not None:
        # Kill any existing data_logger program
        kill_data_logger()
        
        command = f"cd /home/vivek/DL && source /home/vivek/DL/venv/bin/activate && python /home/vivek/DL/{program}"
        data_logger_process = subprocess.Popen(command, shell=True, executable="/bin/bash")
        draw_text(display_message)  # Show the specific message on start
        print(f"{display_message} started.")
    else:
        print("Another Data Logger is already running.")

def kill_data_logger():
    global data_logger_process
    if data_logger_process and data_logger_process.poll() is None:
        data_logger_process.terminate()  # Terminate the process
        data_logger_process.wait()  # Ensure it has stopped
        draw_text("Stopped")  # Show "Stopped" message on stop
        time.sleep(3)
        draw_text("Ready?")
        print("Data Logger terminated.")
    else:
        print("Data Logger is not running.")

# Show initial ready message
draw_text("Ready?")
try:
    while True:
        # Check for start button press
        if GPIO.input(road_button_pin) == False:  # Start button pressed
            print("Start button pressed!")
            run_data_logger("road_data_logger.py", "Ride safe")
            time.sleep(0.2)  # Debounce delay

        # Check for road button press
        if GPIO.input(track_button_pin) == False:  # Track button pressed
            print("Road mode button pressed!")
            run_data_logger("data_logger_15th_september.py", "Send it!!!")
            time.sleep(0.2)  # Debounce delay

        # Check for kill button press
        if GPIO.input(kill_button_pin) == False:  # Kill button pressed
            print("Kill button pressed!")
            kill_data_logger()
            time.sleep(0.2)  # Debounce delay

except KeyboardInterrupt:
    draw_text("")
    GPIO.cleanup()
