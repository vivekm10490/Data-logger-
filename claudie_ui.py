import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import folium
from folium.plugins import MarkerCluster
import webbrowser
import os
import io

class RaceLogParserUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Race Log Parser with Map")
        self.master.geometry("800x600")

        self.create_widgets()
        self.data = None

    def create_widgets(self):
        # File selection
        self.select_file_button = tk.Button(self.master, text="Select CSV File", command=self.select_file)
        self.select_file_button.pack(pady=10)

        # Display area
        self.tree = ttk.Treeview(self.master)
        self.tree.pack(expand=True, fill='both', padx=10, pady=10)

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.master, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side='right', fill='y')
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # Map button
        self.map_button = tk.Button(self.master, text="Generate Map", command=self.generate_map)
        self.map_button.pack(pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if file_path:
            self.parse_csv(file_path)

    def parse_csv(self, file_path):
        # Clear existing data
        for i in self.tree.get_children():
            self.tree.delete(i)

        # Read CSV file
        self.data = pd.read_csv(file_path)

        # Set up columns
        self.tree["columns"] = list(self.data.columns)
        self.tree["show"] = "headings"

        for column in self.data.columns:
            self.tree.heading(column, text=column)
            self.tree.column(column, width=100)

        # Insert data
        for _, row in self.data.iterrows():
            self.tree.insert("", "end", values=list(row))

    def generate_map(self):
        if self.data is None:
            tk.messagebox.showerror("Error", "Please load a CSV file first.")
            return

        # Create a map centered on the mean of latitude and longitude
        center_lat = self.data['Latitude'].mean()
        center_lon = self.data['Longitude'].mean()
        m = folium.Map(location=[center_lat, center_lon], zoom_start=15)

        # Add markers for each point
        marker_cluster = MarkerCluster().add_to(m)
        for _, row in self.data.iterrows():
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=f"Time: {row['Timestamp']}<br>Speed: {row['Speed (kmph)']}<br>Lean Angle: {row['Lean Angle']}",
            ).add_to(marker_cluster)

        # Save map to a temporary file and open in browser
        map_path = "race_log_map.html"
        m.save(map_path)
        webbrowser.open('file://' + os.path.realpath(map_path))

if __name__ == "__main__":
    root = tk.Tk()
    app = RaceLogParserUI(root)
    root.mainloop()
