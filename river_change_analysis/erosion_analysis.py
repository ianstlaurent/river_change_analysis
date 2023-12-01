import ee
from rasterio.plot import show
import matplotlib.pyplot as plt
import rasterio
import numpy as np

def quantify_migration(annual_data, dem):
    erosion_data = []
    accretion_data = []
    erosion_volume_data = []
    accretion_volume_data = []
    years = [int(river.year) for river in annual_data]

    # Calculate erosion for each year compared to the last
    for i in range(1, len(annual_data)):

        annual_data[i].quantify_migration(annual_data[i-1], dem)
        erosion_data.append(annual_data[i].erosion)
        accretion_data.append(annual_data[i].accretion)
        erosion_volume_data.append(annual_data[i].erosion_volume)
        accretion_volume_data.append(annual_data[i].accretion_volume)


    # Plot the erosion data over time
    plt.figure(figsize=(10, 5))
    plt.plot(years[1:], erosion_data, marker='o', linestyle='-', color='red')
    plt.title('Annual Erosion Over Time')
    plt.xlabel('Year')
    plt.ylabel('Erosion (km2)')
    plt.grid(True)
    plt.show()

    # Plot the accretion data over time
    plt.figure(figsize=(10, 5))
    plt.plot(years[1:], accretion_data, marker='o', linestyle='-', color='red')
    plt.title('Annual Accretion Over Time')
    plt.xlabel('Year')
    plt.ylabel('Accretion (km2)')
    plt.grid(True)
    plt.show()

    # Plot the erosion volume data over time
    plt.figure(figsize=(10, 5))
    plt.plot(years[1:], erosion_volume_data, marker='o', linestyle='-', color='red')
    plt.title('Erosion Volume Over Time')
    plt.xlabel('Year')
    plt.ylabel('Erosion Volume (km3)')
    plt.grid(True)
    plt.show()

    # Plot the erosion volume data over time
    plt.figure(figsize=(10, 5))
    plt.plot(years[1:], accretion_volume_data, marker='o', linestyle='-', color='red')
    plt.title('Accretion Volume Over Time')
    plt.xlabel('Year')
    plt.ylabel('Accretion Volume (km3)')
    plt.grid(True)
    plt.show()



