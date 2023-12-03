from skimage.morphology import skeletonize
import matplotlib.pyplot as plt
from skimage.filters import sobel
import os
import rasterio
import numpy as np
from shapely.geometry import LineString
from scipy.ndimage import distance_transform_edt, sobel
from skimage.morphology import remove_small_objects
from scipy.ndimage import distance_transform_edt, gaussian_gradient_magnitude
from skimage.morphology import skeletonize, thin
from skimage.filters import threshold_otsu
from scipy.ndimage import binary_erosion



class River:
    def __init__(self, mask_file_path):
        """
        Initialize a River object.

        Args:
            mask_file_path (str): Path to the mask file.
        """
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
        self.erosion_volume = None
        self.accretion_volume = None


    def process(self):
        """
        Process the river mask to extract the centerline.
        """
        # Load river mask
        with rasterio.open(self.file_path) as dataset:
            self.mask = dataset.read(1)  # Read the first band into a 2D array
            self.year = self.file_path[-8:-4]

    def find_end_points(centerline):
        # Use a more sensitive method to identify end points
        # Create a padded version of the centerline to handle edge cases
        padded_centerline = np.pad(centerline, 1, mode='constant', constant_values=0)
        end_points = []
        # Iterate through centerline
        for y in range(1, padded_centerline.shape[0] - 1):
            for x in range(1, padded_centerline.shape[1] - 1):
                if padded_centerline[y, x]:  # If current pixel is part of the centerline
                    # Count the number of 8-connected neighbors
                    neighborhood = padded_centerline[y-1:y+2, x-1:x+2]
                    num_neighbors = np.sum(neighborhood) - 1  # Subtract 1 for the center pixel
                    if num_neighbors == 1:
                        # If only one neighbor, it's an end point
                        end_points.append((y-1, x-1))  # Adjust for the padding
        return end_points

    def plot_centerline(annual_data):
        years = len(annual_data)
        MAX_DISTANCE_BRANCH_REMOVAL = 100
        years_to_plot = range(0, years, 5)
        fig, ax = plt.subplots(figsize=(20, 15))
        for i, year in enumerate(years_to_plot):
            river_mask = annual_data[year]
            river_mask.centerline = river_mask.prune_centerline(MAX_DISTANCE_BRANCH_REMOVAL)
            alpha = 0.6
            actual_year = river_mask.year
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Centerline Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')
        plt.show()

    def plot_centerline(annual_data):
        """
        Plot the centerline over time.

        Args:
            data (list): A list of River objects representing the river at different points in time.
        """
        years = len(annual_data)
        MAX_DISTANCE_BRANCH_REMOVAL = 100

        years_to_plot = range(0, years, 5)

        fig, ax = plt.subplots(figsize=(20, 15))

        # Plot each year's centerline
        for i, year in enumerate(years_to_plot):
            river_mask = annual_data[year]
            river_mask.centerline = river_mask.pruned_centerline(MAX_DISTANCE_BRANCH_REMOVAL)
            alpha = 0.6
            actual_year = river_mask.year

        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Centerline Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')

        #plt.savefig('river_centerline_evolution_cleaned.png', dpi=300)
        plt.show()


    def _extract_river_edges(binary_mask):
        """
        Extract the edges of the river from a binary mask.

        Args:
            binary_mask (np.ndarray): Binary mask of the river.

        Returns:
            np.ndarray: Binary mask of the river edges.
        """
        # Erode the binary mask to get the edges
        eroded_mask = binary_erosion(binary_mask)
        edges = binary_mask & ~eroded_mask
        return edges

    def _plot_edges(ax, edges, color, alpha, label):
        """
        Plot the edges of the river on a given axes.

        Args:
            ax (matplotlib.axes.Axes): The axes on which to plot the edges.
            edges (np.ndarray): Binary mask of the river edges.
            color (str): The color to use for the edges.
            alpha (float): The transparency level of the edges.
            label (str): The label for the edges in the legend.
        """
        y, x = np.where(edges)
        ax.scatter(x, y, color=color, alpha=alpha, s=6, label=label, edgecolors='none')


    def plot_river_edges(data):
        """
        Plot the edges of the river over time.

        Args:
            data (list): A list of River objects representing the river at different points in time.
        """
        years = len(data)

        threshold = 150

        years_to_plot = range(0, years, 5)

        fig, ax = plt.subplots(figsize=(20, 15))

        colors = plt.cm.Spectral(np.linspace(0, 1, len(years_to_plot)))

        # Plot each year's river edges
        for i, year in enumerate(years_to_plot):
            river_mask = data[year]
            edges = river_mask._extract_river_edges()
            color = colors[i]
            alpha = 0.6

            actual_year = river_mask.year

            river_mask._plot_edges(ax, edges, color, alpha, label=str(actual_year))

        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Edge Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')

        #plt.savefig('river_edge_evolution_cleaned.png', dpi=300)
        plt.show()

    def plot_self(self):
        """
        Plot the river mask and edges.
        """
        # Plot the mask
        fig, ax = plt.subplots(figsize=(12, 8))
        # Plot the mask with a colormap that represents water
        ax.imshow(self.mask, cmap='Blues', interpolation='none', alpha=0.7)
        ax.imshow(self.edges, cmap='Greens', interpolation='none', alpha=0.5)
        plt.title('Athabasca River Mask ' + str(self.year))
        plt.show()

    def plot_river_migration(self, other):
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
      ax.set_title(f'River Migration: {self.year} Compared to {other.year}', pad=20, ha='center')
      plt.show()

    def quantify_erosion(annual_data):
        """
        Quantify the erosion of the river.
        #dem and pixel area
        Args:
            other (River): Another River object to compare with.
            dem (np.ndarray): Digital Elevation Model.
            pixel_area (float): Area of a pixel.
        """
        erosion_data = []
        years = [int(river.year) for river in annual_data]
        for i in range(1, len(annual_data)):
            erosion = (annual_data[i].mask.astype(int) - annual_data[i-1].mask.astype(int)) > 0
            accretion = (annual_data[i].mask.astype(int) - annual_data[i-1].mask.astype(int)) > 0
            # Calculate the area of erosion and accretion
            annual_data[i].erosion = np.sum(erosion * (30**2)) / 1000000
            annual_data[i].accretion = np.sum(accretion * (30**2)) / 1000000

            # Calculate the volume of erosion and accretion
            #annual_data[i].erosion_volume = np.sum(erosion * dem * (pixel_area**2)) / 1000000
            #annual_data[i].accretion_volume = np.sum(accretion * dem * (pixel_area**2)) / 1000000


    def plot_erosion(annual_data):
        """
        Plot erosion over time and accumulated erosion over time.

        Args:
        Annual Data (list): A list of River objects representing the river at different points in time.
        """
        # Sort the annual_data list by year
        annual_data.sort(key=lambda river: int(river.year))

        erosion_data = []
        years = [int(river.year) for river in annual_data]
        for i in range(1, len(annual_data)):
            erosion_data.append(annual_data[i].erosion)

        # Calculate the accumulated erosion
        accumulated_erosion = np.cumsum(erosion_data)

        # Calculate the average erosion rate
        average_erosion_rate = accumulated_erosion / (len(years) - 1)

        print(f"Average erosion rate: {average_erosion_rate} km2/year")

        # Plot the erosion data over time
        plt.figure(figsize=(10, 5))
        plt.plot(years[1:], erosion_data, marker='o', linestyle='-', color='red', label='Yearly Erosion (km2)')
        plt.plot(years[1:], accumulated_erosion, marker='o', linestyle='-', color='blue', label='Accumulated Erosion (km2)')
        plt.title('Annual and Accumulated Erosion Over Time')
        plt.xlabel('Year')
        plt.ylabel('Erosion (km2)')
        plt.grid(True)
        plt.legend()
        plt.show()

