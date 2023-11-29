#Python Script to download DEMs from Google Earth Engine
import ee
from rasterio.plot import show
import matplotlib.pyplot as plt
import rasterio

class dem:
    def __init__(self, roi):
        self.roi = roi
        self.dem = None
        self.elevation = None
        self.slope = None

    def process(self, files):
        with rasterio.open(files[0]) as src:
            self.dem = src.read(1)

        with rasterio.open(files[1]) as src:
            self.elevation = src.read(1)

        with rasterio.open(files[2]) as src:
            self.slope = src.read(1)

    def plot_dem(self):
        fig, axs = plt.subplots(1, 3, figsize=(30,10))  # 1 row, 3 columns

        show(self.dem, ax=axs[0])
        axs[0].set_title('DEM')

        show(self.elevation, ax=axs[1])
        axs[1].set_title('Elevation')

        show(self.slope, ax=axs[2])
        axs[2].set_title('Slope')

        plt.tight_layout()
        plt.show()











