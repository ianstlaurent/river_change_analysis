# Purpose: Import binary river masks from local/Google Drive folder
# Author: Ian St. Laurent

import os
def mask_import(folder_path, file_pattern):

    # If no folder_path is provided, prompt the user to enter one
    if not folder_path:
        folder_path = input("Enter path to Google Drive folder: ")

    # If no file_pattern is provided, prompt the user to enter one
    if not file_pattern:
        file_pattern = input("Enter file pattern: ")

    # Initialize a list to store the file paths
    file_paths = []

    # Loop through all files in the directory
    for file_name in os.listdir(folder_path):
        # If the file name starts with the file pattern and ends with ".tif"
        if file_name.startswith(file_pattern) and file_name.endswith(".tif"):
            # Construct the full file path
            file_path = os.path.join(folder_path, file_name)
            # Add the file path to the list
            file_paths.append(file_path)

    # Return the list of file paths
    return file_paths
