#Python Script to download DEMs from Google Earth Engine
import ee
import folium
srtm = ee.Image('USGS/SRTMGL1_003')

class dem:
    def __init__(self, roi):
        self.roi = roi
        self.dem = None
        self.elevation = None
        self.slope = None

    def process(self):
        self.dem = srtm.clip(self.roi)
        self.elevation = self.dem.select('elevation')
        self.slope = ee.Terrain.slope(self.elevation)

    def export(self, image, description, filename):
        task = ee.batch.Export.image.toDrive(
            image=image,
            description=description,
            folder='your_folder_name',
            fileNamePrefix=filename,
            scale=30,
            region=self.roi.getInfo()['coordinates'],
            fileFormat='GeoTIFF'
        )
        task.start()












