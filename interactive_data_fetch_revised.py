import pandas as pd
import os
import math
import folium
from folium.plugins import HeatMap

# Load the data from the CSV file
def get_latest_file(folder_path):
    # Get all files in the folder
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    
    # Get the latest file based on modification time
    if files:
        latest_file = max(files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
        return os.path.join(folder_path, latest_file), os.path.splitext(latest_file)[0]
    else:
        return None

# Example usage
folder_path = '/home/vivek/DL/Logs/raw/'
file_path, file_name = get_latest_file(folder_path)

# Load the data
# df = pd.read_csv(file_path)
df = pd.read_csv("/home/vivek/DL/Logs/raw/roadlog_4.csv")

# Extract relevant columns
latitudes = df['Latitude'].astype(float)
longitudes = df['Longitude'].astype(float)
speeds = df['Speed (kmph)'].astype(float)
lean_angles = df['Lean Angle'].astype(float)

# Create a base map centered around the average location
map_center = [latitudes.mean(), longitudes.mean()]
racing_map = folium.Map(location=map_center, zoom_start=16)

# Plot the racing line with color coding for speed
for i in range(len(latitudes)-1):
    speed_value = speeds
    if not math.isnan(speed_value):
        color = f"#{int(min(speed_value, 100) * 2.55):02x}0000"  # Red gradient based on speed
    else:
        color = "#000000"  # Default to black or any other fallback color
    folium.PolyLine(
        locations=[(latitudes[i], longitudes[i]), (latitudes[i+1], longitudes[i+1])],
        color = color,  # Default to black or any other fallback color
        weight=5
    ).add_to(racing_map)

# Add tooltips for lean angle and speed at each point
for i, (lat, lon, speed, lean_angle) in enumerate(zip(latitudes, longitudes, speeds, lean_angles)):
    folium.CircleMarker(
        location=[lat, lon],
        radius=3,
        color='green',
        fill=True,
        fill_color='blue',
        tooltip=f"Speed: {speed} km/h, Lean Angle: {lean_angle:.2f}°"
    ).add_to(racing_map)

# Save the map to an HTML file
racing_map.save('/home/vivek/DL/Logs/parsed/racing_line_visualization.html')

print("Racing line visualization with tooltips has been generated and saved as 'racing_line_visualization.html'")

