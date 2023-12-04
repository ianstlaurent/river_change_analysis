# This script defines a River class for analyzing and visualizing river data.
# Author: Ian St. Laurent
import os
import numpy as np
import rasterio
import cv2
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from shapely.geometry import LineString
from scipy.ndimage import distance_transform_edt, gaussian_gradient_magnitude, binary_erosion
from skimage.morphology import skeletonize, thin, remove_small_objects
from skimage.filters import sobel, threshold_otsu
from skimage import measure, morphology
from matplotlib.animation import FuncAnimation

MAX_DISTANCE_BRANCH_REMOVAL = 100
WATER_MASK_MIN_SIZE = 1000

class River:
    DEM = None
    SLOPE = None
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
        self.erosion = None
        self.accretion = None

    def load_mask(self):
        """
        Process the river mask geotiff file and store it as a mask in the River object and stores the year.
        Args:
            self (River): A River object.
        Returns:
            None. Modifies the River object mask and year.
        """
        with rasterio.open(self.file_path) as dataset:
            self.mask = dataset.read(1)
            self.year = self.file_path[-8:-4]

    @classmethod
    def load_dem(cls, dem_files):
        """
        Process the dem geotiff file and store the dem and slope
        Args:
            dem_files (list): A list of dem files.
        Returns:
            None. Modifies the dem and slope.
        """
        if dem_files is None:
            print("No files provided")
        for file in dem_files:
            if 'slope' in file or 'SLOPE' in file or 'Slope' in file:
                slope = file
            elif 'dem' in file or 'Dem' in file or 'DEM' in file:
                dem = file
        if slope is not None:
            with rasterio.open(slope) as src:
                SLOPE = src.read(1)
        if dem is not None:
            with rasterio.open(dem) as src:
                DEM  = src.read(1)
        # Cut out the non-river areas
        mask = DEM != 0
        cls.DEM = np.where(mask, DEM, np.nan)
        cls.SLOPE = np.where(mask, SLOPE, np.nan)

    @classmethod
    def plot_dem(cls):
        """
        Plot the dem and slope.
        Args:
            None
        Returns:
            Plotted dem and slope.
        """
        if cls.DEM is None:
            print("No DEM")
        if cls.SLOPE is None:
            print("No Slope")
        # Plot DEM
        plt.figure(figsize=(10, 10))
        img = plt.imshow(cls.DEM, cmap='terrain', interpolation='nearest', aspect='auto')
        plt.colorbar(img, label='Elevation (meters)')
        plt.title('SRTM 30m DEM')
        plt.show()

        # Plot Slope
        plt.figure(figsize=(10, 10))
        img = plt.imshow(cls.SLOPE, cmap='terrain', interpolation='nearest', aspect='auto')
        plt.colorbar(img, label='Slope (Degrees)')
        plt.title('SRTM 30m Slope')
        plt.show()

    def water_mask_process(annual_data, min_size):
        """
        Processes the water mask to fill in small holes and remove small bars.
        Args:
            annual_data (River or list of River): The river data to process.
            min_size (int): Minimum size of a bar to be removed.
        Returns:
            None. Modifies the River objects in place.
        """
        if isinstance(annual_data, list):
            for river_mask in annual_data:
                # Fill small holes in binary mask
                kernel = np.ones((5,5),np.uint8)
                watermask = cv2.morphologyEx(river_mask.mask, cv2.MORPH_CLOSE, kernel)
                if min_size is None or min_size <= 0:
                    min_size = WATER_MASK_MIN_SIZE
                # Identify small bars and fill them in to create a filled water mask.
                labels = measure.label(watermask == 0)
                for region in measure.regionprops(labels):
                    if region.area < min_size:
                        watermask[labels == region.label] = 1
                river_mask.watermask = watermask
        else:
            river_mask = annual_data
            # Fill small holes in binary mask
            kernel = np.ones((5,5),np.uint8)
            watermask = cv2.morphologyEx(river_mask.mask, cv2.MORPH_CLOSE, kernel)
            if min_size is None or min_size <= 0:
                min_size = WATER_MASK_MIN_SIZE
            # Identify small bars and fill them in to create a filled water mask.
            labels = measure.label(watermask == 0)
            for region in measure.regionprops(labels):
                if region.area < min_size:
                    watermask[labels == region.label] = 1
            river_mask.watermask = watermask

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

    def _prune_centerline(self, max_distance):
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
            if max_distance_branch_removal is None or max_distance_branch_removal <= 0:
                max_distance_branch_removal = MAX_DISTANCE_BRANCH_REMOVAL
            river_mask._prune_centerline(max_distance_branch_removal)

    def plot_centerline(annual_data):
        """
        Plot the centerline over time.
        Args:
            data (list): A list of River objects representing the river at different points in time.
        Returns:
            Plotted centerline of the river over time.
        """
        fig, ax = plt.subplots(figsize=(30, 20), dpi=500)
        ax.set_facecolor('black')
        years_to_plot = range(0, len(annual_data), 5)
        colors = plt.cm.Spectral(np.linspace(0, 1, len(years_to_plot)))
        legend_elements = []
        for i, year in enumerate(years_to_plot):
            river = annual_data[year]
            y, x = np.where(river.centerline)
            ax.scatter(x, y, color=colors[i], alpha=0.9, s=1.5, edgecolors='none')
            legend_elements.append(Line2D([0], [0], marker='o', color='w', label=str(river.year),
                                            markerfacecolor=colors[i], markersize=10))
        ax.set_ylim(ax.get_ylim()[::-1])
        ax.set_title('River Centerline Evolution Over Time')
        ax.legend(handles=legend_elements, loc='best')
        ax.set_xlabel('X Coordinate')
        ax.set_ylabel('Y Coordinate')
        ax.set_aspect('equal')
        plt.show()

    def _extract_river_edges(self):
        """
        Extract the edges of the river from a binary mask.
        Args:
            self (River Object).
        Returns:
            np.ndarray: Binary mask of the river edges.
        """
        # Erode the binary mask to get the edges
        eroded_mask = binary_erosion(self.mask)
        edges = self.mask & ~eroded_mask
        return edges

    def _plot_edges(self, ax, edges, color, alpha, label):
        """
        Plot the edges of the river, islands, and sandbars.
        Args:
            ax (matplotlib.axes.Axes): The axes on which to plot the edges.
            edges (np.ndarray): Binary mask of the river edges.
            color (str): The color to use for the edges.
            alpha (float): The transparency level of the edges.
            label (str): The label for the edges in the legend.
        Returns:
            Plot of the edges of the river
        """
        y, x = np.where(edges)
        ax.scatter(x, y, color=color, alpha=alpha, s=6, label=label, edgecolors='none')

    def plot_river_edges(annual_data):
        """
        Plot the edges of the river over time.
        Args:
            annual_data (list): A list of River objects representing the river at different points in time.
        Returns:
            Plotted edges of the river over time.
        """
        years_to_plot = range(0, len(annual_data), 5)
        fig, ax = plt.subplots(figsize=(20, 15))
        colors = plt.cm.Spectral(np.linspace(0, 1, len(years_to_plot)))

        # Plot each year's river edges
        for i, year in enumerate(years_to_plot):
            river_mask = annual_data[year]
            edges = river_mask._extract_river_edges()
            river_mask._plot_edges(ax, edges, colors[i], 0.6, str(river_mask.year))

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
        if folder_file_path is None:
            folder_file_path = os.getcwd()
            folder_file_path = folder_file_path + 'river_centerline_evolution.mp4'
        anim.save(folder_file_path, writer='ffmpeg')

    @classmethod
    def quantify_erosion(cls, annual_data):
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
            accretion = (annual_data[i-1].watermask.astype(int) - annual_data[i].watermask.astype(int)) > 0
            # Calculate the area of erosion and accretion
            annual_data[i].erosion = np.sum(erosion * (30**2)) / 1000000
            annual_data[i].accretion = np.sum(accretion * (30**2)) / 1000000

            # Calculate the volume of erosion and accretion
            if cls.DEM is not None:
                erosion_elevation = cls.DEM[erosion]
                accretion_elevation = cls.DEM[accretion]
                plt.figure(figsize=(10, 5))
                plt.scatter(range(len(erosion_elevation)), erosion_elevation, color='r', label='Erosion')
                plt.scatter(range(len(accretion_elevation)), accretion_elevation, color='b', label='Accretion')
                plt.title('Elevation at Locations of Erosion and Accretion')
                plt.xlabel('Location')
                plt.ylabel('Elevation')
                plt.legend()
                plt.show()


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
        accretion_data = []
        accumulated_erosion_data = []
        accumulated_accretion_data = []
        accumulated_erosion_sum = 0
        accumulated_accretion_sum = 0

        years = [int(river.year) for river in annual_data]
        for i in range(1, len(annual_data)):
            erosion_data.append(annual_data[i].erosion)
            accumulated_erosion_sum += annual_data[i].erosion
            accumulated_erosion_data.append(accumulated_erosion_sum)
            accretion_data.append(annual_data[i].accretion)
            accumulated_accretion_sum += annual_data[i].accretion
            accumulated_accretion_data.append(accumulated_accretion_sum)

        # Plot the erosion data over time
        average_erosion = accumulated_erosion_sum / (len(annual_data) - 1)
        print(f"Total Accumulated Erosion: {accumulated_erosion_sum} km2/year")
        print(f"Average Accumulated Erosion: {average_erosion} km2/year")
        plt.figure(figsize=(10, 5))
        plt.plot(years[1:], erosion_data, marker='o', linestyle='-', color='red', label='Yearly Erosion (km2)')
        plt.plot(years[1:], accumulated_erosion_data, marker='o', linestyle='-', color='blue', label='Accumulated Erosion (km2)')
        plt.title('Annual and Accumulated Erosion Over Time')
        plt.xlabel('Year')
        plt.ylabel('Erosion (km2)')
        plt.grid(True)
        plt.legend()
        plt.show()

        # Plot the accretion data over time
        average_accretion = accumulated_accretion_sum / (len(annual_data) - 1)
        print(f"Total Accumulated Accretion: {accumulated_accretion_sum} km2/year")
        print(f"Average Accumulated Accretion: {average_accretion} km2/year")
        plt.figure(figsize=(10, 5))
        plt.plot(years[1:], accretion_data, marker='o', linestyle='-', color='red', label='Yearly Accretion (km2)')
        plt.plot(years[1:], accumulated_accretion_data, marker='o', linestyle='-', color='blue', label='Accumulated Accretion (km2)')
        plt.title('Annual and Accumulated Accretion Over Time')
        plt.xlabel('Year')
        plt.ylabel('Accretion (km2)')
        plt.grid(True)
        plt.legend()
        plt.show()
