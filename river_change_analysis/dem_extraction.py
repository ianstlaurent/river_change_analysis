#Python Script to download DEMs from Google Earth Engine
import ee

def retrieve_dem(roi):
    srtm = ee.Image('USGS/SRTMGL1_003')
    dem = srtm.clip(roi)

    return dem







