import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load the data
file_path = 'racing_data_October_20_01_09.csv'  # Update this with your correct file path if needed
data = pd.read_csv(file_path)

# Extract relevant columns
latitude = data['Latitude']
longitude = data['Longitude']
speed = data['Speed (kmph)']
lean_angle = data['Lean Angle']

# Plot the racing line (trajectory)
fig = px.scatter_mapbox(
    data,
    lat="Latitude",
    lon="Longitude",
    hover_name="Timestamp",
    hover_data={"Speed (kmph)": True, "Lean Angle": True},
    color="Speed (kmph)",
    zoom=15,
    height=600,
    title="Racing Line with Speed and Lean Angle"
)

# Add lean angle to the plot as a secondary color scale
fig.add_trace(go.Scattermapbox(
    lat=latitude,
    lon=longitude,
    mode='markers',
    marker=dict(
        size=9,
        color=lean_angle,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Lean Angle (degrees)")
    ),
    hoverinfo='none'
))

# Update layout to use a mapbox style
fig.update_layout(mapbox_style="carto-positron")

# Save the plot as an HTML file
html_file_path = 'racing_line_visualization.html'  # Update this with your desired output path
fig.write_html(html_file_path)

print(f"HTML visualization saved to {html_file_path}")
