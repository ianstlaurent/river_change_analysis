#!/usr/bin/env python
import sys
"""Tests for `river_change_analysis` package."""
#sys.path.append("/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/river_change_analysis/river_change_analysis")
import river_change_analysis
#print(river_change_analysis.__path__)

# Now you can use mask_import and YearlyRiverAnalysis through the rc alias
rivers_files = river_change_analysis.mask_import('/Users/ian/Desktop/School/Fall 2023/CSC 497/Python_Library/river_change_analysis/binary_river_masks/', 'Active_channel_binary_mask_python_')

# Process each year and store in a list
annual_data = []
for file in rivers_files:
    yearly_analysis = river_change_analysis.river_width.YearlyRiverAnalysis(file)
    yearly_analysis.process()
    annual_data.append(yearly_analysis)


yearly_analysis.plot_migration(annual_data[0])
yearly_analysis.quantify_migration(annual_data[0], 30)
print(yearly_analysis.erosion)
print(yearly_analysis.accretion)

