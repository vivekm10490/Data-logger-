import pandas as pd
import folium

# Load your CSV file
df = pd.read_csv('racing_data.csv')

# Create a map centered around the average latitude and longitude
map_center = [df['Latitude'].mean(), df['Longitude'].mean()]
map_ = folium.Map(location=map_center, zoom_start=15)

# Add a line connecting all the GPS points
locations = list(zip(df['Latitude'], df['Longitude']))
folium.PolyLine(locations, color="blue", weight=2.5, opacity=1).add_to(map_)

# Save the map to an HTML file
map_.save('gps_track_map.html')

