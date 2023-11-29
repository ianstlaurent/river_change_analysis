from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from skimage.filters import sobel
import os
import rasterio
import numpy as np
from shapely.geometry import LineString


class river:
    def __init__(self, mask_file_path):
        self.file_path = mask_file_path
        self.year = None
        self.mask = None
        self.centerline = None
        self.edges = None
        self.buffered = None
        self.widths = None
        self.avg_width = None
        self.buffer_distance = None
        self.wra = None
        self.wavg = None
        self.x_coords = None
        self.y_coords = None
        self.erosion = None
        self.accretion = None
        self.river_elevation = None
        self.erosion_correlated_with_elevation = None
        self.accretion_correlated_with_elevation = None

    def process(self):
        # Load river mask
        with rasterio.open(self.file_path) as dataset:
            self.mask = dataset.read(1)  # Read the first band into a 2D array
            self.year = self.file_path[-8:-4]
            # Skeletonize the mask to get the centerline
            self.centerline = skeletonize(self.mask)

            # Get the edges of the mask
            self.edges = sobel(self.mask)

            # Extract the coordinates of the centerline
            y_coords, x_coords = np.where(self.centerline)

            # Create a LineString from the centerline array
            centerline_geom = LineString(zip(x_coords, y_coords))
            self.widths = self.mask.sum(axis=1)

            self.widths = self.widths[self.widths > 50]
            self.avg_width = np.mean(self.widths)
            self.buffer_distance = self.avg_width / 2
            # Buffer the LineString to create a Polygon
            self.y_coords = y_coords
            self.x_coords = x_coords

            # Convert the coordinate lists to numpy arrays if they aren't already
            # Create a new LineString with the smoothed coordinates
            #self.centerline = LineString(zip(x_coords_smooth, y_coords_smooth))

            # Compute angles and curvatures here

            self.Wra = self.mask.sum() / centerline_geom.length

            self.Wavg = np.mean(self.widths)

    def plot(self):
        # Plot the mask
        fig, ax = plt.subplots(figsize=(12, 8))

        # Plot the mask with a colormap that represents water
        ax.imshow(self.mask, cmap='Blues', interpolation='none', alpha=0.7)
        ax.imshow(self.edges, cmap='Greens', interpolation='none', alpha=0.5)
        #ax.scatter(self.x_coords, self.y_coords, color='red', s=1)
        plt.title('Athabasca River Mask ' + str(self.year))


        output_dir = '/content/drive/MyDrive/CSC_497/Plots/'
        output_file_path = os.path.join(output_dir, f'Athabasca_River_Mask_Reach_2_{self.year}.jpeg')
        plt.savefig(output_file_path, format='jpeg', dpi=300)

        plt.show()

    def plot_migration(self, other):
      migration = self.mask.astype(int) - other.mask.astype(int)

      # Plot the migration
      # Positive values (areas that are only in the current year's mask) in red
      # Negative values (areas that are only in the other year's mask) in blue
      fig, ax = plt.subplots(figsize=(20, 10))
      cmap = plt.get_cmap('bwr')
      im = ax.imshow(migration, cmap=cmap, vmin=-1, vmax=1)

      # Create an axes for colorbar.
      cax = fig.add_axes([ax.get_position().x1 + 0.01, ax.get_position().y0, 0.02, ax.get_position().height])
      colorbar = plt.colorbar(im, cax=cax)  # Place the colorbar in the axes created
      colorbar.set_label('Erosion (Red) and Accretion (Blue)', rotation=270, labelpad=15)

      # Set the title to be in the center
      ax.set_title('River Migration: 1986 Compared to 2021', pad=20, ha='center')

      plt.show()


    def quantify_migration(self, other, pixel_area):
      erosion = (self.mask.astype(int) - other.mask.astype(int)) > 0
      accretion = (other.mask.astype(int) - self.mask.astype(int)) > 0
      no_change = (self.mask.astype(int) == other.mask.astype(int)) & (self.mask.astype(int) == 1)

      self.erosion = np.sum(((erosion) * (pixel_area**2))) / 1000000
      self.accretion = np.sum(((accretion) * (pixel_area**2))) / 1000000
      no_change_area = ((no_change) * pixel_area)
      elevation_change = self.river_elevation - other.river_elevation
      self.erosion_correlated_with_elevation = np.sum((elevation_change < 0) & (self.mask > 0))
      self.accretion_correlated_with_elevation = np.sum((elevation_change > 0) & (self.mask > 0))

