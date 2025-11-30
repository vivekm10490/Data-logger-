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
import obd

# GPS Setup
port = "/dev/serial0"
ser = serial.Serial(port, baudrate=9600, timeout=1)

# IMU Setup
i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)

# GPS coordinates for geofencing (start/finish line)
start_finish_coords = (13.0001169, 79.9891869)

# Variables for lap timing
last_cross_time = None
lap_count = 0
lap_times = []
geofence_radius = 30  # in meters
cooldown_time = 15  # Cooldown period before logging the next lap

# Display Setup
cs_pin = digitalio.DigitalInOut(board.D8)
dc_pin = digitalio.DigitalInOut(board.D23)
spi = board.SPI()
display = adafruit_ssd1306.SSD1306_SPI(128, 64, spi, dc_pin, None, cs_pin)
width, height = display.width, display.height
image = Image.new('1', (width, height))
draw = ImageDraw.Draw(image)

# Load a larger font
font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
font_size = 24
font = ImageFont.truetype(font_path, font_size)

# OBD-II Setup
connection = obd.OBD()

# Define OBD commands
throttle_command = obd.commands.THROTTLE_POS
rpm_command = obd.commands.RPM

# Sending an OBD-II command
def send_obd_command(command):
    sock.sendall((command + "\r").encode())  # Send command with carriage return
    response = sock.recv(1024).decode().strip()  # Read response and decode
    return response

# rpm_command = '2121'
# throttle_command = '0111'
# afr_command = '212f'

# CSV File for Data Logging
now = datetime.now()
time_str = now.strftime("%B_%d_%H_%M")
csv_file = f'racing_data_{time_str}.csv'
lap_time_file = f'lap_times_{time_str}.log'


with open(csv_file, mode='w') as file, open(lap_time_file, mode='w') as lap_file:
    writer = csv.writer(file)
    writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed (kmph)", "Lean Angle", "Gyro (x,y,z)", "Throttle"])

    def calculate_lean_angle(accel_x, accel_z):
        lean_angle = math.atan2(accel_x, accel_z) * (180/math.pi)
        return lean_angle

    def is_within_geofence(current_coords, center_coords, radius):
        """Check if the current coordinates are within the geofence radius."""
        distance = geodesic(current_coords, center_coords).meters
        return distance <= radius

    def parseGPS(data):
        global last_cross_time, lap_count
        if data[0:6] ["$GPRMC", "$GNRMC"]:
            msg = pynmea2.parse(data)
            timestamp = msg.timestamp
            latitude = msg.latitude
            longitude = msg.longitude
            speed = msg.spd_over_grnd * 1.852 if msg.spd_over_grnd is not None else 0
            current_coords = (float(latitude), float(longitude))

            # Check if the current position is within the geofence
            if is_within_geofence(current_coords, start_finish_coords, geofence_radius):
                if last_cross_time is None or (time.time() - last_cross_time) > cooldown_time:
                    record_lap_time()

            # IMU Data
            accel_x, accel_y, accel_z = mpu.acceleration
            lean_angle = calculate_lean_angle(accel_x, accel_z)
            gyro = mpu.gyro            
            
            # Base value for rpm and throttle position
            rpm = 0
            throttle = 0
            
            # OBD-II Data
            if connection.is_connected():
                # rpm = query_rpm()
                throttle = query_throttle()
                # afr = query_afr()

            # Log Data
            writer.writerow([timestamp, latitude, longitude, speed, lean_angle, gyro, throttle])
            print(f"Logged data at {timestamp}")

    def query_rpm():
        response_rpm = connection.query(rpm_command, force=True)
        rpm = response_rpm.value.magnitude if response_rpm.value else None
        return rpm

    def query_throttle():
        response_tps = connection.query(throttle_command)
        tps = response_tps.value.magnitude if response_tps.value else None
        return tps
        '''
        position = tps * 100 / 255
        percentage = ((position-11)/(89-11)*100)
        return percentage
       '''
    '''
    def query_afr():
        afr_response = send_obd_command(afr_command)
        hex_data = afr_response.split()
        if hex_data[0] != '212f':
            A = int(hex_data[3], 16)
            B = int(hex_data[4], 16)
        else:
            A = int(hex_data[3], 16)
            B = int(hex_data[4], 16)
        afr = ((A*256) + B) / 2378
        return afr
    '''

    def record_lap_time():
        global last_cross_time, lap_count, lap_times
        current_time = time.time()

        if last_cross_time is not None:
            lap_time = current_time - last_cross_time
            lap_times.append(lap_time)
            lap_count += 1
            lap_time_str = f"{int(lap_time // 60):02d}:{int(lap_time % 60):02d}.{int((lap_time % 1) * 1000):03d}"
            
            lap_file.write(f"Lap {lap_count}: {lap_time_str}\n")
            lap_file.flush()
            
            writer.writerow([f"Lap {lap_count} completed in {lap_time:.2f} seconds"])
            writer.writerow([f"Lap {lap_count+1} started "])
            print(f"Lap {lap_count} completed in {lap_time:.2f} seconds")
            draw_text(lap_time_str)

        last_cross_time = current_time

    def draw_text(text):
        # Clear the display
        draw.rectangle((0, 0, width, height), outline=0, fill=0)
        
        # Calculate text size and position
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Rotate the text 180 degrees
        draw.text((x, y), text, font=font, fill=255)
        rotated_image = image.rotate(180)  # Upside down
        display.image(rotated_image)
        display.show()

    while True:
        try:
            # GPS Data
            data = ser.readline().decode('ascii', errors='replace')
            parseGPS(data)

            # Display ongoing lap time
            if last_cross_time is not None:
                elapsed_time = time.time() - last_cross_time
                elapsed_time_str = f"{int(elapsed_time // 60):02d}:{int(elapsed_time % 60):02d}.{int((elapsed_time % 1) * 1000):03d}"
                draw_text(elapsed_time_str)

            time.sleep(1)  # Log data every 0.5 seconds

        except KeyboardInterrupt:
            print("Stopping data logging.")
            display.fill(0)
            display.show()
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

print(f"Total laps: {lap_count}")
for i, lap_time in enumerate(lap_times, start=1):
    print(f"Lap {i}: {lap_time:.2f} seconds")
