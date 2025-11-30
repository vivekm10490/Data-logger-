import pandas as pd
import plotly.express as px
import re

# Load the data
file_path = '/home/vivek/DL/racing_data_September_01_11_42.csv'  # Update this path to your CSV file location
data = pd.read_csv(file_path)

# Initialize variables
lap_data = {}
current_lap = None
lap_times = {}

# Function to detect and process lap start/end events
def process_lap_event(row):
    global current_lap
    event = str(row['Timestamp'])
    if 'started' in event:
        current_lap = int(re.search(r'Lap (\d+) started', event).group(1))
        lap_data[current_lap] = []
        print(f"Lap {current_lap} started")
    elif 'completed' in event and current_lap is not None:
        lap_duration = float(re.search(r'completed in (\d+\.?\d*) seconds', event).group(1))
        lap_times[current_lap] = lap_duration
        print(f"Lap {current_lap} completed in {lap_duration} seconds")
        current_lap = None

# Process the data
for _, row in data.iterrows():
    if pd.isna(row['Latitude']):  # This is a lap event
        process_lap_event(row)
    elif current_lap is not None:
        lap_data[current_lap].append(row)

# Create plots for each lap
for lap, lap_rows in lap_data.items():
    lap_df = pd.DataFrame(lap_rows)
    
    fig = px.scatter_mapbox(
        lap_df,
        lat="Latitude",
        lon="Longitude",
        color="Speed (kmph)",
        hover_data={"Speed (kmph)": True, "Lean Angle": True},
        zoom=14,
        height=600,
        title=f"Racing Line for Lap {lap}"
    )
    
    fig.update_layout(mapbox_style="open-street-map")
    
    # Save each lap plot as an HTML file
    html_file_path = f'racing_line_lap_{lap}.html'
    fig.write_html(html_file_path)
    print(f"Lap {lap} plot saved to {html_file_path}")

# Generate a simple HTML report
html_report = '<h1>Racing Report</h1>'
for lap, lap_rows in lap_data.items():
    lap_df = pd.DataFrame(lap_rows)
    top_speed = lap_df['Speed (kmph)'].max()
    max_lean_angle = lap_df['Lean Angle'].abs().max()
    lap_time = lap_times.get(lap, "Unknown")
    
    html_report += f"<h2>Lap {lap}</h2>"
    html_report += f"<p>Top Speed: {top_speed:.2f} km/h</p>"
    html_report += f"<p>Max Lean Angle: {max_lean_angle:.2f} degrees</p>"
    html_report += f"<p>Lap Time: {lap_time} seconds</p>"
    html_report += f'<a href="racing_line_lap_{lap}.html">View Lap {lap} Plot</a><br><br>'

# Save the report as an HTML file
report_file_path = 'racing_report.html'
with open(report_file_path, 'w') as report_file:
    report_file.write(html_report)
print(f"HTML racing report saved to {report_file_path}")
