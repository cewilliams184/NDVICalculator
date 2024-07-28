# Name: NDVI_Calculations
# Author : Chantel Williams
# Start Date : 7/27/2024
# Purpose: create flexible class that calculates NDVI from landsat raster files
# Tutorials Used:


import numpy
import os
import rasterio
from rasterio.plot import show

import constants as cn


# convert .tif to a numpy array

class NDVI_Calculations():
    def __init__(self,
                 near_infrared_band=cn.near_infrared_band,
                 project_path=cn.project_path,
                 red_band=cn.red_band,
                 ):
        self.near_infrared_band = near_infrared_band
        self.project_path = project_path
        self.red_band = red_band

    def initialize_NDVI_Calculations(self):
        self.calcualte_NDVI()
        return

    def execute_NDVI_Calculations(self):
        self.initialize_NDVI_Calculations()
        return

    def calcualte_NDVI(self):
        """ calculate NDVI raster from infrared and red bands"""
        near_infrared_band_rasterio_open = rasterio.open(self.near_infrared_band)
        red_band_rasterio_open = rasterio.open(self.red_band)

        near_infrared_band_rasterio_read = near_infrared_band_rasterio_open.read()  # open and read as numpy array
        red_band_rasterio_read = red_band_rasterio_open.read()

        show(near_infrared_band_rasterio_read)
        show(red_band_rasterio_read)

        near_infrared_band_rasterio_float = near_infrared_band_rasterio_read.astype(float)
        red_band_rasterio_float = red_band_rasterio_read.astype(float)

        numpy.seterr(divide='ignore', invalid='ignore')  # allow 0 division in numpy
        ndvi = numpy.empty(near_infrared_band_rasterio_open.shape, dtype=rasterio.float32)

        check = numpy.logical_or(near_infrared_band_rasterio_float > 0,
                                 red_band_rasterio_float > 0)  # apply filter on values > 0 to be used to calculate NDVI

        ndvi = numpy.where(check, (near_infrared_band_rasterio_float - red_band_rasterio_float) / (
                    near_infrared_band_rasterio_float + red_band_rasterio_float), -999)
        show(ndvi, cmap='summer')
        print(f"NDVI mean: {ndvi.mean()}")
        print(f"NDVI standard deviation: {ndvi.std()}")
        return


def main():
    NDVIC = NDVI_Calculations()
    NDVIC.execute_NDVI_Calculations()


if __name__ == "__main__":
    main()
