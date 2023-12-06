# 1. River Change Analysis

The objective of this Python Package is to allow for a streamlined planform analysis of large rivers using Python. This package utilizes the Google Earth Engine API to extract Landsat imagery over a user-specified region of interest. 

## 2. Description

This package allows for quick visualization of key river morphological features using Landsat Imagery. In addition, users can quickly obtain a rough estimation of annual and cumulative erosion/accretion of a river section over a period of years or decades.

## 3. Installation

Google Colab Installation:

```python
# Install the 'river_change_analysis' package directly from the Git repository.
!pip install git+https://@github.com/ianstlaurent/river_change_analysis.git
```

Python Installation:

# Install the 'river_change_analysis' package directly from the Git repository.
```python
pip3 install git+https://@github.com/ianstlaurent/river_change_analysis.git

# Install Google Authentication Library to connect to GEE API
pip3 install google-auth-oauthlib
```

## 4. Google Colab Example

### Import relevant Python Libraries

```python
# Import Relevant Python Libraries
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import binary_erosion
from rasterio.plot import show
import rasterio

# Import the Google Colab drive module
from google.colab import drive

# Mount your Google Drive. This will make the files in your Google Drive accessible from this Google Colab notebook. You'll be prompted to sign in to your Google account, and you'll need to allow Colab to access your Google Drive.
drive.mount('/content/drive')
```

### Import Python Library

After installing the Python package, the first step is to import it into Google Colab. This can be done by importing river_change_analysis; then, to make it easier to call the library in the future, you can call it something simple like rca.

```python
!pip install git+https://@github.com/ianstlaurent/river_change_analysis.git
import river_change_analysis as rca
# This will trigger the authentication flow and will prompt you to sign in to your Google account. You'll need to allow the Earth Engine Python API to access your account, giving you a code to paste into the prompt in Google Colab.
```
### Define Region of Interest

The next step is to define a region of interest (ROI) using a list of coordinates for the polygon shape. Then, use the define_roi(roi) function to turn the list of coordinates into an earth engine polygon.  If the roi is not an acceptable format or if the roi is empty, then a default roi will be used for the Lower Athabasca River in the Peace Athabasca Delta.

```python
region = rca.define_roi(roi)
```

### Process Landsat Imagery

Next, process the images using process_images function. This function requires several arguments:

start_year
end_year
month_day_start
month_day_end
roi
folder_name
file_name

```python
# Define the path to the folder where the binary river masks are stored.
folder= "CSC_497"

# Define the pattern that the filenames of the binary river masks follow.
file_pattern = "Reach_1_"

date_start = '-06-01'
date_end = '-10-31'

year_start = 1986
year_end = 2021

# Process the images for the specified years (e.g. 2000 to 2010) and region.
# This function creates tasks in the Google Earth Engine (GEE) task manager.
# You must go to the GEE task manager (https://code.earthengine.google.com/tasks) and accept the tasks to start the processing.
rca.process_images(year_start, year_end, date_start, date_end, region, folder, file_pattern)
```

### Import Landsat Imagery

The processing of the images may require some time to finish, depending on the number of years being processed. Once all the processing tasks are completed, you can import the Python masks by calling the mask_import function.

```python
binary_mask_folder_path = "/content/drive/MyDrive/CSC_497"
binary_mask_file_pattern = "Active_channel_binary_mask_reach_1_"
# Import the binary masks for the rivers.
# The masks are located in the folder specified by 'folder_path', and their filenames follow the pattern specified by 'file_pattern'.
rivers_files = rca.mask_import(binary_mask_folder_path, binary_mask_file_pattern)
```

### Import 30m DEM

Import 30m DEM and slope Geotiffs cropped to the ROI.

```python
# Choose DEM file name pattern
dem_file_pattern = "Athabasca"
# Choose the folder in Google Drive
dem_folder = "CSC_497"
# Extract from GEE DEM and slope GeoTiffs
rca.gee_extraction.import_dem(region,dem_file_pattern,dem_folder)

# Grab the DEM, Elevation, and slope GeoTiffs from the Google Drive
dem_folder_path = "/content/drive/MyDrive/CSC_497"
dem_files = rca.mask_import(dem_folder_path, dem_file_pattern)

# Load files into River Class
rca.River.load_dem(dem_files)
```

### Create River Binary Mask Objects

```python
# Create an empty list to store the analysis results for each year.
annual_data = []

# Process each river file.
for file in rivers_files:

    # Create a 'river' object for the current file. This object represents a river for a specific year.
    yearly_analysis = rca.River(file)

    # Process the river data for the current year.
    yearly_analysis.load_mask()

    # Add the analysis results for the current year to the 'annual_data' list.
    annual_data.append(yearly_analysis)
```

### Process River Binary Masks

```python
# Create Filled Water Channel Masks for each River object
# Specify the minimum island/bar size to be removed (1000 is recommended)
water_mask_min_size = 1000
rca.River.water_mask_process(annual_data, water_mask_min_size)

# Create Centerlines for each River object
# Specify the max branch removal for each centerline. The higher the number, the more points are removed from the centerline (100 is recommended)
# This may take a couple of minutes, depending on the number of binary masks
max_distance_branch_removal = 100
rca.River.process_centerline(annual_data, max_distance_branch_removal)
```

### Calculate Erosion/Accretion

```python
# Calculate then plot erosion/accretion for each River object
rca.River.quantify_erosion(annual_data)
```

### Plot All the Results

```python
# Plot any year by itself
annual_data[0].plot_self()

# Plot the migration between any two years
annual_data[-1].plot_river_migration(annual_data[0])

# Plot the annual and accumulated erosion/accretion 
rca.River.plot_erosion(annual_data)

# Plot the centerlines over time
rca.River.plot_centerline(annual_data)

#Plot the river edges over time
rca.River.plot_river_edges(annual_data)

# Create an animation of the centerline migration over time
# Provide a direct path along with filename and .mp4
folder_path_anim = '/content/drive/MyDrive/CSC_497/river_centerline_evolution.mp4'
rca.River.animate_centerline_migration(annual_data,folder_path_anim)

#Plot DEM and Slope
rca.River.plot_dem()
```









