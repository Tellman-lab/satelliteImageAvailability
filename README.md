# satelliteImageAvailability
GitHub respository containing short code to create a graphic of available satellite images for a given region (ROI) and time period (TOI). Graphic includes estimates of % of ROI area covered, and % cloud cover in the ROI. 

### WORKING! STILL NEED TO ADD:
* __Check Planet API__
* __Merge MODIS Aqua and Terra__
* __Add VIIRS__


**NOTE:** availability return for Planet data does not consistently work in current version. Users are encouraged to manually extract the Planet image dates, with ROI area and cloud cover estimates from Planet Explorer. An option is provided in the script to provide link to a csv file containing the manually extracted Planet information.

Social Pixel Lab

Alex Saunders, Jonathan Giezendanner

September 2023

Instructions for use:

* Run the file *createImageAvailabilityGraphic.ipynb*
    * Specify the region of interest - easiest done as a shapefile in GEE assets
    * Specify the time period of interest - option to use either a central date with a time window, or manually define start and end date
    * Note that multiple regions and multiple time periods can be run in one go - code will create multiple figures (one for each ROI and TOI)
    
* Helper codes are in *ImageAvailabilityInfos.py*, *ImageAvailabilityVisualisation.py* and *PlanetDataInfo.py*
    * Graph visualization is optimized for approx 20-30 day time windows, matplotlib parameters may need to be modified if creating graphs for shorter or longer time windows - this can be done in ImageAvailabilityVisualisation.py
