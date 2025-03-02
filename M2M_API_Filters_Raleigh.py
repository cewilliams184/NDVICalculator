import datetime
import numpy
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from Convert2GeopandasObject import Convert2GeopandasObject
from EarthAccessData import AccessEarthAccessData

AccessEarthAccessData = AccessEarthAccessData()
read_coordinates_from_polygon = AccessEarthAccessData.read_coordinates_from_polygon


def create_scene_filter(): #TODO: feed coordinates from user drawn polygon here
    polygon = [[35.95397342058534, -76.64996823193624], [35.95397342058534, -75.97293004875567], [35.52305406304399, -75.97293004875567], [35.52305406304399, -76.64996823193624], [35.95397342058534, -76.64996823193624]]
    spatialFilter = {'filterType': "mbr",
                     'lowerLeft': {'latitude': polygon[1][0], 'longitude': polygon[1][1]},
                     'upperRight': {'latitude': polygon[3][0], 'longitude': polygon[3][1]}}
    sceneFilter = {'cloudCoverFilter': {'min': 0, 'max': 20},
                   'spatialFilter': spatialFilter,
                   'temporalFilter': create_temporal_filter()}

    return sceneFilter, polygon


def create_temporal_filter():
    # TODO: set start to beginning on one month previous current_month = datetime.now().month
    temporal_filter = {'start': (datetime.datetime.now() - datetime.timedelta(days=30)).strftime("%Y-%m-%d") , 'end': datetime.datetime.now().strftime("%Y-%m-%d")}
    return temporal_filter


def filter_on_centroid(result_extents, coordinates):
    """ find output that intersects center of polygon"""
    # https://stackoverflow.com/questions/4355894/how-to-get-center-of-set-of-points-using-python
    # find centroid
    search_polygon = create_scene_filter(coordinates)[1]
    # TODO: Fix naming x is currently y (latitude) and y is currently x (longtude)
    x,y=zip(*search_polygon)
    center=(max(y)+min(y))/2., (max(x)+min(x))/2.

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
