import ee
import pandas as pd
import numpy as np

import PlanetDataInfo
import importlib
importlib.reload(PlanetDataInfo)

def GetDataFrames(startDate, endDate, geometry, planetAPIKey, planetCSV=None):
    start_date = ee.Date(startDate)
    end_date = ee.Date(endDate)

    # modis_aqua = ee.ImageCollection("MODIS/061/MYD09GA")
    modis_terra = ee.ImageCollection("MODIS/061/MOD09GA")
    landsat7 = ee.ImageCollection("LANDSAT/LE07/C02/T1")
    landsat8 = ee.ImageCollection("LANDSAT/LC08/C02/T1")
    landsat9 = ee.ImageCollection("LANDSAT/LC09/C02/T1")
    sentinel2 = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
    sentinel1 = ee.ImageCollection("COPERNICUS/S1_GRD")

    sentinel2_collection = get_imagery_availability(sentinel2, 'S2', start_date, end_date, geometry, 'sentinel2', 20)
    sentinel1_collection = get_imagery_availability(sentinel1, 'S1', start_date, end_date, geometry, None, None)
    # modis_aqua_collection = get_imagery_availability(modis_aqua, 'MODIS', start_date, end_date, geometry, 'modis', 1000)
    modis_terra_collection = get_imagery_availability(modis_terra, 'MODIS', start_date, end_date, geometry, 'modis', 1000)
    landsat7_collection = get_imagery_availability(landsat7, 'L7', start_date, end_date, geometry, 'landsat', 30)
    landsat8_collection = get_imagery_availability(landsat8, 'L8', start_date, end_date, geometry, 'landsat', 30)
    landsat9_collection = get_imagery_availability(landsat9, 'L9', start_date, end_date, geometry, 'landsat', 30)

    date_list = pd.date_range(pd.to_datetime(start_date.getInfo()['value'], unit='ms'), pd.to_datetime(end_date.getInfo()['value'], unit='ms')).tolist()
    date_list_df = pd.DataFrame(data = [date_list], index = ['date']).T
    date_list_df['date'] = date_list_df['date'].dt.date

    sentinel2_df = create_imagery_info_df(sentinel2_collection)
    sentinel1_df = create_imagery_info_df(sentinel1_collection)
    # modis_aqua_df = create_imagery_info_df(modis_aqua_collection)
    modis_terra_df = create_imagery_info_df(modis_terra_collection)
    landsat7_df = create_imagery_info_df(landsat7_collection)
    landsat8_df = create_imagery_info_df(landsat8_collection)
    landsat9_df = create_imagery_info_df(landsat9_collection)

    if planetCSV==None:
        PlanetInfoDF = PlanetDataInfo.GetDataAvailability(planetAPIKey, geometry.getInfo(), startDate, endDate)
        PlanetInfoDF = PlanetInfoDF.rename(columns = {'Date':'date', 'Overlap':'pctArea', 'CloudCover':'pctCloud'})
        PlanetInfoDF = PlanetInfoDF.set_index('date')
        PlanetInfoDF['pctCloud'] = PlanetInfoDF['pctCloud']*100
        PlanetInfoDF['pctArea'] = PlanetInfoDF['pctArea']*100
    elif planetCSV!=None:
        PlanetInfoDF = pd.read_csv(planetCSV)
        PlanetInfoDF = PlanetInfoDF.set_index('date')
        
    return date_list_df, sentinel2_df, sentinel1_df, modis_terra_df, landsat7_df, landsat8_df, landsat9_df, PlanetInfoDF



def bitwiseExtract(value, fromBit, toBit):
    if (toBit == None): 
        toBit = fromBit
    maskSize = ee.Number(1).add(toBit).subtract(fromBit)
    mask = ee.Number(1).leftShift(maskSize).subtract(1)
    return value.rightShift(fromBit).bitwiseAnd(mask)

# Create function to add cloudy pixels for Sentinel-2 - NOTE: THIS ONE SIMPLY TAKES THE MEAN CLOUD PROBABILITY ACROSS THE IMAGE ROI
def add_clouds_s2(image):
    s2_qa_band = 'MSK_CLDPRB'
    cloudy = image.select(s2_qa_band).divide(100).rename('cloudy') #simply makes copy of the cloud probability layer (scaled to 0 to 1)
    return image.addBands(cloudy)

