# Purpose : convert any geometry object regardless of file format to a geopandas object
# Author : Chantel Williams
# Date : July 2024

import geopandas
import pandas

def read_file_to_pandas_dataframe(file):
    #check file extension
    if file.endswith('.txt'):
        pandas_dataframe = pandas.read_csv(file, sep="\t")
    if file.endswith('.shp'):
        pandas_dataframe = geopandas.read_file(file, crs="EPSG:32119")
    return pandas_dataframe


def read_spatial_data(input_file):
    #check file extension
    pandas_dataframe = read_file_to_pandas_dataframe(input_file)
    if hasattr(pandas_dataframe, 'geometry'):
        if pandas_dataframe.geometry.type[0] == 'MultiPolygon':
            spatial_data = pandas_dataframe.geometry
        elif pandas_dataframe.geometry.type[0] == 'Point':
            spatial_data = pandas_dataframe.geometry
        elif pandas_dataframe.geometry.type[0] == 'Polygon':
            spatial_data = pandas_dataframe.geometry
        else:
            spatial_data = pandas_dataframe.geometry
    else:
        spatial_data = geopandas.GeoDataFrame(pandas_dataframe, geometry=geopandas.points_from_xy(pandas_dataframe.lon, pandas_dataframe.lat), crs="EPSG:32119")
    # spatial_data.iloc[[0]] #select first object
    return spatial_data


class Convert2GeopandasObject(object):
    def __init__(self,
                 file):
        self.file = file
        self.converted_file = self.initialize_convert2geopandas_object()

    def initialize_convert2geopandas_object(self):
        input_file = read_spatial_data(self.file)
        return input_file

    def execute_convert2Geopandas_object(self):
        converted_file = self.initialize_convert2geopandas_object()
        return converted_file


def main():
    C2G = Convert2GeopandasObject(object)
    C2G.execute_convert2Geopandas_object()


if __name__ == "__main__":
    main()
