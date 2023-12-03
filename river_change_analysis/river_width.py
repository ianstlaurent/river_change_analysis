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
            # Step 1: Distance transform
            distance = distance_transform_edt(self.mask)

            # Step 2: Gradient
            gradient = gaussian_gradient_magnitude(distance, sigma=1)

            # Threshold the gradient
            thresh = threshold_otsu(gradient)
            binary = gradient > thresh

            # Step 3: Skeletonize to get raw centerline
            centerline_raw = skeletonize(binary)

            # Prune the centerline to remove spurious branches
            self.centerline = thin(centerline_raw, max_iter=500)  # Adjust max_iter as needed


    def extract_river_edges(binary_mask):
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

    def plot_river_edges(ax, edges, color, alpha, label):
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


    def plot_river_migration(data):
        """
        Plot the migration of the river over time.

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
            edges = river_mask.extract_river_edges(river_mask)
            color = colors[i]
            alpha = 0.6

            actual_year = river_mask.year

            river_mask.plot_river_edges(ax, edges, color, alpha, label=str(actual_year))

        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Edge Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')

        #plt.savefig('river_edge_evolution_cleaned.png', dpi=300)
        plt.show()

    def plot(self):
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
      ax.set_title(f'River Migration: {self.year} Compared to {other.year}', pad=20, ha='center')
      plt.show()

    def quantify_migration(self, other, dem, pixel_area):
        """
        Quantify the migration of the river.

        Args:
            other (River): Another River object to compare with.
            dem (np.ndarray): Digital Elevation Model.
            pixel_area (float): Area of a pixel.
        """
        erosion = (self.mask.astype(int) - other.mask.astype(int)) > 0
        accretion = (other.mask.astype(int) - self.mask.astype(int)) > 0

        # Calculate the area of erosion and accretion
        self.erosion = np.sum(erosion * (pixel_area**2)) / 1000000
        self.accretion = np.sum(accretion * (pixel_area**2)) / 1000000

        # Calculate the volume of erosion and accretion
        self.erosion_volume = np.sum(erosion * dem * (pixel_area**2)) / 1000000
        self.accretion_volume = np.sum(accretion * dem * (pixel_area**2)) / 1000000