# Create function to add cloudy pixels for MODIS
def add_clouds_modis(image):
    modis_qa_band = 'state_1km'
    qa = image.select(modis_qa_band)
    clouds = (bitwiseExtract(qa, 0, 1).neq(0).And(bitwiseExtract(qa, 0, 1).neq(3)))
    cirrus = bitwiseExtract(qa, 8, 9).neq(0)
    cloudy = clouds.Or(cirrus).rename('cloudy') # this gives us cloudy pixels
    return image.addBands(cloudy)

# Create function to add cloudy pixels for Landsat
def add_clouds_landsat(image):
    landsat_qa_band = 'QA_PIXEL'
    qa = image.select(landsat_qa_band)
    clouds = bitwiseExtract(qa, 3, None).neq(0)
    dilated_clouds = bitwiseExtract(qa, 1, None).neq(0)
    cloudy = clouds.Or(dilated_clouds).rename('cloudy') # this gives us cloudy pixels
    return image.addBands(cloudy)

def mosaicBy(collection):

    # Return the collection as a list of images
    image_list = ee.ImageCollection(collection).toList(ee.ImageCollection(collection).size())

    # Get all the dates as list
    def get_date(image):
        date = ee.Image(image).date().format("YYYY-MM-dd")
        return date

    all_dates = image_list.map(get_date)

    # Get distinct dates
    dates_unique = all_dates.distinct()

    # Create mosaic of images on the same day
    def mosaic_day(day):

        # Split into components
        day1 = ee.String(day).split(" ")
        date1 = ee.Date(day1.get(0))

        # Filter with start date and date + 1 day, to an imageCollection
        imagecol = ee.ImageCollection(collection).filterDate(date1, date1.advance(1, "day"))

        # Mosaic the daily imageCollection - *** should this be specified to maximise the cloud-free pixels?
        image = imagecol.mosaic()

        # # Do a quality mosaic of the daily imageCollection
        # def quality_mosaic_prep(image):
        #   cldProb = image.select(sensor_mosaic_band)
        #   cldProbInv = cldProb.multiply(-1).rename('quality')
        #   return image.addBands(cldProbInv)
        #
        # imagecol = imagecol.map(quality_mosaic_prep)
        # image = imagecol.qualityMosaic(quality)

        # Perform a dissolve of the daily imageCollection geometries to get the mosaic image extent
        mosaic_geom = imagecol.geometry().dissolve()

        return ee.Image(image).set(
            "system:time_start", date1.millis(),
            "system:date", date1.format("YYYY-MM-dd"),
            "system:id", day1,
            'system:footprint', mosaic_geom); # preserve the geometry

    mosaic_image_list = ee.ImageCollection(dates_unique.map(mosaic_day))

    return mosaic_image_list

