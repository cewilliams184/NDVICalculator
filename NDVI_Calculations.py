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
                 # near_infrared_band=cn.near_infrared_band,
                 # near_infrared_band=None,
                 project_path=cn.project_path,
                 # red_band=cn.red_band,
                 ):
        # self.near_infrared_band = near_infrared_band
        self.near_infrared_band = None
        self.project_path = project_path
        self.red_band = None

    def initialize_NDVI_Calculations(self):
        self.near_infrared_band = self.locate_latest_near_infrared_band_downloaded()[0]
        self.red_band = self.locate_latest_near_infrared_band_downloaded()[1]
        self.calcualte_NDVI()
        return

    def execute_NDVI_Calculations(self):
        self.initialize_NDVI_Calculations()
        return

    def locate_latest_near_infrared_band_downloaded(self):
        """ parse data folder for latest near infrared downloaded"""
        global latest_near_infrared, latest_red_band
        data_folder = os.path.join(self.project_path, 'Data')
        # latest_downloaded_folder = (
        downloaded_files = []
        with os.scandir(data_folder) as it:
            for entry in it:
                downloaded_files.append(entry.path)
        downloaded_files.sort(key=os.path.getctime, reverse=True)

        latest_downloaded_file_directory = downloaded_files[0]

        #enter directory and pull out file ending in 'B5.tif'
        latest_downloaded_files = os.listdir(latest_downloaded_file_directory)
        for file in latest_downloaded_files:
            if file[-6:] == 'B4.TIF':
                latest_red_band = os.path.join(latest_downloaded_file_directory,file)
            if file[-6:] == 'B5.TIF':
                latest_near_infrared = os.path.join(latest_downloaded_file_directory,file)

        return latest_near_infrared, latest_red_band

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
        #save ndvi files to display on web app
        print(f"NDVI mean: {ndvi.mean()}")
        print(f"NDVI standard deviation: {ndvi.std()}")
        return


def main():
    NDVIC = NDVI_Calculations()
    NDVIC.execute_NDVI_Calculations()


if __name__ == "__main__":
    main()
