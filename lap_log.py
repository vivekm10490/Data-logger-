import serial
import time
import pynmea2
import board
import adafruit_mpu6050
import csv
import math

# GPS Setup
port = "/dev/serial0"
ser = serial.Serial(port, baudrate=9600, timeout=1)

# IMU Setup
i2c = board.I2C()
mpu = adafruit_mpu6050.MPU6050(i2c)

def calculate_lean_angle(accel_x, accel_z):
    lean_angle = math.atan2(accel_x, accel_z) * (180/math.pi)
    return lean_angle

# CSV File for Data Logging
with open('racing_data.csv', mode='w') as file:
    writer = csv.writer(file)
    # writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed (kmph)", "Acceleration (x,y,z)", "Gyro (x,y,z)"])
    writer.writerow(["Timestamp", "Latitude", "Longitude", "Speed (kmph)", "lean_angle", "Gyro (x,y,z)"])

    while True:
        try:
            # GPS Data
            data = ser.readline().decode('ascii', errors='replace')
            if data[0:6] == "$GPRMC":
                msg = pynmea2.parse(data)
                timestamp = msg.timestamp
                latitude = msg.latitude
                longitude = msg.longitude
                speed = msg.spd_over_grnd
                
                # IMU Data
                accel_x, accel_y, accel_z = mpu.acceleration
                lean_angle = calculate_lean_angle(accel_x, accel_z)
                gyro = mpu.gyro

                # Log Data
                writer.writerow([timestamp, latitude, longitude, speed, lean_angle, gyro])
                print(f"Logged data at {timestamp}")

        except KeyboardInterrupt:
            print("Stopping data logging.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue

