import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import re
import os

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

# Create a single figure with subplots for map and statistics
fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3], specs=[[{"type": "mapbox"}, {"type": "table"}]])

# Create dropdown menu options and traces
dropdown_options = []
map_traces = []
table_traces = []

for i, (lap, lap_rows) in enumerate(lap_data.items()):
    lap_df = pd.DataFrame(lap_rows)
    
    # Create scatter_mapbox trace for this lap
    scatter_trace = go.Scattermapbox(
        lat=lap_df["Latitude"],
        lon=lap_df["Longitude"],
        mode="markers",
        marker=dict(size=8, color=lap_df["Speed (kmph)"], colorscale="Viridis", showscale=True),
        text=lap_df.apply(lambda row: f"Speed: {row['Speed (kmph)']:.2f} km/h<br>Lean Angle: {row['Lean Angle']:.2f}°", axis=1),
        hoverinfo="text",
        name=f"Lap {lap}",
        visible=(i == 0)  # First lap (i==0) is visible, others are not
    )
    map_traces.append(scatter_trace)
    
    # Create table trace for lap statistics
    top_speed = lap_df['Speed (kmph)'].max()
    max_lean_angle = lap_df['Lean Angle'].abs().max()
    lap_time = lap_times.get(lap, "Unknown")
    
    table_trace = go.Table(
        header=dict(values=["Statistic", "Value"]),
        cells=dict(values=[
            ["Top Speed", "Max Lean Angle", "Lap Time"],
            [f"{top_speed:.2f} km/h", f"{max_lean_angle:.2f}°", f"{lap_time} seconds"]
        ]),
        visible=(i == 0)  # First lap (i==0) is visible, others are not
    )
    table_traces.append(table_trace)

    # Create dropdown options
    visibility = [False] * len(lap_data) * 2  # For both map and table traces
    visibility[i] = True  # Map trace
    visibility[i + len(lap_data)] = True  # Table trace
    
    dropdown_options.append(dict(
        args=[{"visible": visibility}],
        label=f"Lap {lap}",
        method="update"
    ))

# Add all traces to the figure
for trace in map_traces:
    fig.add_trace(trace, row=1, col=1)
for trace in table_traces:
    fig.add_trace(trace, row=1, col=2)

# Update layout
fig.update_layout(
    updatemenus=[dict(
        active=0,
        buttons=dropdown_options,
        direction="down",
        pad={"r": 10, "t": 10},
        showactive=True,
        x=0.1,
        xanchor="left",
        y=1.1,
        yanchor="top"
    )],
    mapbox=dict(
        style="open-street-map",
        center=dict(lat=data["Latitude"].mean(), lon=data["Longitude"].mean()),
        zoom=13
    ),
    height=800,
    title_text="Race Log Analysis",
    showlegend=False
)

# Save the interactive plot as a single HTML file
parsed_path = '/home/vivek/DL/Logs/parsed/'
output_file = parsed_path+file_name+'.html'
fig.write_html(output_file, full_html=True, include_plotlyjs='cdn')
print(f"Interactive race analysis saved to {output_file}")
