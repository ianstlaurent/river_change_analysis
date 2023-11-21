import ee

def authenticate_gee():
    ee.Authenticate()
    ee.Initialize()

def define_roi(polygon):
    if polygon:  # This will be False if polygon is an empty list
        roi = ee.Geometry.Polygon(polygon)
    else:
        roi = ee.Geometry.Polygon([
            [-109.92484982890903,57.52552656456479],
            [-109.92484982890903,59.16266725855286],
            [-112.99003537578403,59.16266725855286],
            [-112.99003537578403,57.52552656456479]
        ])
    return roi
# Define functions for classification
def Ndvi(image):
    ndvi = image.normalizedDifference(['Nir', 'Red']).rename('ndvi')
    return ndvi

def Lswi(image):
    lswi = image.normalizedDifference(['Nir', 'Swir1']).rename('lswi')
    return lswi

def Mndwi(image):
    mndwi = image.normalizedDifference(['Green', 'Swir1']).rename('mndwi')
    return mndwi

def Evi(image):
    evi = image.expression('2.5 * (Nir - Red) / (1 + Nir + 6 * Red - 7.5 * Blue)', {
        'Nir': image.select(['Nir']),
        'Red': image.select(['Red']),
        'Blue': image.select(['Blue'])
        })
    return evi.rename(['evi'])

def process_images(start_year, end_year, roi, folder_name, file_name):
    mndwi_param = -0.40
    ndvi_param = 0.20
    cleaning_pixels = 100

    # Band namesg
    bn8 = ['B1', 'B2', 'B3', 'B4', 'B6', 'pixel_qa', 'B5', 'B7']
    bn7 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bn5 = ['B1', 'B1', 'B2', 'B3', 'B5', 'pixel_qa', 'B4', 'B7']
    bns = ['uBlue', 'Blue', 'Green', 'Red', 'Swir1', 'BQA', 'Nir', 'Swir2']

    # Image collections
    ls5 = ee.ImageCollection("LANDSAT/LT05/C01/T1_SR").filterDate('1985-04-01', '1999-04-15').select(bn5, bns)
    ls7 = ee.ImageCollection("LANDSAT/LE07/C01/T1_SR").select(bn7, bns)
    ls8 = ee.ImageCollection("LANDSAT/LC08/C01/T1_SR").select(bn8, bns)
    merged = ls5.merge(ls7).merge(ls8)

    for year in range(start_year, end_year+1):
        sDate_T1 = str(year) + '-06-01'
        eDate_T1 = str(year) + '-10-10'

        # Filter date range, roi and apply simple cloud processing:
        def mask_clouds(image):
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

        # Define outputs:
        Wetted_channel = waterMasked_p50
        Alluvial_deposits = activebeltMasked_p50
        Active_channel_binary_mask = noise_removal_p50_Masked

        filename = "River_Binary_Mask_" + str(year)
        task = ee.batch.Export.image.toDrive(
            image = Active_channel_binary_mask,
            description = filename,
            fileNamePrefix = file_name + str(year),
            region = roi.getInfo()['coordinates'],
            scale = 30,
            fileFormat = 'GeoTIFF',
            folder = folder_name,
            maxPixels = 1e12
        )
        task.start()
