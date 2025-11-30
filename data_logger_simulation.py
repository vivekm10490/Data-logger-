import time
import sys
import board
import adafruit_mpu6050
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
import select

# IMU Setup
i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)

# Variables for lap timing
last_cross_time = None
lap_count = 0
lap_times = []

# Display Setup
cs_pin = digitalio.DigitalInOut(board.D8)    # Chip select
dc_pin = digitalio.DigitalInOut(board.D23)   # Data/Command

# Create the SPI bus
spi = board.SPI()

# Initialize the display (128x64)
display = adafruit_ssd1306.SSD1306_SPI(128, 64, spi, dc_pin, None, cs_pin)

# Create an image for drawing
width = display.width
height = display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Load a larger font
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'  # Update this path if needed
font_size = 24  # Adjust font size as needed
font = ImageFont.truetype(font_path, font_size)

def draw_text(text):
    # Clear the display
    draw.rectangle((0, 0, width, height), outline=0, fill=0)
    
    # Calculate text size and position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2  # Center text horizontally
    y = (height - text_height) // 2  # Center text vertically
    draw.text((x, y), text, font=font, fill=255)
    
    rotated_image = image.rotate(180)
    # Update the display
    display.image(rotated_image)
    display.show()

def record_lap_time():
    global last_cross_time, lap_count, lap_times
    current_time = time.time()

    if last_cross_time is not None:
        lap_time = current_time - last_cross_time
        lap_times.append(lap_time)
        lap_count += 1
        print(f"Lap {lap_count} completed in {lap_time:.2f} seconds")

        # Update the display with the completed lap time
        lap_time_str = f"{int(lap_time // 60):02d}:{int(lap_time % 60):02d}.{int((lap_time % 1) * 1000):03d}"
        draw_text(lap_time_str)
        time.sleep(5)  # Pause for 2 seconds to show the lap time

    last_cross_time = current_time

try:
    print("Press Enter to start the first lap...")

    while True:
        if last_cross_time is None:
            input()  # Wait for the first Enter press
            last_cross_time = time.time()

        # Continuously update the display with the current lap time
        elapsed_time = time.time() - last_cross_time
        elapsed_time_str = f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}.{int((elapsed_time % 1) * 1000):03d}"
        draw_text(elapsed_time_str)

        # Use select to check for Enter press without blocking
        if select.select([sys.stdin], [], [], 0)[0]:
            input()  # Consume the Enter keypress
            record_lap_time()

        time.sleep(0.1)  # Update display every 0.1 seconds

except KeyboardInterrupt:
    print("Stopping simulation.")
    display.fill(0)
    display.show()

# When the session ends, print all lap times
print(f"Total laps: {lap_count}")
for i, lap_time in enumerate(lap_times, start=1):
    print(f"Lap {i}: {lap_time:.2f} seconds")
