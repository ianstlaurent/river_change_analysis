#!/usr/bin/env python
import sys
"""Tests for `river_change_analysis` package."""
import river_change_analysis as rca

folder_path = "CSC_497"
dem_folder_path = "/content/drive/MyDrive/ content drive MyDrive CSC_497"
file_pattern = "Reach_1_"
file_pattern_2 = "Reach_2_"
dem_file_pattern = "Athabasca"
date_start = '-06-01'
date_end = '-10-01'

year_start = 1986
year_end = 2021

region = rca.define_roi([])

rca.process_images(year_start, year_end, date_start, date_end,region, folder_path, file_pattern)

rivers_files = rca.mask_import('/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/rca/binary_river_masks/', 'Active_channel_binary_mask_python_')

# Process each year and store in a list
annual_data = []
for file in rivers_files:
    yearly_analysis = rca.river_width.river(file)
    yearly_analysis.process()
    annual_data.append(yearly_analysis)


yearly_analysis.plot_migration(annual_data[0])
yearly_analysis.quantify_migration(annual_data[0], 30)
print(yearly_analysis.erosion)
print(yearly_analysis.accretion)


