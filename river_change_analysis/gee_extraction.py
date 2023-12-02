# GEE River Binary Mask Extraction
# Modified from Example Work Flow in:
# Boothroyd, RJ, Williams, RD, Hoey, TB, Barrett, B, Prasojo, OA. Applications of Google Earth Engine
# in fluvial geomorphology for detecting river channel change. WIREs Water.
# 2021; 8:e21496. https://doi.org/10.1002/wat2.1496
# and

import ee
from skimage.morphology import thin
from skimage import filters, morphology
import numpy as np
from ee import Kernel
CLOUD_SHADOW_BIT_MASK = 1 << 3
CLOUDS_BIT_MASK = 1 << 5


ee.Authenticate()
ee.Initialize()

def define_roi(polygon):
    if polygon:  # This will be False if polygon is an empty list
        roi = ee.Geometry.Polygon(polygon)
    else:
        print("No region of interest provided. Using default ROI.")
        roi = ee.Geometry.Polygon([
            [-109.92484982890903,57.52552656456479],
            [-109.92484982890903,59.16266725855286],
            [-112.99003537578403,59.16266725855286],
            [-112.99003537578403,57.52552656456479]
        ])
    return roi

# Define functions for classification
def Ndvi(image):
    """Calculate the Normalized Difference Vegetation Index (NDVI) for an image."""
    return image.normalizedDifference(['Nir', 'Red']).rename('ndvi')

def Lswi(image):
    """Calculate the Land Surface Water Index (LSWI) for an image."""
    return image.normalizedDifference(['Nir', 'Swir1']).rename('lswi')

def Mndwi(image):
    """Calculate the Modified Normalized Difference Water Index (MNDWI) for an image."""
    return image.normalizedDifference(['Green', 'Swir1']).rename('mndwi')

def Evi(image):
    """Calculate the Enhanced Vegetation Index (EVI) for an image."""
    evi = image.expression('2.5 * (Nir - Red) / (1 + Nir + 6 * Red - 7.5 * Blue)', {
        'Nir': image.select(['Nir']),
        'Red': image.select(['Red']),
        'Blue': image.select(['Blue'])
    })
    return evi.rename(['evi'])

"""Import a Digital Elevation Model (DEM) from Google Earth Engine."""
def import_dem(roi, file_name_prefix, folder_name):
    dem = ee.Image('USGS/SRTMGL1_003').clip(roi)
    elevation = dem.select('elevation')
    slope = ee.Terrain.slope(elevation)
    task = ee.batch.Export.image.toDrive(
            image = dem,
            description = file_name_prefix + '_dem',
            fileNamePrefix = file_name_prefix + '_dem',
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
    )
    task.start()

    task1 = ee.batch.Export.image.toDrive(
            image = elevation,
            description = file_name_prefix + '_elevation',
            fileNamePrefix = file_name_prefix + '_elevation',
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
    )
    task1.start()

    task2 = ee.batch.Export.image.toDrive(
            image = slope,
            description = file_name_prefix + '_slope',
            fileNamePrefix = file_name_prefix + '_slope',
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
    )
    task2.start()