# 3) Create a function which combines functions to get info about the available imagery
def get_imagery_availability(collection, collectionName, start, end, roi, sensor_cloud_flag, sensor_cloud_scale):
    
    # 3.0) Filter the ImageCollection for the ROI and TOI
    filteredCollection = collection.filterDate(ee.Date(start), ee.Date(end)).filter(ee.Filter.bounds(roi))
    n = 0
    try:
        n = filteredCollection.size().getInfo()
    except:
        n = 0
    
    if n == 0: # stop the function if no images for the ROI and TOI
        print(collectionName, ': No images for the TOI and ROI')
        return
    
    # 3.1) Add cloud pixels to the image, if MODIS, S2 or Landsat
    if sensor_cloud_flag == 'modis':
        filteredCollection_wClouds = filteredCollection.map(add_clouds_modis)
    elif sensor_cloud_flag == 'sentinel2':
        filteredCollection_wClouds = filteredCollection.map(add_clouds_s2)
    elif sensor_cloud_flag == 'landsat':
        filteredCollection_wClouds = filteredCollection.map(add_clouds_landsat)
    else:
        filteredCollection_wClouds = filteredCollection
    
    
    # 3.2) Apply the mosaic function on the filteredCollection to mosaic images by day
    mosaicCollection = mosaicBy(filteredCollection_wClouds)
    
    
    # Convert the ROI to geometry and get its area, for performing the clip and intersection
    roi_geom = roi
    roi_area = roi_geom.area()
    
    # 3.3) Create a function to clip the image to the ROI, map to the collection
    def clip_to_roi(image):
        return image.clip(roi)

    
    # 3.3) Apply the clipping function on the fiteredCollection mosaic - NOT PERFORMED
    #mosaicCollectionClipped = mosaicCollection.map(clip_to_roi)
    mosaicCollectionClipped = mosaicCollection
    
   
    # 3.4) Create a function to compute the % of ROI area covered by the image, set as a new property
    def get_pct_area_intersect(image):
        image_geom = image.geometry()
        intersect = roi_geom.intersection(image_geom) #roi_geom.intersection(bbox, 1)
        intersect_area = intersect.area()#.getInfo()
        pct_area = intersect_area.divide(roi_area).multiply(100)#.getInfo()
        return image.set('PctArea', pct_area)
    
    # Apply the get area intersect function on the collection
    mosaicCollectionClipped_wArea = mosaicCollectionClipped.map(get_pct_area_intersect)

    
    # 3.5) Create a function to get the cloudiness of the image  and set it as a new property, only if optical imagery
    # Create function to reduce cloud values must be run inside the main function as uses roi and sensor_cloud_scale
    def reduce_clouds(image):
        pctCloud = (image.select('cloudy').reduceRegion(reducer = ee.Reducer.mean(), # taking the mean is same as taking the sum divided by the total pixels
                                                            geometry = roi_geom.intersection(image.geometry()), #roi_geom,
                                                            scale = sensor_cloud_scale,
                                                            bestEffort = True)) # sensor_cloud_scale: MODIS cloud mask resolution is 1 km // S2 is 60 m // Landsat is 30 m
        pctCloudVal = ee.Number(pctCloud.get('cloudy')).multiply(100)
        return image.set('PctCloud', pctCloudVal) # Add as a property
    
    def reduce_clouds_dummy(image):
        return image.set('PctCloud', 0) # Add as a property
    
    # Apply the reduce clouds function to get a single cloudiness value for the ROI
    if sensor_cloud_flag in ['modis', 'sentinel2', 'landsat']:
        mosaicCollectionClipped_wArea_wCloudInfo = mosaicCollectionClipped_wArea.map(reduce_clouds)
    else:
        mosaicCollectionClipped_wArea_wCloudInfo = mosaicCollectionClipped_wArea.map(reduce_clouds_dummy)
     
    # # Create a function to extract cloudiness data from a MODIS image
    # def get_cloudiness_modis(image):
    #   # Cloud state is in the low two bits of the 'state_1km' band
    #   cloudState = image.select('state_1km').bitwiseAnd(0x03)
    #   # 0 means clear, 1 means cloudy, 2 means mixed, and 3 means missing data, convert to the range 0.0-1.0 and mask out the missing pixels
    #   return cloudState.float().where(cloudState.eq(2), 0.5).updateMask(cloudState.neq(3))

    # Return the imageCollection, filtered to the ROI and TOI, mosaicded, with the useful info as new properties
    print(collectionName, ': Success in getting the FilteredCollection with image info')
    return mosaicCollectionClipped_wArea_wCloudInfo

# Create a function to extract the dates, % area of ROI and % cloudiness into a data frame
# And then convert to a time series of all dates between the start and end date, filled in with the relevant info where images are available and -1 where not
def create_imagery_info_df(collection):
    
    if collection == None:
        return pd.DataFrame()
    
    # Extract the info as separate numpy arrays
    dateTime = np.array(collection.aggregate_array('system:time_start').getInfo())
    pctArea = np.array(collection.aggregate_array('PctArea').getInfo())
    try:
        pctCloud = np.array(collection.aggregate_array('PctCloud').getInfo())
    except:
        pctCloud = np.ones(pctArea.shape) * 50.0
        
    # Create a pandas dataframe combining the arrays
    collection_df = pd.DataFrame(data = [dateTime, pctArea, pctCloud], index = ['dateTime', 'pctArea', 'pctCloud']).T
    
    # Convert the date format and add a simplified date column
    collection_df['dateTime'] = pd.to_datetime(collection_df['dateTime'], unit='ms')
    collection_df['date'] = collection_df['dateTime'].dt.date
    
    # Set the date as the index
    collection_df = collection_df.set_index('date')
    
    # # Merge the collection_info_df with the date_list to update values where there was available imagery
    # collection_df_full = pd.merge(date_list_df, collection_df, on='date', how='outer').set_index('date')

    # Return both the original and the full (time series) dataframes of info about the imagery
    return collection_df