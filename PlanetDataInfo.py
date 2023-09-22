import json
import ee
import geopandas as gpd
import pandas as pd
from shapely.geometry import shape
import numpy as np
import os
import requests
from requests.auth import HTTPBasicAuth


def GetDataAvailability(apiKey, geom, startDate, endDate):
    # the geo json geometry object we got from geojson.io
    geo_json_geometry = geom

    # filter for items the overlap with our chosen geometry
    geometry_filter = {
    "type": "GeometryFilter",
    "field_name": "geometry",
    "config": geo_json_geometry
    }

    # filter images acquired in a certain date range
    date_range_filter = {
    "type": "DateRangeFilter",
    "field_name": "acquired",
    "config": {
        "gte": startDate + "T00:00:00.000Z",
        "lte": endDate + "T00:00:00.000Z"
    }
    }

    filter = {
    "type": "AndFilter",
    "config": [geometry_filter, date_range_filter]
    }

    search_endpoint_request = {
    "item_types": ["PSScene"],
    "filter": filter
    }

    result = requests.post(
        'https://api.planet.com/data/v1/quick-search',
        auth=HTTPBasicAuth(apiKey, ''),
        json=search_endpoint_request)
    
    requestJson = json.loads(result.text)

    dateTimes = [item['properties']['acquired'] for item in requestJson['features']]

    dates = [item['properties']['acquired'].split('T')[0] for item in requestJson['features']]
    cloudCover = [item['properties']['cloud_cover'] for item in requestJson['features']]
    satelliteID = [item['properties']['satellite_id'] for item in requestJson['features']]
    # eps = [item['properties']['epsg_code'] for item in requestJson['features']]
    geomShape = shape(geom)
    geometries = [shape(item['geometry']) for item in requestJson['features']]
    intersectionGeom = [geomShape.intersection(geom) for geom in geometries]
    intersectionArea = [geom.area / geomShape.area for geom in intersectionGeom]
    df = gpd.GeoDataFrame(geometry=intersectionGeom)
    df['Date'] = dates
    df['DateTime'] = dateTimes
    df['cloudCover'] = cloudCover
    df['IntersectionArea'] = intersectionArea
    df['SatelliteID'] = satelliteID
    df = df.set_crs("EPSG:32646")

    def getWeightedMean(subDf):
        return np.sum(subDf.cloudCover.values * subDf.IntersectionArea.values) / np.sum(subDf.IntersectionArea.values)

    groupedDF0 = pd.DataFrame(df.groupby(['Date','SatelliteID']).apply(lambda x: getWeightedMean(x)))
    groupedDF1 = pd.DataFrame(df.groupby(['Date','SatelliteID']).apply(lambda x: gpd.GeoDataFrame(x['geometry']).dissolve()))

    groupedDF1['IntersectionArea'] = [geomShape.intersection(groupedDF1.iloc[geom_i,:].geometry).area / geomShape.area for geom_i in range(len(groupedDF1))]
    groupedDF1['cloudCover'] = groupedDF0.values

    df = pd.DataFrame(groupedDF1.groupby(['Date']).apply(lambda x: getWeightedMean(x)))

    planetOverlap = pd.DataFrame()
    planetOverlap['Date'] = df.reset_index().Date
    planetOverlap['Overlap'] = [geom.intersection(geomShape).area / geomShape.area for geom in groupedDF1.groupby(['Date']).apply(lambda x: gpd.GeoDataFrame(x['geometry']).dissolve()).geometry]
    planetOverlap['CloudCover'] = df.values

    return planetOverlap