def process_images(start_year, end_year, month_day_start, month_day_end, roi, folder_name, file_name):

    if (start_year == None) | (end_year == None):
        raise ValueError("Please provide a start year and end year.")
    if (month_day_start == None) | (month_day_end == None):
        raise ValueError("Please provide a start date and end date.")
    if roi == None:
        raise ValueError("Please provide a region of interest.")
    if folder_name == None:
        raise ValueError("Please provide a folder name.")
    if file_name == None:
        raise ValueError("Please provide a file name.")

    # Parameters for water and active river belt classification
    mndwi_param = -0.40
    ndvi_param = 0.20
    cleaning_pixels = 100

    # Band names for different Landsat sensors
    bn8 = ['B1', 'B2', 'B3', 'B4', 'B6', 'pixel_qa', 'B5', 'B7']
    bn7 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bn5 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bns = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'BQA', 'Nir', 'Swir2']

    # Image collections for different Landsat sensors
    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").filterDate('1985-04-01', '1999-04-15').select(bn5, bns)
    ls7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR").select(bn7, bns)
    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns)
    merged = ls5.merge(ls7).merge(ls8)  # Merge all collections into one

    for year in range(start_year, end_year+1):
        sDate_T1 = str(year) + month_day_start  # Start date for filtering
        eDate_T1 = str(year) + month_day_end  # End date for filtering

        # Filter date range, roi and apply simple cloud processing:
        def mask_clouds(image):
            """Mask clouds and cloud shadows in an image."""
            cloudShadowBitMask = 1 << 3
            cloudsBitMask = 1 << 5
            qa = image.select('BQA')
            mask = qa.bitwiseAnd(cloudShadowBitMask).eq(0).And(qa.bitwiseAnd(cloudsBitMask).eq(0))
            return image.updateMask(mask).multiply(0.0001).clip(roi)

        imgCol = merged.filterDate(sDate_T1, eDate_T1).filterBounds(roi).map(mask_clouds)

        # Define and rename quantiles of interest:
        bnp50 = ['uBlue_p50', 'Blue_p50', 'Green_p50', 'Red_p50', 'Swir1_p50', 'BQA_p50', 'Nir_p50', 'Swir2_p50']
        p50 = imgCol.reduce(ee.Reducer.percentile([50])).select(bnp50, bns)

        # Apply to each percentile:
        mndwi_p50 = Mndwi(p50)
        ndvi_p50 = Ndvi(p50)
        evi_p50 = Evi(p50)
        lswi_p50 = Lswi(p50)

        # Water classification from (Zou 2018):
        water_p50 = mndwi_p50.gt(ndvi_p50).Or(mndwi_p50.gt(evi_p50)).And(evi_p50.lt(0.1))
        waterMasked_p50 = water_p50.updateMask(water_p50.gt(0))

        # Active river belt classification:
        activebelt_p50 = mndwi_p50.gte(mndwi_param).And(ndvi_p50.lte(ndvi_param))
        activebeltMasked_p50 = activebelt_p50.updateMask(activebelt_p50.gt(0))
        active_p50 = water_p50.Or(activebelt_p50)

        # Clean binary active channel:
        smooth_map_p50 = active_p50.focal_mode(radius=10, kernelType='octagon', units='pixels', iterations=1).mask(active_p50.gte(1))
        noise_removal_p50 = active_p50.updateMask(active_p50.connectedPixelCount(cleaning_pixels, False).gte(cleaning_pixels)).unmask(smooth_map_p50)
        noise_removal_p50_Masked = noise_removal_p50.updateMask(noise_removal_p50.gt(0))

        # Image closure operation to fill small holes.
        watermask = noise_removal_p50_Masked.focal_max().focal_min()
        #REMOVE NOISE AND SMALL ISLANDS TO SIMPLIFY THE TOPOLOGY.
        MIN_SIZE = 2E3
        barPolys = watermask.Not().selfMask() \
            .reduceToVectors(
                geometry=roi,
                scale=30,
                eightConnected=True,
                maxPixels=1e9
            ) \
            .filter(ee.Filter.lte('count', MIN_SIZE))
        filled = watermask.paint(barPolys, 1)
        Wetted_channel = watermask.updateMask(filled.Not())
        river_mask = watermask

        #Alluvial_deposits = activebeltMasked_p50

        filename = file_name + str(year)
        task = ee.batch.Export.image.toDrive(
            image = river_mask,
            description = filename,
            fileNamePrefix = file_name + str(year),
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
        )
        task.start()


        filename = file_name + str(year) + '_wetted_channel_'
        task = ee.batch.Export.image.toDrive(
            image = Wetted_channel,
            description = filename,
            fileNamePrefix = file_name + str(year),
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
        )
        task.start()



