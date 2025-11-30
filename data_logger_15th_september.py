import os
import serial
import time
import pynmea2
import board
import adafruit_mpu6050
import csv
import math
from geopy.distance import geodesic
import digitalio
import adafruit_ssd1306
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

# GPS Setup
port = "/dev/serial0"
ser = serial.Serial(port, baudrate=9600, timeout=1)

# IMU Setup
i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)

# Mmrt coordinates
#start_finish_coords = (13.0001169, 79.9891869)
# kalkare tea shop
# start_finish_coords = (13.031304556194229, 77.66127211356375)
# jayanthi nagar signal
# start_finish_coords = (13.02892763322248, 77.66367313635548)
# Motarrad 
# start_finish_coords = (13.0340690, 77.6574236)
# 7 plates
# start_finish_coords = (13.0231718, 77.6397435)
# aruani
# start_finish_coords = (12.8764318, 77.7430639)
#velocity
start_finish_coords = (13.0711226, 77.8387238)


# Variables for lap timing
last_cross_time = None
lap_count = 0
lap_times = []

# Geofence radius (in meters)
geofence_radius = 10  # Adjust as necessary

# Cooldown period (in seconds)
cooldown_time = 15  # Time after crossing the start/finish line before logging another lap

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
    
    # Update the display
    display.image(image)
    display.show()

# CSV File for Data Logging
now = datetime.now()
time_str = now.strftime("%B_%d_%H_%M_%S")
log_dir = "/home/vivek/DL/Logs/raw"  # Change to your actual log directory
laptime_dir = "/home/vivek/DL/Logs/laptime"

# Ensure log directory exists
os.makedirs(log_dir, exist_ok=True)

# Get list of existing log files
existing_logs = [f for f in os.listdir(log_dir) if f.startswith("tracklog_") and f.endswith(".csv")]

# Find the highest sequence number
sequence_numbers = []
for log in existing_logs:
    try:
        seq_num = int(log.split("_")[1].split(".")[0])  # Extract number
        sequence_numbers.append(seq_num)
    except ValueError:
        pass  # Ignore files with incorrect format

next_seq = max(sequence_numbers, default=0) + 1  # Increment sequence

# Create new log file
log_filename = f"tracklog_{next_seq}.csv"
lap_filename = f"tracklog_{next_seq}.log"
csv_file = os.path.join(log_dir, log_filename)
lap_time_file = os.path.join(laptime_dir, lap_filename)
# csv_file = f'/home/vivek/DL/Logs/raw/racing_data_{time_str}.csv'
# lap_time_file = f'/home/vivek/DL/Logs/laptime/lap_times_{time_str}.log'

with open(csv_file, mode='w') as file, open(lap_time_file, mode='w') as lap_file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed (kmph)", "Lean Angle", "Gyro (x,y,z)"])

    def calculate_lean_angle(accel_x, accel_z):
        lean_angle = math.atan2(accel_x, accel_z) * (180/math.pi)
        lean_angle = lean_angle + 177
        if lean_angle > 180:
            lean_angle = -(360 - lean_angle)
        return lean_angle

    def is_within_geofence(current_coords, center_coords, radius):
        """Check if the current coordinates are within the geofence radius."""
        distance = geodesic(current_coords, center_coords).meters
        return distance <= radius

    def parseGPS(data):
        global last_cross_time, lap_count
        if data[0:6] in ["$GPRMC", "$GNRMC"]:
            msg = pynmea2.parse(data)
            timestamp = msg.timestamp
            latitude = msg.latitude
            longitude = msg.longitude
            if msg.spd_over_grnd is not None:
                converted_speed = msg.spd_over_grnd * 1.852
                speed = 0 if converted_speed < 4 else converted_speed
            else:
                speed = 0

            current_coords = (float(latitude), float(longitude))

            # Check if the current position is within the geofence
            if is_within_geofence(current_coords, start_finish_coords, geofence_radius):
                # Only record the lap time if the cooldown period has passed
                if last_cross_time is None or (time.time() - last_cross_time) > cooldown_time:
                    record_lap_time()

            # IMU Data
            accel_x, accel_y, accel_z = mpu.acceleration
            lean_angle = calculate_lean_angle(accel_x, accel_z)
            gyro = mpu.gyro

            # Log Data
            writer.writerow([timestamp, latitude, longitude, speed, lean_angle, gyro])
            print(f"Logged data at {timestamp}")

    def record_lap_time():
        global last_cross_time, lap_count, lap_times
        current_time = time.time()

        if last_cross_time is not None:
            lap_time = current_time - last_cross_time
            lap_times.append(lap_time)
            lap_count += 1
            lap_time_str = f"{int(lap_time // 60):02d}:{int(lap_time % 60):02d}.{int((lap_time % 1) * 1000):03d}"
            
            # Log the lap time to the lap times file
            lap_file.write(f"Lap {lap_count}: {lap_time_str}\n")
            lap_file.flush()  # Ensure data is written immediately
            writer.writerow([f"Lap {lap_count} completed in {lap_time:.2f} seconds"])
            writer.writerow([f"Lap {lap_count+1} started "])
            print(f"Lap {lap_count} completed in {lap_time:.2f} seconds")

            # Update the display with lap time
            draw_text(lap_time_str)

        last_cross_time = current_time

    while True:
        try:
            # GPS Data
            data = ser.readline().decode('ascii', errors='replace')
            parseGPS(data)

            # Display the ongoing lap time
            if last_cross_time is not None:
                elapsed_time = time.time() - last_cross_time
                elapsed_time_str = f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}.{int((elapsed_time % 1) * 1000):03d}"
                draw_text(elapsed_time_str)

        except KeyboardInterrupt:
            print("Stopping data logging.")
            display.fill(0)
            display.show()
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

# When the session ends, print all lap times
print(f"Total laps: {lap_count}")
for i, lap_time in enumerate(lap_times, start=1):
    print(f"Lap {i}: {lap_time:.2f} seconds")

