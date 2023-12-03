# This script defines a River class for analyzing and visualizing river data.
# Author: Ian St. Laurent
import os
import numpy as np
import rasterio
import cv2
import matplotlib.pyplot as plt
from shapely.geometry import LineString
from scipy.ndimage import distance_transform_edt, gaussian_gradient_magnitude, binary_erosion
from skimage.morphology import skeletonize, thin, remove_small_objects
from skimage.filters import sobel, threshold_otsu
from skimage import measure, morphology
from matplotlib.animation import FuncAnimation

MAX_DISTANCE_BRANCH_REMOVAL = 100
WATER_MASK_MIN_SIZE = 1000

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
        self.watermask = None
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
        Args:
            self (River): A River object.
        Returns:
            np.ndarray: Binary mask of the centerline.
        """
        # Load river mask
        with rasterio.open(self.file_path) as dataset:
            self.mask = dataset.read(1)
            self.year = self.file_path[-8:-4]

    def water_mask_process(annual_data, min_size):
        """
        Proceses the water mask to fill in small holes and remove small bars.
        Args:
            self (River) or annual_data list of River Objects.
            min_size (int): Minimum size of a bar to be removed.
        Returns:
            Creates a cleaned water mask and adds it to River object then plots it.
        """
        if annual_data is type(list):
            for i, data in enumerate(annual_data):
                river = annual_data[i]
                # Fill small holes in binary mask
                kernel = np.ones((5,5),np.uint8)
                watermask = cv2.morphologyEx(river.mask, cv2.MORPH_CLOSE, kernel)
                if min_size is None | min_size <= 0:
                        min_size = WATER_MASK_MIN_SIZE
                # Identify small bars and fill them in to create a filled water mask.
                labels = measure.label(watermask == 0)
                for region in measure.regionprops(labels):
                    if region.area < min_size:
                        watermask[labels == region.label] = 1
                river.watermask = watermask
        else:
            river = annual_data
            # Fill small holes in binary mask
            kernel = np.ones((5,5),np.uint8)
            watermask = cv2.morphologyEx(river.mask, cv2.MORPH_CLOSE, kernel)
            if min_size is None | min_size <= 0:
                    min_size = WATER_MASK_MIN_SIZE
            # Identify small bars and fill them in to create a filled water mask.
            labels = measure.label(watermask == 0)
            for region in measure.regionprops(labels):
                if region.area < min_size:
                    watermask[labels == region.label] = 1
            river.watermask = watermask

    def _find_end_points(self):
        '''
        Find the end points of a centerline.
        Args:
            centerline (np.ndarray): Binary mask of the centerline.
        Returns:
            list: A list of tuples containing the coordinates of the end points.
        '''
        # Create a padded version of the centerline to handle edge cases
        padded_centerline = np.pad(self.centerline, 1, mode='constant', constant_values=0)
        end_points = []
        # Iterate through centerline
        for y in range(1, padded_centerline.shape[0] - 1):
            for x in range(1, padded_centerline.shape[1] - 1):
                if padded_centerline[y, x]:
                    # Count the number of 8-connected neighbors
                    neighborhood = padded_centerline[y-1:y+2, x-1:x+2]
                    num_neighbors = np.sum(neighborhood) - 1
                    if num_neighbors == 1:
                        # If only one neighbor, it's an end point
                        end_points.append((y-1, x-1))
        return end_points

    def prune_centerline(self, max_distance):
        '''
        Prune the centerline by removing branches.
        Args:
            centerline (np.ndarray): Binary mask of the centerline.
            max_distance (int): The maximum distance to remove branches.
        Returns:
            Prunes centerline and adds it to River object.
        '''
        for _ in range(max_distance):
            # Find end points in the current centerline
            end_points = self._find_end_points()
            # If there are no end points, stop the loop
            if not end_points:
                break
            for end_point in end_points:
                # Set end point to 0 in the centerline
                self.centerline[end_point] = False

    def process_centerline(annual_data, max_distance_branch_removal):
        '''
        Process the centerline to remove branches.
        Args:
            centerline (np.ndarray): Binary mask of the centerline.
            max_distance_branch_removal (int): The maximum distance to remove branches.
        Returns:
            Prunes centerline and adds it to River object.
        '''
        for i, data in enumerate(annual_data):
            river_mask = annual_data[i]
            if river_mask.watermask is None:
                river_mask.water_mask_process(WATER_MASK_MIN_SIZE)
            river_mask.centerline = thin(river_mask.watermask)
            if max_distance_branch_removal is None | max_distance_branch_removal <= 0:
                max_distance_branch_removal = MAX_DISTANCE_BRANCH_REMOVAL
            river_mask.prune_centerline(max_distance_branch_removal)

    def plot_centerline(annual_data):
        """
        Plot the centerline over time.
        Args:
            data (list): A list of River objects representing the river at different points in time.
        Returns:
            Plotted centerline of the river over time.
        """
        years_to_plot = range(0, len(annual_data), 5)
        fig, ax = plt.subplots(figsize=(20, 15))
        colors = plt.cm.Spectral(np.linspace(0, 1, len(years_to_plot)))
        for i, year in enumerate(years_to_plot):
            river_mask = annual_data[year]
            if river_mask.watermask is None | river_mask.centerline is None:
                river_mask.water_mask_process(WATER_MASK_MIN_SIZE)
                river_mask.centerline = thin(river_mask.watermask)
                river_mask.prune_centerline(MAX_DISTANCE_BRANCH_REMOVAL)
            ax.plot(river_mask.centerline, color=colors[i], alpha=0.6, label=str(river_mask.year))
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Centerline Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')
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
        Returns:
            Plot of the edges of the river on a given axes.
        """
        y, x = np.where(edges)
        ax.scatter(x, y, color=color, alpha=alpha, s=6, label=label, edgecolors='none')

    def plot_river_edges(data):
        """
        Plot the edges of the river over time.
        Args:
            data (list): A list of River objects representing the river at different points in time.
        Returns:
            Plotted edges of the river over time.
        """
        years_to_plot = range(0, len(data), 5)
        fig, ax = plt.subplots(figsize=(20, 15))
        colors = plt.cm.Spectral(np.linspace(0, 1, len(years_to_plot)))

        # Plot each year's river edges
        for i, year in enumerate(years_to_plot):
            river_mask = data[year]
            edges = river_mask._extract_river_edges()
            river_mask._plot_edges(ax, edges, colors[i], 0.6, label=str(river_mask.year))

        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Edge Evolution Over 30 Years')
        ax.legend(loc='best', fontsize='x-small')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')
        plt.show()

    def plot_self(self):
        """
        Plot the river mask and edges.
        Args:
            self (River): A River object.
        Returns:
            Plotted river mask.
        """
        # Plot the mask
        fig, ax = plt.subplots(figsize=(12, 8))
        # Plot the mask with a colormap that represents water
        ax.imshow(self.mask, cmap='Blues', interpolation='none', alpha=0.7)
        plt.title('Athabasca River Mask' + str(self.year))
        plt.show()
        if self.watermask is None:
            self.water_mask_process(WATER_MASK_MIN_SIZE)
        fig, ax = plt.subplots(figsize=(12, 8))
        # Plot the mask with a colormap that represents water
        ax.imshow(self.watermask, cmap='Blues', interpolation='none', alpha=0.7)
        plt.title('Athabasca Filled River Mask' + str(self.year))
        plt.show()

    def plot_river_migration(self, other):
        """
        Plot the migration of the river.
        Args:
            self (River): A River object.
            other (River): Another River object to compare with.
        Returns:
            Plotted river migration.
        """
        # Calculate the migration
        migration = self.mask.astype(int) - other.mask.astype(int)
        # Plot the migration
        # Positive values (areas that are only in the current year's mask) in red
        # Negative values (areas that are only in the other year's mask) in blue
        fig, ax = plt.subplots(figsize=(20, 10))
        cmap = plt.get_cmap('bwr')
        im = ax.imshow(migration, cmap=cmap, vmin=-1, vmax=1)

        # Create an axes for colorbar.
        cax = fig.add_axes([ax.get_position().x1 + 0.01, ax.get_position().y0, 0.02, ax.get_position().height])
        colorbar = plt.colorbar(im, cax=cax)
        colorbar.set_label('Erosion (Red) and Accretion (Blue)', rotation=270, labelpad=15)

        # Set the title to be in the center
        ax.set_title(f'River Migration: {self.year} Compared to {other.year}', pad=20, ha='center')
        plt.show()

    def animate_centerline_migration(annual_data, folder_file_path):
        '''
        Animate the centerline migration over time.
        Args:
            data (list): A list of River objects representing the river at different points in time.
            folder_file_path (str): Path to the folder where the animation will be stored with name of file and .mp4.
        Returns:
            Animated centerline migration over time.
        '''
        fig, ax = plt.subplots(figsize=(30, 50))
        ax.set_title('Athabasca River (Reach 1) Centerline Migration 1986-2021')
        im = ax.imshow(annual_data[0].centerline, cmap='gray')
        def init():
            return [im]
        def animate(i):
            im.set_data(annual_data[i].centerline)
            return [im]
        # Create the animation
        anim = FuncAnimation(fig, animate, init_func=init, frames=len(annual_data), interval=1000)
        plt.show()
        if folder_path is None:
            folder_path = os.getcwd()
            folder_path = folder_path + 'river_centerline_evolution.mp4'
        anim.save(folder_path, writer='ffmpeg')

    def quantify_erosion(annual_data):
        """
        Quantify the erosion of the river.
        Args:
            annual_data (list): A list of River objects representing the river at different points in time.
        Returns:
            Erosion and accretion of the river.
        """
        for i in range(1, len(annual_data)):
            if annual_data[i].watermask is None:
                annual_data[i].water_mask_process(WATER_MASK_MIN_SIZE)
            erosion = (annual_data[i].watermask.astype(int) - annual_data[i-1].watermask.astype(int)) > 0
            accretion = (annual_data[i].watermask.astype(int) - annual_data[i-1].watermask.astype(int)) > 0
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
        Returns:
            Plotted erosion over time and accumulated erosion over time.
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

