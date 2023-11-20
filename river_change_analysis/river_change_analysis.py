import os
import river_width as rw
def mask_import(folder_path, file_pattern):
    # Path to your Google Drive folder
    #folder_path = "/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/River_Analysis/binary_river_masks/"
    #file_pattern = "Active_channel_binary_mask_python_"

    # List for storing file paths
    file_paths = []

    # Loop through all files in the directory
    for file_name in os.listdir(folder_path):
        if file_name.startswith(file_pattern) and file_name.endswith(".tif"):
            file_path = os.path.join(folder_path, file_name)
            file_paths.append(file_path)


    # Process each year and store in a list
    annual_data = []

    for file_path in file_paths:
        yearly_analysis = rw.YearlyRiverAnalysis(file_path)
        yearly_analysis.process()
        annual_data.append(yearly_analysis)

    yearly_analysis.quantify_migration(annual_data[0], 30)
    yearly_analysis.accretion
    yearly_analysis.erosion
