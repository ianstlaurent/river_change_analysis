#Python Script to download DEMs from Google Earth Engine
import ee

srtm = ee.Image('USGS/SRTMGL1_003')

class dem:
    def __init__(roi):
        self.roi = roi
        self.dem = None
        self.elevation = None
        self.slope = None

    def process(self):
        self.dem = srtm.clip(self.roi)
        self.elevation = dem.select('elevation')
        self.slope = ee.Terrain.slope(elevation)












