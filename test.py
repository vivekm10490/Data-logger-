
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
full_path, file_path= get_latest_file(folder_path)

# Load the data
print(full_path)
print(file_path)
