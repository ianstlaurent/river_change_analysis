# 1. River Change Analysis

The objective of this Python Package is to allow for a streamlined planform analysis of large rivers using Python. This package utilizes the Google Earth Engine API to extract Landsat imagery over a user-specified region of interest. The code then

## 2. Description


## 3. Installation

Google Colab Installation:

```python
# Install the 'river_change_analysis' package directly from the Git repository.
!pip install git+https://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@github.com/ianstlaurent/river_change_analysis.git
```


## 4. Example

### Import relevant Python Libraries

```python
# Import Relevant Python Libraries
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from scipy.ndimage import binary_erosion

# Import the Earth Engine Python API library
import ee

# Trigger the authentication flow. This will prompt you to sign in to your Google account.
# You'll need to allow the Earth Engine Python API to access your account,
# then you'll be given a code to paste into the prompt in Colab.
ee.Authenticate()

# Initialize the Earth Engine Python API. This prepares the API to make requests to Earth Engine's servers.
# You need to do this before you can use Earth Engine functions.
ee.Initialize()

# Import the Google Colab drive module
from google.colab import drive

# Mount your Google Drive. This will make the files in your Google Drive accessible from this Google Colab notebook.
# You'll be prompted to sign in to your Google account, and you'll need to allow Colab to access your Google Drive.
drive.mount('/content/drive')
```

### Import Python Library

The first step after installing the Python package is to import it into Google Colab. This can be done by importing river_change_analysis then to make it easier to call the library in the future you can call it something simple like rca.

```python
import river_change_analysis as rca
```
### Define Region of Interest

Next step is to define region of interest (ROI) using a list of coordinates for the polygon shape. Then use the define_roi(roi) function to turn the list of coordinates into a earth engine polygon.  If the roi is not an acceptable format or if the roi is empty then a defauly roi will be used for the Lower Athabasca River in the Peace Athabasca Delta.

```python
region = rca.define_roi(roi)
```

### Process Landsat Imagery

Next, process the images using process_images function. This function requires several arugments:

start_year
end_year
month_day_start
month_day_end
roi
folder_name
file_name

```python
# Define the path to the folder where the binary river masks are stored.
folder_path = "/content/drive/MyDrive/CSC_497/"

# Define the pattern that the filenames of the binary river masks follow.
file_pattern = "Active_channel_binary_mask_reach_1_"

date_start = '06-01'
date_end = '09-31'

year_start = 1986
year_end = 2021

# Process the images for the specified years (e.g. 2000 to 2010) and region.
# This function creates tasks in the Google Earth Engine (GEE) task manager.
# You'll need to go to the GEE task manager (https://code.earthengine.google.com/tasks) and accept the tasks to start the processing.
rca.process_images(year_start, year_end, date_start, date_end, region, folder_path, file_pattern)
```

### Import Landsat Imagery

The processing of the images may require some time to finish depending on the number of years being processes. Once all the processing tasks are completed, you can import the Python masks by calling the mask_import function.

```python
# Import the binary masks for the rivers.
# The masks are located in the folder specified by 'folder_path', and their filenames follow the pattern specified by 'file_pattern'.
rivers_files = rca.mask_import(folder_path, file_pattern)
```

###





