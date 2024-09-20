import datetime
import numpy
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from Convert2GeopandasObject import Convert2GeopandasObject
from EarthAccessData import AccessEarthAccessData

AccessEarthAccessData = AccessEarthAccessData()
read_coordinates_from_polygon = AccessEarthAccessData.read_coordinates_from_polygon


def create_scene_filter(search_area):
    polygon = read_coordinates_from_polygon(Convert2GeopandasObject(search_area))
    AccessEarthAccessData.read_coordinates_from_polygon(Convert2GeopandasObject(search_area))
    spatialFilter = {'filterType': "mbr",
                     'lowerLeft': {'latitude': polygon[1][1], 'longitude': polygon[1][0]},
                     'upperRight': {'latitude': polygon[3][1], 'longitude': polygon[3][0]}}
    sceneFilter = {'cloudCoverFilter': {'min': 0, 'max': 20},
                   'spatialFilter': spatialFilter,
                   'temporalFilter': create_temporal_filter()}

    return sceneFilter, polygon


def create_temporal_filter():
    temporal_filter = {'start': '2024-08-01', 'end': datetime.datetime.now().strftime("%Y-%m-%d")}
    return temporal_filter




def filter_on_centroid(result_extents):
    """ find output that intersects center of polygon"""
    # https://stackoverflow.com/questions/4355894/how-to-get-center-of-set-of-points-using-python
    # find centroid
    # parse_results(result_extents)
    search_polygon = create_scene_filter(r"C:\Users\cewil\Documents\GitHub\NDVICalculator\InputData\Shapefiles\Pocosin_FWS\Pocosin_FWS\Pocosin_FWS_AOI_WGS84.shp")[1]
    x,y=zip(*search_polygon)
    center=(max(x)+min(x))/2., (max(y)+min(y))/2.

    #check if center is inside results extent
    # https://stackoverflow.com/questions/36399381/whats-the-fastest-way-of-checking-if-a-point-is-inside-a-polygon-in-python
    point = Point(center)
    polygon_coordinates = result_extents['spatialBounds']['coordinates'][0]
    polygon_coordinate_pairs = []
    for x in tuple(polygon_coordinates):
        polygon_coordinate_pairs.append(tuple(x))
    polygon = Polygon(polygon_coordinate_pairs)
    point_inside_polygon = (polygon.contains(point))
    return point_inside_polygon
