#Python Script to download DEMs from Google Earth Engine
import ee

srtm = ee.Image('USGS/SRTMGL1_003')
class dem:
    def __init__(roi):
        dem = srtm.clip(roi)
        elevation = dem.select('elevation')
        slope = ee.Terrain.slope(elevation)












