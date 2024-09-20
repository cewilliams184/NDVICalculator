#use earthaccess python library to access data from NASA
#Chantel Williams
#July 2024

import earthaccess
from pyproj import Transformer

from Convert2GeopandasObject import Convert2GeopandasObject

earthaccess.login(strategy="netrc")


# earthaccess.login(strategy="environment")# use for azure


class AccessEarthAccessData(object):
    def __init__(self):
        data = None

    def initialize_access_earth_access_data(self):
        # self.read_coordinates_from_polygon()
        self.retrieve_landsat8_data()

    def execute_access_earth_access_data(self):
        self.initialize_access_earth_access_data()

    def retrieve_landsat8_data(self):
        results = earthaccess.search_data(
            short_name="ATL06",
            cloud_hosted=False,
            temporal=("2019-01", "2019-02"),
            polygon=[(-100, 40), (-110, 40), (-105, 38), (-100, 40)]
        )
        # print(results)

        user_defined_polygon = earthaccess.search_datasets(
            # short_name="Sentinel-5P",  # Sentinel-6A C2L2
            keyword="sentinel 5p near infrared",
            cloud_hosted=False,
            temporal=("2024-07-11", "2024-07-11"),
            polygon=self.read_coordinates_from_polygon(Convert2GeopandasObject(r"C:\Users\cewil\Documents\GitHub\NDVICalculator\InputData\Shapefiles\Pocosin_FWS\Pocosin_FWS\Pocosin_FWS_AOI_WGS84.shp")).reverse()
        )
        print(user_defined_polygon)
        return user_defined_polygon

    def read_coordinates_from_polygon(self, polygon):
        # polygon = Convert2GeopandasObject(

        # transformer = Transformer.from_crs(f"EPSG:{polygon.converted_file.crs.to_epsg()}", "EPSG:4326")
        transformer = Transformer.from_crs(polygon.converted_file.crs.to_epsg(), 4326)

        polygon_coordinates_linestring = polygon.converted_file.boundary[0].coords.xy
        polygon_coordinates_pairs = []
        coordinate_pair = zip(polygon_coordinates_linestring[1], polygon_coordinates_linestring[0])

        for x in tuple(coordinate_pair):
            polygon_coordinates_pairs.append(x)

        transformed_polygon = []
        for point in transformer.itransform(polygon_coordinates_pairs):
            transformed_polygon.append((point))

        transformed_polygon.reverse()

        return transformed_polygon


def main():
    AEAD = AccessEarthAccessData()
    AEAD.execute_access_earth_access_data()


if __name__ == "__main__":
    main()
