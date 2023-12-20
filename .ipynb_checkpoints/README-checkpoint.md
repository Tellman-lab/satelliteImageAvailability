# satelliteImageAvailability
GitHub respository containing short code to create a graphic of available satellite images for a given region (ROI) and time period (TOI). Graphic includes estimates of % of ROI area covered, and % cloud cover in the ROI. 

### WORKING! FIXES / IMPROVEMENTS THAT NEED TO BE ADDED:
* __Check Planet API__
    * We understand this issue is because the Planet API can only retain the first X (around 250) number of scenes. So if the region and / or the time period are large, many scenes will be returned, as a result some image dates will be lost.
* __Merge MODIS Aqua and Terra__
    * I.e. use MODIS AQUA and TERRA, create composite with least cloudy pixel from either AQUA and TERRA, then do reduce region on that.
* __Add VIIRS__
* __Separate graph, one with Aqua/Terra and Landsats (7, 8, 9) separated__
    * Currently, we group Landsats together.

**NOTE:** for the reason mentioned above, availability return for Planet data does not consistently work in current version. Users are encouraged to manually extract the Planet image dates, with ROI area and cloud cover estimates from Planet Explorer. An option is provided in the script to provide link to a csv file containing the manually extracted Planet information.

Social Pixel Lab

Alex Saunders, Jonathan Giezendanner

September 2023

__Instructions for use:__

* Run the file *createImageAvailabilityGraphic.ipynb*
    * Specify the region of interest - easiest done as a shapefile in GEE assets
    * Specify the time period of interest - option to use either a central date with a time window, or manually define start and end date
    * Note that multiple regions and multiple time periods can be run in one go - code will create multiple figures (one for each ROI and TOI)
    
* Helper codes are in *ImageAvailabilityInfos.py*, *ImageAvailabilityVisualisation.py* and *PlanetDataInfo.py*
    * Graph visualization is optimized for approx 20-30 day time windows, matplotlib parameters may need to be modified if creating graphs for shorter or longer time windows - this can be done in ImageAvailabilityVisualisation.py
