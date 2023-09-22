# satelliteImageAvailability
GitHub respository containing short code to create a graphic of available satellite images for a given region and time period.

Social Pixel Lab

Alex Saunders, Jonathan Giezendanner

September 2023

Instructions for use:
* Run the file createImageAvailabilityGraphic.ipynb
    * Specify the region of interest - easiest done as a shapefile in GEE assets
    * Specify the time period of interest - option to use either a central date with a time window, or manually define start and end date
    * Note that multiple regions and multiple time periods can be run in one go - code will create multiple figures (one for each ROI and TOI)
* Helper codes are in ImageAvailabilityInfos.py, ImageAvailabilityVisualisation.py and PlanetDataInfo.py
    * Graph visualization is optimized for approx 20-30 day time windows, matplotlib parameters may need to be modified if creating graphs for shorter or longer time windows - this can be done in ImageAvailabilityVisualisation.py
